from fastapi import FastAPI
from prometheus_client import start_http_server
from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app: FastAPI, port: int):
    Instrumentator().instrument(app)
    start_http_server(port)
