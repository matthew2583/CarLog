import logging

from fastapi import FastAPI

from backend.routers import cars, records
from common.config import config
from common.logging_setup import add_request_logging, setup_logging

setup_logging(config.LOG_LEVEL, "backend")
log = logging.getLogger("carlog")

app = FastAPI(title="CarLog", root_path="/api")
add_request_logging(app)

app.include_router(cars.router)
app.include_router(records.router)

log.info("CarLog запущен")
