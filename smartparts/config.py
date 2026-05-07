from pathlib import Path


APP_VERSION_ENV_KEY = "APP_VERSION"
DEFAULT_APP_VERSION = "0.1.0"


def get_app_version() -> str:
    return _read_env_value(APP_VERSION_ENV_KEY) or DEFAULT_APP_VERSION


def _read_env_value(key: str) -> str:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return ""

    for line in env_path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
            continue

        name, value = clean_line.split("=", 1)
        if name.strip() == key:
            return value.strip().strip("\"'")

    return ""
