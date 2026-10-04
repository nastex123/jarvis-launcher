"""Tests gateway sin red: JWT HS256 stdlib y pairing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["JARVIS_GATEWAY_SECRET"] = "test-secreto-32-caracteres-minimo-xxxx"

from apps.gateway.auth import issue_jwt, new_pairing_token, verify_jwt


def test_jwt_roundtrip():
    token = issue_jwt("mobile-test")
    payload = verify_jwt(token)
    assert payload["sub"] == "mobile-test"


def test_pairing_token_shape():
    token, exp = new_pairing_token()
    assert len(token) >= 32
    assert exp == 300
