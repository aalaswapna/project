from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Dict

from fastapi import HTTPException, status


@dataclass(frozen=True)
class AuthConfig:
    username: str
    password: str
    secret: str
    token_ttl_seconds: int
    auth_required: bool
    password_hash_iterations: int


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * ((4 - (len(value) % 4)) % 4)
    return base64.urlsafe_b64decode(value + padding)


def load_auth_config() -> AuthConfig:
    raw_ttl = os.environ.get("APP_AUTH_TOKEN_TTL_MINUTES", "480").strip()
    try:
        ttl_minutes = max(5, int(raw_ttl))
    except Exception:
        ttl_minutes = 480

    raw_hash_iterations = os.environ.get("APP_AUTH_HASH_ITERATIONS", "120000").strip()
    try:
        hash_iterations = max(50000, int(raw_hash_iterations))
    except Exception:
        hash_iterations = 120000

    username = os.environ.get("APP_LOGIN_USERNAME", "admin").strip() or "admin"
    password = os.environ.get("APP_LOGIN_PASSWORD", "admin123")
    secret = os.environ.get("APP_AUTH_SECRET", "replace-this-secret")
    auth_required = os.environ.get("API_REQUIRE_AUTH", "1").strip() != "0"

    return AuthConfig(
        username=username,
        password=password,
        secret=secret,
        token_ttl_seconds=ttl_minutes * 60,
        auth_required=auth_required,
        password_hash_iterations=hash_iterations,
    )


def _signature(payload_segment: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_segment.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def issue_token(username: str, cfg: AuthConfig) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + cfg.token_ttl_seconds,
    }
    payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    return f"{payload_segment}.{_signature(payload_segment, cfg.secret)}"


def validate_token(token: str, cfg: AuthConfig) -> Dict[str, object]:
    parts = token.split(".")
    if len(parts) != 2:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    payload_segment, signature = parts
    expected = _signature(payload_segment, cfg.secret)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        payload = json.loads(_b64url_decode(payload_segment).decode("utf-8"))
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Corrupted token payload: {ex}")

    username = str(payload.get("sub", "")).strip()
    expires_at = int(payload.get("exp", 0))
    now = int(time.time())

    if not username or expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    return payload


def extract_bearer_token(header_value: str | None) -> str:
    if not header_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")

    parts = header_value.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    return parts[1].strip()


def hash_password(password: str, iterations: int) -> tuple[str, str]:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    return _b64url_encode(salt), _b64url_encode(derived)


def verify_password(password: str, salt_b64: str, hash_b64: str, iterations: int) -> bool:
    try:
        salt = _b64url_decode(salt_b64)
        expected = _b64url_decode(hash_b64)
    except Exception:
        return False

    if not salt or not expected:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected))
    return hmac.compare_digest(candidate, expected)
