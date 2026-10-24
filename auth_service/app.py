import logging

from fastapi import APIRouter, FastAPI, HTTPException

from auth_service.auth import create_token, hash_password, verify_password
from auth_service.metrics import LOGINS, REGISTRATIONS
from auth_service.models import Credentials
from common.config import config
from common.db import sql
from common.logging_setup import add_request_logging, setup_logging
from common.metrics import setup_metrics

setup_logging(config.LOG_LEVEL, "auth-service")
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
    REGISTRATIONS.inc()
    log.info("Пользователь зарегистрирован", extra={"fields": {"user.id": user["id"]}})
    return token_response(user["id"])


@router.post("/login")
def login(data: Credentials):
    username = data.username.strip()
    user = sql("SELECT id, password_hash FROM users WHERE username = %s", (username,))
    if not user or not verify_password(data.password, user["password_hash"]):
        LOGINS.labels("failed").inc()
        log.warning("Вход отклонён")
        raise HTTPException(401, "Неверное имя пользователя или пароль")
    LOGINS.labels("success").inc()
    log.info("Пользователь вошёл в систему", extra={"fields": {"user.id": user["id"]}})
    return token_response(user["id"])


app = FastAPI(title="CarLog Auth", root_path="/api/auth")
add_request_logging(app)
setup_metrics(app, config.AUTH_METRICS_PORT)
app.include_router(router)
log.info("Сервис авторизации запущен")
