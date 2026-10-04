"""Auth LAN: pairing QR (token corto) + JWT HS256 con stdlib.

Sin dependencias externas para que el gateway verifique sin PyJWT.
El telefono escanea el JSON del endpoint /api/pairing y guarda el JWT.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

JWT_EXP_S = 15 * 60
PAIRING_EXP_S = 5 * 60


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64url(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def get_secret() -> str:
    secret = os.environ.get("JARVIS_GATEWAY_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JARVIS_GATEWAY_SECRET debe tener 32+ caracteres (ver .env.example)")
    return secret


def issue_jwt(subject: str = "mobile", exp_s: int = JWT_EXP_S) -> str:
    # Cabecera + payload HS256 manual (sin PyJWT para MVP verificable).
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({"sub": subject, "exp": int(time.time()) + exp_s}).encode())
    sig = _b64url(hmac.new(get_secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def verify_jwt(token: str) -> dict:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("formato JWT invalido")
    expected = _b64url(hmac.new(get_secret().encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig_b64):
        raise ValueError("firma JWT invalida")
    payload = json.loads(_unb64url(payload_b64).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("JWT expirado")
    return payload


def new_pairing_token() -> tuple[str, int]:
    # Token opaco de un solo uso que el movil canjea por JWT en LAN.
    return secrets.token_urlsafe(24), PAIRING_EXP_S
