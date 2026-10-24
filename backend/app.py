import logging

from fastapi import FastAPI

from backend.routers import cars, records
from common.config import config
from common.logging_setup import add_request_logging, setup_logging
from common.metrics import setup_metrics

setup_logging(config.LOG_LEVEL, "backend")
log = logging.getLogger("carlog")

app = FastAPI(title="CarLog", root_path="/api")
add_request_logging(app)
setup_metrics(app, config.BACKEND_METRICS_PORT)

app.include_router(cars.router)
app.include_router(records.router)

log.info("CarLog запущен")
