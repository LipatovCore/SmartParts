from dataclasses import dataclass


@dataclass(frozen=True)
class Brand:
    id: str
    name: str
    code: str = ""
    external_code: str = ""


@dataclass(frozen=True)
class Counterparty:
    id: str
    name: str
    phone: str = ""
    group: str = ""
    comment: str = ""


@dataclass(frozen=True)
class AppSession:
    access_token: str
    operator_name: str
    system_role: str
    brands: tuple[Brand, ...] = ()
    counterparties: tuple[Counterparty, ...] = ()
