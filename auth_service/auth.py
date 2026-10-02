import hashlib
import hmac
import os
import time

import jwt

from auth_service.config import config


def hash_password(password: str):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 20000)
    return salt.hex() + ":" + digest.hex()


def verify_password(password: str, password_hash: str) -> bool:
    salt, digest = password_hash.split(":")
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 20000)
    return hmac.compare_digest(check.hex(), digest)


def create_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": int(time.time()) + config.TOKEN_TTL_MIN * 60,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")
