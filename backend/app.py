import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import config
from backend.logging_setup import setup_logging
from backend.routers import cars, records, users

setup_logging(config.LOG_LEVEL)
log = logging.getLogger("carlog")

app = FastAPI(title="CarLog")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in config.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(cars.router)
app.include_router(records.router)

log.info("CarLog запущен, CORS: %s", config.CORS_ORIGINS)
