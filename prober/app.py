import json
import os
import time
import urllib.error
import urllib.request

from prometheus_client import Gauge, start_http_server

BASE = os.environ.get("TARGET", "http://gateway")
INTERVAL, TIMEOUT = 5, 5
CREDS = {"username": "prober", "password": "prober-pass"}

SUCCESS = Gauge("carlog_probe_success", "1 - проба успешна, 0 - нет", ["probe"])
DURATION = Gauge("carlog_probe_duration_seconds", "Время пробы", ["probe"])


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return 0, b""


def probe(name, method, path, body=None, token=None):
    start = time.time()
    status, raw = call(method, path, body, token)
    DURATION.labels(name).set(time.time() - start)
    SUCCESS.labels(name).set(1 if status == 200 else 0)
    return status, raw


start_http_server(8102)
while True:
    probe("frontend", "GET", "/")
    probe("get_method", "GET", "/api/get_method")
    status, raw = probe("login", "POST", "/api/auth/login", CREDS)
    if status == 401:  # пользователя пробера ещё нет, создаём
        call("POST", "/api/auth/register", CREDS)
    if status == 200:
        probe("cars", "GET", "/api/cars", token=json.loads(raw)["access_token"])
    else:
        SUCCESS.labels("cars").set(0)
    time.sleep(INTERVAL)