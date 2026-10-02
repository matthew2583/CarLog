import logging

from fastapi import APIRouter, FastAPI, HTTPException

from auth_service.auth import create_token, hash_password, verify_password
from auth_service.config import config
from auth_service.db import sql
from auth_service.models import Credentials
from common.logging_setup import setup_logging

setup_logging(config.LOG_LEVEL)
log = logging.getLogger("auth_service")

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


app = FastAPI(title="CarLog Auth", root_path="/api/auth")
app.include_router(router)
log.info("Auth service запущен")
