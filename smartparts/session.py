from dataclasses import dataclass


@dataclass(frozen=True)
class AppSession:
    access_token: str
    operator_name: str
    system_role: str
