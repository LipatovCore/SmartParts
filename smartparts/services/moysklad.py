import base64
import gzip
import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import quote, urlencode
from typing import Any

from smartparts.session import AppSession, Brand, Counterparty, Warehouse


API_BASE_URL = "https://api.moysklad.ru/api/remap/1.2"
TOKEN_URL = f"{API_BASE_URL}/security/token"
EMPLOYEE_CONTEXT_URL = f"{API_BASE_URL}/context/employee"
EMPLOYEE_URL = f"{API_BASE_URL}/entity/employee"
CUSTOM_ENTITY_URL = f"{API_BASE_URL}/entity/customentity"
PRODUCT_URL = f"{API_BASE_URL}/entity/product"
COUNTERPARTY_URL = f"{API_BASE_URL}/entity/counterparty"
WAREHOUSE_URL = f"{API_BASE_URL}/entity/store"
STOCK_CURRENT_URL = f"{API_BASE_URL}/report/stock/all/current"
STOCK_BY_SLOT_CURRENT_URL = f"{API_BASE_URL}/report/stock/byslot/current"
STOCK_ALL_URL = f"{API_BASE_URL}/report/stock/all"
BRANDS_DICTIONARY_NAME = "Бренды"
BRAND_ATTRIBUTE_NAMES = ("Бренд", "Бренды")
REQUEST_TIMEOUT_SECONDS = 15
PAGE_LIMIT = 1000


@dataclass(frozen=True)
class ArticleLookupItem:
    brand: str
    number: str
    normalized_number: str = ""


@dataclass(frozen=True)
class ProductStockMatch:
    id: str
    name: str
    article: str
    brand: str
    quantity: float
    cell: str = ""
    brand_matches_query: bool = False


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


def load_counterparties(access_token: str) -> tuple[Counterparty, ...]:
    return _request_counterparties(access_token)


def load_warehouses(access_token: str) -> tuple[Warehouse, ...]:
    return _request_warehouses(access_token)


def find_article_stock(access_token: str, warehouse_id: str, items: list[ArticleLookupItem]) -> tuple[ProductStockMatch, ...]:
    print(f"[MoySklad] find_article_stock: warehouse_id={warehouse_id}, items={len(items)}", flush=True)
    return _request_article_stock(access_token, warehouse_id, items)


def normalize_article(value: str) -> str:
    return "".join(character for character in value.upper() if character.isalnum())


def normalize_brand(value: str) -> str:
    return "".join(character for character in value.casefold().upper() if character.isalnum())


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


def _request_counterparties(token: str) -> tuple[Counterparty, ...]:
    counterparties: list[Counterparty] = []
    offset = 0
    while True:
        query = urlencode({"limit": PAGE_LIMIT, "offset": offset, "expand": "group"})
        payload = _open_json(_bearer_request(f"{COUNTERPARTY_URL}?{query}", token))
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise MoySkladAuthError("MoySklad returned an invalid counterparties list.")

        counterparties.extend(_extract_counterparty(row) for row in rows if isinstance(row, dict))

        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        size = meta.get("size")
        limit = meta.get("limit", PAGE_LIMIT)
        offset = meta.get("offset", offset) + limit
        if not isinstance(size, int) or not isinstance(limit, int) or offset >= size:
            break

    return tuple(counterparties)


def _request_warehouses(token: str) -> tuple[Warehouse, ...]:
    warehouses: list[Warehouse] = []
    offset = 0
    while True:
        query = urlencode({"limit": PAGE_LIMIT, "offset": offset})
        payload = _open_json(_bearer_request(f"{WAREHOUSE_URL}?{query}", token))
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise MoySkladAuthError("MoySklad returned an invalid warehouses list.")

        warehouses.extend(_extract_warehouse(row) for row in rows if isinstance(row, dict))

        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        size = meta.get("size")
        limit = meta.get("limit", PAGE_LIMIT)
        offset = meta.get("offset", offset) + limit
        if not isinstance(size, int) or not isinstance(limit, int) or offset >= size:
            break

    return tuple(warehouses)


