import os
import psycopg
from psycopg import IntegrityError
from psycopg.rows import dict_row
from decimal import Decimal
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="CarLog")


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
        with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row) as c:
            cur = c.execute(query, args)
            return cur.fetchall() if many else cur.fetchone()
    except IntegrityError as e:
        raise HTTPException(409, str(e).splitlines()[0])


def found(row):
    if not row:
        raise HTTPException(404, "Not found")
    return row


@app.get("/cars")
def get_cars():
    return sql("SELECT * FROM cars", many=True)


@app.get("/cars/{car_id}")
def get_car(car_id: int):
    return found(sql("SELECT * FROM cars WHERE id = %s", (car_id,)))


@app.post("/cars")
def create_car(car: Car):
    return sql(
        "INSERT INTO cars (brand, model, year, mileage) VALUES (%s, %s, %s, %s) RETURNING *",
        (car.brand, car.model, car.year, car.mileage),
    )


@app.put("/cars/{car_id}")
def update_car(car_id: int, car: Car):
    return found(
        sql(
            "UPDATE cars SET brand = %s, model = %s, year = %s, mileage = %s WHERE id = %s RETURNING *",
            (car.brand, car.model, car.year, car.mileage, car_id),
        )
    )


@app.delete("/cars/{car_id}")
def delete_car(car_id: int):
    return found(sql("DELETE FROM cars WHERE id = %s RETURNING *", (car_id,)))


@app.get("/records")
def get_records():
    return sql("SELECT * FROM records", many=True)


@app.get("/records/{record_id}")
def get_record(record_id: int):
    return found(sql("SELECT * FROM records WHERE id = %s", (record_id,)))


@app.post("/records")
def create_record(record: Record):
    return sql(
        "INSERT INTO records (car_id, date, kind, cost, note) VALUES (%s, %s, %s, %s, %s) RETURNING *",
        (record.car_id, record.date, record.kind, record.cost, record.note),
    )


@app.put("/records/{record_id}")
def update_record(record_id: int, record: Record):
    return found(
        sql(
            "UPDATE records SET car_id = %s, date = %s, kind = %s, cost = %s, note = %s WHERE id = %s RETURNING *",
            (
                record.car_id,
                record.date,
                record.kind,
                record.cost,
                record.note,
                record_id,
            ),
        )
    )


@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    return found(sql("DELETE FROM records WHERE id = %s RETURNING *", (record_id,)))


app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend"), html=True))
