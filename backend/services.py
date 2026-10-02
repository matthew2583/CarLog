import logging
from datetime import date
from decimal import Decimal

from fastapi import HTTPException

from backend.models import Record
from common.db import found, sql

log = logging.getLogger("carlog.services")


def own_car(car_id: int, user_id: int):
    return found(
        sql("SELECT * FROM cars WHERE id = %s AND user_id = %s", (car_id, user_id))
    )


def check_mileage(car: dict, new_mileage: int):
    if new_mileage < car["mileage"]:
        log.info("Отклонено уменьшение пробега авто id=%s", car["id"])
        raise HTTPException(
            409, f"Пробег не может быть меньше текущего ({car['mileage']})"
        )


def check_record_date(record: Record, car: dict):
    if car["year"] and record.date.year < car["year"]:
        log.info(
            "Отклонена запись: дата %s раньше года выпуска %s", record.date, car["year"]
        )
        raise HTTPException(
            422, f"Дата записи раньше года выпуска автомобиля ({car['year']})"
        )


def months_between(first: date, last: date) -> int:
    return (last.year - first.year) * 12 + (last.month - first.month) + 1


def build_car_stats(car_id: int):
    total = sql(
        "SELECT COUNT(*) AS count, COALESCE(SUM(cost), 0) AS total, "
        "MIN(date) AS first_date, MAX(date) AS last_date "
        "FROM records WHERE car_id = %s",
        (car_id,),
    )
    by_kind = sql(
        "SELECT kind, COUNT(*) AS count, SUM(cost) AS total "
        "FROM records WHERE car_id = %s GROUP BY kind ORDER BY total DESC",
        (car_id,),
        many=True,
    )
    by_month = sql(
        "SELECT to_char(date, 'YYYY-MM') AS month, SUM(cost) AS total "
        "FROM records WHERE car_id = %s GROUP BY month ORDER BY month",
        (car_id,),
        many=True,
    )

    avg_per_month = Decimal(0)
    if total["count"]:
        months = months_between(total["first_date"], total["last_date"])
        avg_per_month = (total["total"] / months).quantize(Decimal("0.01"))

    return {
        "car_id": car_id,
        "records_count": total["count"],
        "total_cost": total["total"],
        "avg_per_month": avg_per_month,
        "last_record_date": total["last_date"],
        "by_kind": by_kind,
        "by_month": by_month,
    }
