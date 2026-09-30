import logging

from fastapi import APIRouter, HTTPException

from backend.auth import create_token, hash_password, verify_password
from backend.db import sql
from backend.models import Credentials

log = logging.getLogger("carlog.users")
router = APIRouter(prefix="/auth", tags=["auth"])


def token_response(user_id: int):
    return {"access_token": create_token(user_id), "token_type": "bearer"}


@router.post("/register", status_code=201)
def register(data: Credentials):
    username = data.username.strip()
    if sql("SELECT id FROM users WHERE username = %s", (username,)):
        raise HTTPException(409, "Пользователь c таким именем уже существует")
    user = sql(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
        (username, hash_password(data.password)),
    )
    log.info("Зарегистрирован пользователь %s (id=%s)", username, user["id"])
    return token_response(user["id"])


@router.post("/login")
def login(data: Credentials):
    username = data.username.strip()
    user = sql("SELECT id, password_hash FROM users WHERE username = %s", (username,))
    if not user or not verify_password(data.password, user["password_hash"]):
        log.warning("Неудачная попытка входа: %s", username)
        raise HTTPException(401, "Неверное имя пользователя или пароль")
    log.info("Вход пользователя %s (id=%s)", username, user["id"])
    return token_response(user["id"])
