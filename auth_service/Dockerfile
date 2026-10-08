FROM python:3.14-slim

WORKDIR /srv

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
RUN pip install poetry

COPY poetry.lock pyproject.toml ./
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-root

COPY auth_service ./auth_service
COPY common ./common

CMD ["sh", "-c", "exec uvicorn auth_service.app:app --host 0.0.0.0 --port ${AUTH_PORT}"]
