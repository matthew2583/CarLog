import logging
from datetime import date
from decimal import Decimal

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg import IntegrityError, OperationalError
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from backend.auth import create_token, current_user_id, hash_password, verify_password
from backend.config import config
from backend.logging_setup import setup_logging

setup_logging(config.LOG_LEVEL)
log = logging.getLogger("CarLog")

app = FastAPI(title="CarLog")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in config.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
log.info("CarLog запущен, CORS: %s", config.CORS_ORIGINS)


class Creadentials(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class Car(BaseModel):
    brand: str
    model: str
    year: int | None = None
    mileage: int = 0


class Record(BaseModel):
    car_id: int
    date: date
    kind: str
    cost: Decimal = 0.0
    note: str | None = None


def sql(query, args=(), many=False):
    try:
        with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as c:
            cur = c.execute(query, args)
            return cur.fetchall() if many else cur.fetchone()
    except IntegrityError as e:
        log.warning("Нарушение целостности БД: %s", str(e).splitlines()[0])
        raise HTTPException(409, str(e).splitlines()[0])
    except OperationalError:
        log.exception("База данных недоступна")
        raise HTTPException(503, "База данных временно недоступна")


def toker_response(user_id: int):
    return {"access_token": create_token(user_id), "token_type": "bearer"}


def found(row):
    if not row:
        raise HTTPException(404, "Not found")
    return row


def check_own_car(user_id: int, car_id: int):
    found(sql("SELECT id FROM cars WHERE id = %s AND user_id = %s", (car_id, user_id)))


@app.post("/auth/register")
def register(data: Creadentials):
    username = data.username.strip()
    if sql("SELECT id FROM users WHERE username = %s", (username,)):
        raise HTTPException(409, "Пользователь с таким именем уже существует")
    user = sql(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
        (username, hash_password(data.password)),
    )
    log.info("Зарегистрирован новый пользователь: %s (id: %d)", username, user["id"])
    return toker_response(user["id"])


@app.post("/auth/login")
def login(data: Creadentials):
    username = data.username.strip()
    user = sql("SELECT  id, password_hash FROM users WHERE username = %s", (username,))
    if not user or not verify_password(data.password, user["password_hash"]):
        log.info("Неудачная попытка входа для пользователя: %s", username)
        raise HTTPException(401, "Неверное имя пользователя или пароль")
    log.info("Пользователь %s (id: %d) успешно вошёл в систему", username, user["id"])
    return toker_response(user["id"])


@app.get("/cars")
def get_cars(user_id: int = Depends(current_user_id)):
    return sql(
        "SELECT * FROM cars WHERE user_id = %s ORDER BY id", (user_id,), many=True
    )


@app.get("/cars/{car_id}")
def get_car(car_id: int, user_id: int = Depends(current_user_id)):
    return found(
        sql("SELECT * FROM cars WHERE id = %s AND user_id = %s", (car_id, user_id))
    )


@app.post("/cars", status_code=201)
def create_car(car: Car, user_id: int = Depends(current_user_id)):
    created = sql(
        "INSERT INTO cars (brand, model, year, mileage, user_id)"
        "VALUES (%s, %s, %s, %s, %s) RETURNING *",
        (car.brand, car.model, car.year, car.mileage, user_id),
    )
    log.info(
        "Пользователь %d создал машину: %s %s (id: %d)",
        user_id,
        car.brand,
        car.model,
        created["id"],
    )
    return created


@app.put("/cars/{car_id}")
def update_car(car_id: int, car: Car, user_id: int = Depends(current_user_id)):
    return found(
        sql(
            "UPDATE cars SET brand = %s, model = %s, year = %s, mileage = %s "
            "WHERE id = %s AND user_id = %s RETURNING *",
            (car.brand, car.model, car.year, car.mileage, car_id, user_id),
        )
    )


@app.delete("/cars/{car_id}")
def delete_car(car_id: int, user_id: int = Depends(current_user_id)):
    deleted = found(
        sql(
            "DELETE FROM cars WHERE id = %s AND user_id = %s RETURNING *",
            (car_id, user_id),
        )
    )
    log.info(
        "Пользователь %d удалил машину: %s %s (id: %d)",
        user_id,
        deleted["brand"],
        deleted["model"],
        car_id,
    )
    return deleted


@app.get("/records")
def get_records(user_id: int = Depends(current_user_id)):
    return sql(
        "SELECT r.* FROM records r JOIN cars c ON c.id = r.car_id "
        "WHERE c.user_id = %s ORDER BY r.date DESC, r.id DESC",
        (user_id,),
        many=True,
    )


@app.get("/records/{record_id}")
def get_record(record_id: int, user_id: int = Depends(current_user_id)):
    return found(
        sql(
            "SELECT r.* FROM records r JOIN cars c ON c.id = r.car_id "
            "WHERE r.id = %s AND c.user_id = %s",
            (record_id, user_id),
        )
    )


@app.post("/records", status_code=201)
def create_record(record: Record, user_id: int = Depends(current_user_id)):
    check_own_car(record.car_id, user_id)
    created = sql(
        "INSERT INTO records (car_id, date, kind, cost, note) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING *",
        (record.car_id, record.date, record.kind, record.cost, record.note),
    )
    log.info(
        "Пользователь %d создал запись: %s (id: %d)",
        user_id,
        record.kind,
        created["id"],
    )
    return created


@app.put("/records/{record_id}")
def update_record(
    record_id: int, record: Record, user_id: int = Depends(current_user_id)
):
    check_own_car(record.car_id, user_id)  # нельзя перенести запись на чужую машину
    return found(
        sql(
            "UPDATE records SET car_id = %s, date = %s, kind = %s, cost = %s, note = %s "
            "WHERE id = %s AND car_id IN (SELECT id FROM cars WHERE user_id = %s) "
            "RETURNING *",
            (
                record.car_id,
                record.date,
                record.kind,
                record.cost,
                record.note,
                record_id,
                user_id,
            ),
        )
    )


@app.delete("/records/{record_id}")
def delete_record(record_id: int, user_id: int = Depends(current_user_id)):
    deleted = found(
        sql(
            "DELETE FROM records WHERE id = %s "
            "AND car_id IN (SELECT id FROM cars WHERE user_id = %s) RETURNING *",
            (record_id, user_id),
        )
    )
    log.info(
        "Пользователь %d удалил запись: %s (id: %d)",
        user_id,
        deleted["kind"],
        record_id,
    )
    return deleted
