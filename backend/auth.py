import hashlib
import hmac
import logging
import os
import time

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import config

log = logging.getLogger("carlog.auth")

bearer = HTTPBearer(auto_error=True)


def hash_password(password: str):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 20000)
    return salt.hex() + ":" + digest.hex()


def verify_password(password: str, password_hash: str):
    salt, digest = password_hash.split(":")
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 20000)
    return hmac.compare_digest(check.hex(), digest)


def create_token(user_id: int):
    payload = {"sub": str(user_id), "exp": int(time.time()) + config.TOKEN_TTL_MIN * 60}
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def current_user_id(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        payload = jwt.decode(creds.credentials, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        log.info("Отклонён токен: %s: %s", type(e).__name__, e)
        raise HTTPException(401, "Неверный или просроченный токен")
    return int(payload["sub"])