def _request_article_stock(token: str, warehouse_id: str, items: list[ArticleLookupItem]) -> tuple[ProductStockMatch, ...]:
    article_to_brands: dict[str, set[str]] = {}
    search_terms: set[str] = set()
    for item in items:
        brand_key = normalize_brand(item.brand)
        for term in (item.number, item.normalized_number, normalize_article(item.number), normalize_article(item.normalized_number)):
            term = term.strip()
            article_key = normalize_article(term)
            if not article_key:
                continue
            search_terms.add(term)
            search_terms.add(article_key)
            article_to_brands.setdefault(article_key, set()).add(brand_key)

    print(
        f"[MoySklad] Prepared lookup: article_keys={len(article_to_brands)}, search_terms={len(search_terms)}",
        flush=True,
    )
    if article_to_brands:
        preview = ", ".join(list(article_to_brands)[:12])
        print(f"[MoySklad] Article key preview: {preview}", flush=True)

    if not article_to_brands or not warehouse_id:
        print("[MoySklad] Lookup stopped: no article keys or warehouse id", flush=True)
        return ()

    products = _request_products_by_article_terms(token, search_terms, set(article_to_brands))
    print(f"[MoySklad] Products matched by article: {len(products)}", flush=True)
    if not products:
        return ()

    stock_by_product_id = _request_stock_by_warehouse(token, warehouse_id)
    print(f"[MoySklad] Stock rows indexed: {len(stock_by_product_id)}", flush=True)
    cell_by_product_id = _request_cells_by_product(token, warehouse_id, tuple(products))
    print(f"[MoySklad] Cell rows indexed: {len(cell_by_product_id)}", flush=True)
    results: list[ProductStockMatch] = []
    for product_id, product in products.items():
        article = _extract_string(product, "article")
        article_key = normalize_article(article)
        brand = _extract_product_brand(product)
        source_brands = article_to_brands.get(article_key, set())
        results.append(
            ProductStockMatch(
                id=product_id,
                name=_extract_string(product, "name"),
                article=article,
                brand=brand,
                quantity=stock_by_product_id.get(product_id, 0.0),
                cell=cell_by_product_id.get(product_id, ""),
                brand_matches_query=normalize_brand(brand) in source_brands,
            )
        )

    print(f"[MoySklad] Final stock matches: {len(results)}", flush=True)
    return tuple(sorted(results, key=lambda item: (item.brand.casefold(), item.article.casefold(), item.name.casefold())))


def _request_products_by_article_terms(token: str, search_terms: set[str], article_keys: set[str]) -> dict[str, dict]:
    products: dict[str, dict] = {}
    article_terms = sorted({term for term in search_terms if term}, key=lambda value: (len(value), value.casefold()))
    chunk_size = 30
    for chunk_start in range(0, len(article_terms), chunk_size):
        term_chunk = article_terms[chunk_start : chunk_start + chunk_size]
        filter_value = ";".join(f"article={term}" for term in term_chunk)
        offset = 0
        while True:
            query = urlencode({"limit": PAGE_LIMIT, "offset": offset, "filter": filter_value, "expand": "attributes.value"})
            print(
                f"[MoySklad] Product batch request: terms={len(term_chunk)}, offset={offset}, first={term_chunk[0]!r}",
                flush=True,
            )
            payload = _open_json(_bearer_request(f"{PRODUCT_URL}?{query}", token))
            rows = payload.get("rows")
            if not isinstance(rows, list):
                print("[MoySklad] Product batch returned invalid rows", flush=True)
                break

            matched_on_page = 0
            for row in rows:
                if not isinstance(row, dict):
                    continue
                article = _extract_string(row, "article")
                if normalize_article(article) not in article_keys:
                    continue
                product_id = _extract_entity_id(row)
                if product_id:
                    products[product_id] = row
                    matched_on_page += 1

            print(
                f"[MoySklad] Product batch response: terms={len(term_chunk)}, rows={len(rows)}, matched_on_page={matched_on_page}, total_matches={len(products)}",
                flush=True,
            )

            meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
            size = meta.get("size")
            limit = meta.get("limit", PAGE_LIMIT)
            offset = meta.get("offset", offset) + limit
            if not isinstance(size, int) or not isinstance(limit, int) or offset >= size:
                break

    return products


