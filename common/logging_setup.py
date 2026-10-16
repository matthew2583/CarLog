import json
import logging
import sys
import time
from contextvars import ContextVar
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

trace_id_context: ContextVar[str | None] = ContextVar("trace_id", default=None)


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord):
        data = {
            **getattr(record, "fields", {}),
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "service.name": self.service,
            "logger_name": record.name,
        }
        if trace_id := trace_id_context.get():
            data["trace_id"] = trace_id
        if record.exc_info:
            data["stack_trace"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False, default=str)


def setup_logging(level: str, service: str):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service))
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)
    logging.captureWarnings(True)
    logging.getLogger("uvicorn.access").disabled = True


def add_request_logging(app: FastAPI):
    log = logging.getLogger("carlog.http")

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        trace_id = str(uuid4())
        token = trace_id_context.set(trace_id)
        started = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = trace_id
            return response
        except Exception:
            log.exception("Необработанная ошибка запроса")
            return JSONResponse({"detail": "Internal Server Error"}, status_code=500)
        finally:
            route = request.scope.get("route")
            log.log(
                logging.ERROR if status >= 500 else logging.INFO,
                "HTTP-запрос завершён",
                extra={"fields": {
                    "request.method": request.method,
                    "url.path": route.path if route else request.url.path,
                    "http.response.status_code": status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                }},
            )
            trace_id_context.reset(token)