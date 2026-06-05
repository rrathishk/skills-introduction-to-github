"""
auth.py
=======
Self-contained email + password authentication with JWTs. No external auth
service required (so dev and CI run with zero setup), yet it gives the player a
real account whose progress follows them across web AND mobile.

- Passwords are hashed with PBKDF2-HMAC-SHA256 (Python stdlib — no native deps).
- Sessions are stateless JWTs signed with ``JWT_SECRET_KEY``.

Production note: set a strong ``JWT_SECRET_KEY`` (see CONFIGURATION.md). The
default below is intentionally insecure and only for local dev. If you prefer a
managed provider (e.g. Supabase Auth), you can instead verify that provider's
JWTs here — the rest of the app is unaffected because everything keys off the
returned ``user_id``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from typing import Optional

import jwt  # PyJWT

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "dev-insecure-secret-change-me")
JWT_ALGO = "HS256"
TOKEN_TTL_SECONDS = int(os.environ.get("JWT_TTL_SECONDS", str(60 * 60 * 24 * 30)))  # 30 days

_PBKDF2_ROUNDS = 200_000


def is_using_insecure_secret() -> bool:
    return JWT_SECRET == "dev-insecure-secret-change-me"


# ---------------------------------------------------------------------------
# Password hashing (PBKDF2, stdlib)
# ---------------------------------------------------------------------------

def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${_PBKDF2_ROUNDS}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds_s, salt_s, hash_s = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        rounds = int(rounds_s)
        salt = _unb64(salt_s)
        expected = _unb64(hash_s)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWTs
# ---------------------------------------------------------------------------

def new_user_id() -> str:
    return f"usr_{uuid.uuid4().hex[:16]}"


def create_token(user_id: str) -> str:
    now = int(time.time())
    payload = {"sub": user_id, "iat": now, "exp": now + TOKEN_TTL_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> Optional[str]:
    """Return the user_id (``sub``) if the token is valid, else None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload.get("sub")
    except Exception:
        return None
