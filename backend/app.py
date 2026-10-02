import logging

from fastapi import FastAPI

from backend.config import config
from backend.logging_setup import setup_logging
from backend.routers import cars, records, users

setup_logging(config.LOG_LEVEL)
log = logging.getLogger("carlog")

app = FastAPI(title="CarLog", root_path="/api")

app.include_router(users.router)
app.include_router(cars.router)
app.include_router(records.router)

log.info("CarLog запущен")
