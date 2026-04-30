import base64
import gzip
import json
import socket
import urllib.error
import urllib.request
from urllib.parse import quote

from smartparts.session import AppSession


API_BASE_URL = "https://api.moysklad.ru/api/remap/1.2"
TOKEN_URL = f"{API_BASE_URL}/security/token"
EMPLOYEE_CONTEXT_URL = f"{API_BASE_URL}/context/employee"
EMPLOYEE_URL = f"{API_BASE_URL}/entity/employee"
REQUEST_TIMEOUT_SECONDS = 15


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
