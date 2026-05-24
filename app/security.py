import base64
import hmac
import json
import secrets
import time
from hashlib import sha256
from typing import Any

from fastapi import Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


def _secret() -> str:
    settings = get_settings()
    secret = settings.security_secret_key or "local-dev-secret-change-me"
    if settings.is_production and secret == "local-dev-secret-change-me":
        raise RuntimeError("SECURITY_SECRET_KEY must be set in production.")
    return secret


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def sign_payload(payload: dict[str, Any]) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(_secret().encode("utf-8"), body.encode("ascii"), sha256).digest()
    return f"{body}.{_b64(signature)}"


def verify_signed_payload(token: str) -> dict[str, Any]:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid session token.") from exc
    expected = _b64(hmac.new(_secret().encode("utf-8"), body.encode("ascii"), sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid session token.")
    payload = json.loads(_unb64(body).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Session expired.")
    return payload


def create_admin_token(user_id: int, telegram_id: int, ttl_seconds: int = 60 * 60 * 12) -> str:
    return sign_payload(
        {
            "sub": str(user_id),
            "telegram_id": telegram_id,
            "role": "admin",
            "iat": int(time.time()),
            "exp": int(time.time()) + ttl_seconds,
            "nonce": secrets.token_urlsafe(12),
        }
    )


def require_admin_session(
    authorization: str | None = Header(default=None),
    x_admin_telegram_id: str | None = Header(default=None),
) -> dict[str, Any]:
    settings = get_settings()
    if authorization and authorization.lower().startswith("bearer "):
        payload = verify_signed_payload(authorization.split(" ", 1)[1].strip())
        if payload.get("role") == "admin" and int(payload.get("telegram_id", 0)) in settings.admin_ids:
            return payload
    if not settings.is_production and x_admin_telegram_id and x_admin_telegram_id.isdigit():
        if int(x_admin_telegram_id) in settings.admin_ids:
            return {"role": "admin", "telegram_id": int(x_admin_telegram_id), "dev_header": True}
    raise HTTPException(status_code=403, detail="Admin access required.")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if get_settings().is_production:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
