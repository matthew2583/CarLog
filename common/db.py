import logging

import psycopg
from fastapi import HTTPException
from psycopg import IntegrityError, OperationalError
from psycopg.rows import dict_row

from common.config import config

log = logging.getLogger("carlog.db")


def sql(query, args=(), many=False):
    try:
        with psycopg.connect(
            config.DATABASE_URL, row_factory=dict_row, connect_timeout=5
        ) as connection:
            cursor = connection.execute(query, args)
            return cursor.fetchall() if many else cursor.fetchone()
    except IntegrityError as error:
        log.warning("Нарушение целостности БД: %s", str(error).splitlines()[0])
        raise HTTPException(409, str(error).splitlines()[0])
    except OperationalError:
        log.exception("База данных недоступна")
        raise HTTPException(503, "База данных временно недоступна")


def found(row):
    if not row:
        raise HTTPException(404, "Not found")
    return row