def _request_stock_by_warehouse(token: str, warehouse_id: str) -> dict[str, float]:
    query = urlencode({"stockType": "stock", "filter": f"storeId={warehouse_id}"})
    try:
        print(f"[MoySklad] Stock current request: warehouse_id={warehouse_id}", flush=True)
        payload = _open_payload(_bearer_request(f"{STOCK_CURRENT_URL}?{query}", token))
    except MoySkladAuthError as error:
        print(
            f"[MoySklad] Stock current failed, trying stock/all: warehouse_id={warehouse_id}, error={error.message}",
            flush=True,
        )
        payload = _open_json(
            _bearer_request(
                f"{STOCK_ALL_URL}?{urlencode({'filter': f'store={WAREHOUSE_URL}/{quote(warehouse_id)};stockType=stock', 'limit': PAGE_LIMIT})}"
            )
        )

    if isinstance(payload, list):
        stock_rows = _extract_current_stock_rows(payload)
        print(f"[MoySklad] Stock current response: rows={len(payload)}, indexed={len(stock_rows)}", flush=True)
        return stock_rows
    if isinstance(payload, dict):
        rows = payload.get("rows")
        if isinstance(rows, list):
            stock_rows = _extract_stock_report_rows(rows)
            print(f"[MoySklad] Stock report response: rows={len(rows)}, indexed={len(stock_rows)}", flush=True)
            return stock_rows
    print("[MoySklad] Stock response has no usable rows", flush=True)
    return {}


def _request_cells_by_product(token: str, warehouse_id: str, product_ids: tuple[str, ...]) -> dict[str, str]:
    if not warehouse_id or not product_ids:
        return {}

    slot_rows = _request_slot_stock_by_warehouse(token, warehouse_id, product_ids)
    if not slot_rows:
        return {}

    slot_names = _request_slot_names(token, warehouse_id)
    cells_by_product_id: dict[str, list[tuple[str, float]]] = {}
    for product_id, rows in slot_rows.items():
        cell_rows: list[tuple[str, float]] = []
        for slot_id, stock in rows:
            slot_name = slot_names.get(slot_id, slot_id)
            if slot_name:
                cell_rows.append((slot_name, stock))
        if cell_rows:
            cells_by_product_id[product_id] = cell_rows

    return {
        product_id: _format_cell_rows(cell_rows)
        for product_id, cell_rows in cells_by_product_id.items()
    }


def _request_slot_stock_by_warehouse(token: str, warehouse_id: str, product_ids: tuple[str, ...]) -> dict[str, list[tuple[str, float]]]:
    slot_rows_by_product_id: dict[str, list[tuple[str, float]]] = {}
    chunk_size = 80
    for chunk_start in range(0, len(product_ids), chunk_size):
        product_chunk = product_ids[chunk_start : chunk_start + chunk_size]
        filter_value = f"assortmentId={','.join(product_chunk)};storeId={warehouse_id}"
        query = urlencode({"filter": filter_value})
        try:
            print(
                f"[MoySklad] Slot stock request: products={len(product_chunk)}, warehouse_id={warehouse_id}",
                flush=True,
            )
            payload = _open_payload(_bearer_request(f"{STOCK_BY_SLOT_CURRENT_URL}?{query}", token))
        except MoySkladAuthError as error:
            print(f"[MoySklad] Slot stock skipped: {error.message}", flush=True)
            return slot_rows_by_product_id

        if not isinstance(payload, list):
            print("[MoySklad] Slot stock response has no usable rows", flush=True)
            continue

        for row in payload:
            if not isinstance(row, dict):
                continue
            product_id = _extract_string(row, "assortmentId")
            slot_id = _extract_string(row, "slotId")
            stock = _extract_float(row, ("stock", "quantity", "freeStock"))
            if not product_id or not slot_id or stock <= 0:
                continue
            slot_rows_by_product_id.setdefault(product_id, []).append((slot_id, stock))

    return slot_rows_by_product_id


