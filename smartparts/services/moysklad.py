import base64
import gzip
import json
import socket
import urllib.error
import urllib.request
from urllib.parse import quote, urlencode

from smartparts.session import AppSession, Brand


API_BASE_URL = "https://api.moysklad.ru/api/remap/1.2"
TOKEN_URL = f"{API_BASE_URL}/security/token"
EMPLOYEE_CONTEXT_URL = f"{API_BASE_URL}/context/employee"
EMPLOYEE_URL = f"{API_BASE_URL}/entity/employee"
CUSTOM_ENTITY_URL = f"{API_BASE_URL}/entity/customentity"
PRODUCT_URL = f"{API_BASE_URL}/entity/product"
BRANDS_DICTIONARY_NAME = "Бренды"
BRAND_ATTRIBUTE_NAMES = ("Бренд", "Бренды")
REQUEST_TIMEOUT_SECONDS = 15
PAGE_LIMIT = 1000


class MoySkladAuthError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidCredentialsError(MoySkladAuthError):
    pass


class MoySkladNetworkError(MoySkladAuthError):
    pass


def authenticate(login: str, password: str) -> AppSession:
    token = _request_token(login, password)
    operator_name, employee_id = _request_operator_profile(token)
    system_role = _request_operator_role(token, employee_id)
    return AppSession(access_token=token, operator_name=operator_name or login, system_role=system_role)


def load_brands(access_token: str) -> tuple[Brand, ...]:
    return _request_brands(access_token)


def _request_token(login: str, password: str) -> str:
    credentials = f"{login}:{password}".encode("utf-8")
    encoded_credentials = base64.b64encode(credentials).decode("ascii")
    base_headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Accept": "application/json;charset=utf-8",
        "Accept-Encoding": "gzip",
    }
    request = urllib.request.Request(
        TOKEN_URL,
        headers=base_headers,
        method="POST",
    )

    payload = _open_json(request)
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise MoySkladAuthError("МойСклад не вернул токен авторизации.")
    return token


def _request_operator_profile(token: str) -> tuple[str, str]:
    request = urllib.request.Request(
        EMPLOYEE_CONTEXT_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json;charset=utf-8",
            "Accept-Encoding": "gzip",
        },
        method="GET",
    )

    payload = _open_json(request)
    return _extract_operator_name(payload), _extract_string(payload, "id")


def _request_operator_role(token: str, employee_id: str) -> str:
    if not employee_id:
        return ""

    request = urllib.request.Request(
        f"{EMPLOYEE_URL}/{quote(employee_id)}/security",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json;charset=utf-8",
            "Accept-Encoding": "gzip",
        },
        method="GET",
    )

    try:
        payload = _open_json(request)
    except MoySkladAuthError:
        return ""
    return _extract_role_name(payload)


def _request_brands(token: str) -> tuple[Brand, ...]:
    dictionary_ids = _request_brand_dictionary_ids(token)
    if not dictionary_ids:
        raise MoySkladAuthError(f"Не удалось найти справочник {BRANDS_DICTIONARY_NAME} в МойСклад.")

    failed_ids: list[str] = []
    last_error: MoySkladAuthError | None = None
    for dictionary_id in dictionary_ids:
        try:
            return _request_custom_entity_brands(token, dictionary_id)
        except MoySkladAuthError as error:
            last_error = error
            failed_ids.append(dictionary_id)

    if last_error is not None:
        print(f"Failed MoySklad brand dictionary candidates: {', '.join(failed_ids)}", flush=True)
        raise last_error
    raise MoySkladAuthError(f"Не удалось загрузить справочник {BRANDS_DICTIONARY_NAME} из МойСклад.")


def _request_custom_entity_brands(token: str, dictionary_id: str) -> tuple[Brand, ...]:
    brands: list[Brand] = []
    offset = 0
    while True:
        query = urlencode({"limit": PAGE_LIMIT, "offset": offset})
        payload = _open_json(_bearer_request(f"{CUSTOM_ENTITY_URL}/{quote(dictionary_id)}?{query}", token))
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise MoySkladAuthError(f"МойСклад вернул некорректный список справочника {BRANDS_DICTIONARY_NAME}.")

        brands.extend(_extract_brand(row) for row in rows if isinstance(row, dict))

        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        size = meta.get("size")
        limit = meta.get("limit", PAGE_LIMIT)
        offset = meta.get("offset", offset) + limit
        if not isinstance(size, int) or not isinstance(limit, int) or offset >= size:
            break

    return tuple(brands)


def _request_brand_dictionary_ids(token: str) -> tuple[str, ...]:
    dictionary_ids: list[str] = []
    dictionary_ids.extend(_find_custom_entity_ids_in_entity_rows(token, PRODUCT_URL, BRAND_ATTRIBUTE_NAMES))
    return tuple(dict.fromkeys(dictionary_ids))


