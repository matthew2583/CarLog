FROM python:3.14-slim

WORKDIR /srv

RUN apt-get update && apt-get install -y libpq5
RUN pip install poetry

COPY poetry.lock pyproject.toml ./
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-root

COPY . .

CMD ["sh", "-c", "exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