def _request_slot_names(token: str, warehouse_id: str) -> dict[str, str]:
    slot_names: dict[str, str] = {}
    offset = 0
    while True:
        query = urlencode({"limit": PAGE_LIMIT, "offset": offset})
        try:
            payload = _open_json(_bearer_request(f"{WAREHOUSE_URL}/{quote(warehouse_id)}/slots?{query}", token))
        except MoySkladAuthError as error:
            print(f"[MoySklad] Slot names skipped: {error.message}", flush=True)
            return slot_names

        rows = payload.get("rows")
        if not isinstance(rows, list):
            print("[MoySklad] Slot names response has no usable rows", flush=True)
            return slot_names

        for row in rows:
            if not isinstance(row, dict):
                continue
            slot_id = _extract_entity_id(row)
            slot_name = _extract_string(row, "name") or _extract_string(row, "code")
            if slot_id and slot_name:
                slot_names[slot_id] = slot_name

        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        size = meta.get("size")
        limit = meta.get("limit", PAGE_LIMIT)
        offset = meta.get("offset", offset) + limit
        if not isinstance(size, int) or not isinstance(limit, int) or offset >= size:
            break

    return slot_names


def _format_cell_rows(cell_rows: list[tuple[str, float]]) -> str:
    formatted: list[str] = []
    for cell_name, stock in sorted(cell_rows, key=lambda item: item[0].casefold()):
        quantity = int(stock) if float(stock).is_integer() else f"{stock:g}"
        formatted.append(f"{cell_name} ({quantity})")
    return "; ".join(formatted)


def _extract_current_stock_rows(rows: list) -> dict[str, float]:
    stock_by_product_id: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        product_id = _extract_string(row, "assortmentId") or _extract_string(row, "productId")
        if not product_id:
            continue
        stock_by_product_id[product_id] = _extract_float(row, ("stock", "quantity", "freeStock"))
    return stock_by_product_id


def _extract_stock_report_rows(rows: list) -> dict[str, float]:
    stock_by_product_id: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        product_id = _extract_entity_id(row)
        meta = row.get("meta")
        if not product_id and isinstance(meta, dict):
            product_id = _extract_id_from_href(_extract_string(meta, "href"))
        if not product_id:
            continue
        stock_by_product_id[product_id] = _extract_float(row, ("stock", "quantity", "freeStock"))
    return stock_by_product_id


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


def _extract_counterparty(payload: dict) -> Counterparty:
    return Counterparty(
        id=_extract_string(payload, "id"),
        name=_extract_string(payload, "name"),
        phone=_extract_string(payload, "phone"),
        group=_extract_group_name(payload),
        comment=_extract_string(payload, "description"),
    )


def _extract_warehouse(payload: dict) -> Warehouse:
    return Warehouse(
        id=_extract_string(payload, "id"),
        name=_extract_string(payload, "name"),
        address=_extract_string(payload, "address"),
    )


def _extract_product_brand(payload: dict) -> str:
    attributes = payload.get("attributes")
    if not isinstance(attributes, list):
        return ""

    expected_names = {name.casefold() for name in BRAND_ATTRIBUTE_NAMES}
    for attribute in attributes:
        if not isinstance(attribute, dict):
            continue
        name = _extract_string(attribute, "name")
        if name.casefold() not in expected_names:
            continue
        value = attribute.get("value")
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            named_value = _extract_named_value(value)
            if named_value:
                return named_value
    return ""


def _extract_entity_id(payload: dict) -> str:
    entity_id = _extract_string(payload, "id")
    if entity_id:
        return entity_id

    meta = payload.get("meta")
    if isinstance(meta, dict):
        return _extract_id_from_href(_extract_string(meta, "href"))
    return ""


def _extract_id_from_href(href: str) -> str:
    return href.rstrip("/").rsplit("/", 1)[-1] if href else ""


def _extract_float(payload: dict, keys: tuple[str, ...]) -> float:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", "."))
            except ValueError:
                continue
    return 0.0


def _extract_group_name(payload: dict) -> str:
    names: list[str] = []

    group = payload.get("group")
    if isinstance(group, str) and group.strip():
        names.append(group.strip())
    elif isinstance(group, dict):
        name = _extract_named_value(group)
        if name:
            names.append(name)

    tags = payload.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                names.append(tag.strip())
            elif isinstance(tag, dict):
                tag_name = _extract_named_value(tag)
                if tag_name:
                    names.append(tag_name)

    return "; ".join(dict.fromkeys(names))


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


def _open_payload(request: urllib.request.Request) -> Any:
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

    return payload


def _open_json(request: urllib.request.Request) -> dict:
    payload = _open_payload(request)
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