def _find_custom_entity_ids_in_entity_rows(token: str, entity_url: str, attribute_names: tuple[str, ...]) -> tuple[str, ...]:
    query = urlencode({"limit": 100, "offset": 0, "expand": "attributes.value"})
    try:
        payload = _open_json(_bearer_request(f"{entity_url}?{query}", token))
    except MoySkladAuthError as error:
        print(f"Failed to inspect MoySklad entity rows {entity_url}: {error.message}", flush=True)
        return ()

    rows = payload.get("rows")
    if not isinstance(rows, list):
        print(f"MoySklad entity rows response has no rows: {entity_url}", flush=True)
        return ()

    expected_names = {name.casefold() for name in attribute_names}
    dictionary_ids: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        attributes = row.get("attributes")
        if not isinstance(attributes, list):
            continue

        for attribute in attributes:
            if not isinstance(attribute, dict):
                continue

            name = _extract_string(attribute, "name")
            if name.casefold() not in expected_names:
                continue

            dictionary_ids.extend(_extract_custom_entity_dictionary_ids(attribute))

    return tuple(dict.fromkeys(dictionary_ids))


def _extract_ids_from_meta(meta: dict) -> tuple[str, ...]:
    ids: list[str] = []
    href = _extract_string(meta, "href")
    if href:
        parts = href.rstrip("/").split("/")
        if "customentity" in parts:
            index = parts.index("customentity")
            if len(parts) > index + 1:
                ids.append(parts[index + 1])
        if parts:
            ids.append(parts[-1])

    metadata_href = _extract_string(meta, "metadataHref")
    if metadata_href:
        ids.append(metadata_href.rstrip("/").rsplit("/", 1)[-1])

    uuid_href = _extract_string(meta, "uuidHref")
    if uuid_href:
        marker = "custom_"
        if marker in uuid_href:
            ids.append(uuid_href.split(marker, 1)[1].split("/", 1)[0].split("?", 1)[0])

    meta_id = _extract_string(meta, "id")
    if meta_id:
        ids.append(meta_id)

    return tuple(dict.fromkeys(ids))


def _extract_custom_entity_dictionary_ids(attribute: dict) -> tuple[str, ...]:
    dictionary_ids: list[str] = []
    for key in ("customEntityMeta", "customentitymeta", "entityMeta", "meta"):
        custom_entity_meta = attribute.get(key)
        if isinstance(custom_entity_meta, dict):
            dictionary_ids.extend(_extract_ids_from_meta(custom_entity_meta))

    value = attribute.get("value")
    if isinstance(value, dict):
        value_meta = value.get("meta")
        if isinstance(value_meta, dict):
            dictionary_ids.extend(_extract_ids_from_meta(value_meta))

    return tuple(dict.fromkeys(dictionary_ids))


def _extract_brand(payload: dict) -> Brand:
    return Brand(
        id=_extract_string(payload, "id"),
        name=_extract_string(payload, "name"),
        code=_extract_string(payload, "code"),
        external_code=_extract_string(payload, "externalCode"),
    )


def _bearer_request(url: str, token: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json;charset=utf-8",
            "Accept-Encoding": "gzip",
        },
        method="GET",
    )


def _extract_operator_name(payload: dict) -> str:
    name = payload.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()

    parts = [payload.get("lastName"), payload.get("firstName"), payload.get("middleName")]
    return " ".join(part.strip() for part in parts if isinstance(part, str) and part.strip())


def _extract_role_name(payload: dict) -> str:
    role = payload.get("role") if isinstance(payload.get("role"), dict) else payload
    name = _extract_named_value(role)
    if name:
        return name

    meta = role.get("meta")
    if isinstance(meta, dict):
        href = _extract_string(meta, "href")
        if href:
            return href.rstrip("/").rsplit("/", 1)[-1]
    return ""


def _extract_string(payload: dict, key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _extract_named_value(payload: dict) -> str:
    for key in ("name", "code", "type", "title", "description"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _open_json(request: urllib.request.Request) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_payload = response.read()
            raw_payload = _decompress_payload(response.headers, raw_payload)
    except urllib.error.HTTPError as error:
        raw_payload = error.read()
        raw_payload = _decompress_payload(error.headers, raw_payload)
        if error.code in (401, 403):
            raise InvalidCredentialsError("Неверный логин или пароль.") from error
        error_message = _read_error_message(raw_payload)
        if error_message:
            raise MoySkladAuthError(f"МойСклад вернул ошибку {error.code}: {error_message}") from error
        raise MoySkladAuthError(f"МойСклад вернул ошибку {error.code}.") from error
    except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
        raise MoySkladNetworkError("Не удалось подключиться к МойСклад. Проверьте интернет и попробуйте снова.") from error

    try:
        payload = json.loads(raw_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MoySkladAuthError("МойСклад вернул некорректный ответ.") from error

    if not isinstance(payload, dict):
        raise MoySkladAuthError("МойСклад вернул некорректный ответ.")
    return payload


def _read_error_message(raw_payload: bytes) -> str:
    try:
        payload = json.loads(raw_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ""

    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first_error = errors[0]
        if isinstance(first_error, dict):
            message = first_error.get("error_message") or first_error.get("errorMessage") or first_error.get("error")
            if isinstance(message, str):
                return message

    message = payload.get("message")
    return message if isinstance(message, str) else ""


def _decompress_payload(headers, body: bytes) -> bytes:
    encoding = ""
    if hasattr(headers, "get"):
        encoding = headers.get("Content-Encoding", "") or headers.get("content-encoding", "")
    if encoding.lower() != "gzip" or not body:
        return body

    try:
        return gzip.decompress(body)
    except OSError:
        return body
