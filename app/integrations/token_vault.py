import json
from typing import Any

from cryptography.fernet import Fernet

from app.config import get_settings


def generate_encryption_key() -> str:
    return Fernet.generate_key().decode("ascii")


def _fernet() -> Fernet | None:
    settings = get_settings()
    key = settings.token_encryption_key.strip()
    if not key:
        if settings.is_production:
            raise RuntimeError("TOKEN_ENCRYPTION_KEY must be set in production.")
        return None
    return Fernet(key.encode("ascii"))


def encrypt_token_payload(payload: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    fernet = _fernet()
    if not fernet:
        return None, {"storage": "plain_dev", "warning": "Set TOKEN_ENCRYPTION_KEY before production."}
    encrypted = fernet.encrypt(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")).decode("ascii")
    return encrypted, {"storage": "fernet", "encrypted": True}


def decrypt_token_payload(encrypted: str | None, fallback: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if not encrypted:
        return fallback
    fernet = _fernet()
    if not fernet:
        return fallback
    return json.loads(fernet.decrypt(encrypted.encode("ascii")).decode("utf-8"))
