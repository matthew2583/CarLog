import socket

from fastapi import APIRouter, FastAPI, Request
from prometheus_client import Gauge

from common.config import config
from common.db import sql

POD = socket.gethostname()
APP_INFO = Gauge("carlog_app_info", "Версия приложения", ["service", "version"])

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    # liveness: процесс жив
    return {"status": "ok"}


@router.get("/ready")
def ready():
    # readiness: под готов принимать трафик, только если доступна БД (503 иначе)
    sql("SELECT 1")
    return {"status": "ready"}


@router.get("/version")
def version():
    return {"version": config.APP_VERSION, "pod": POD}


def setup_version(app: FastAPI, service: str):
    # версия в метрике carlog_app_info и в заголовке каждого ответа
    APP_INFO.labels(service, config.APP_VERSION).set(1)

    @app.middleware("http")
    async def add_version_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-App-Version"] = config.APP_VERSION
        response.headers["X-Pod"] = POD
        return response
