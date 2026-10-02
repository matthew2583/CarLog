import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from backend.auth import current_user_id
from backend.models import KINDS, Record
from backend.services import check_record_date, own_car
from common.db import found, sql

log = logging.getLogger("carlog.records")
router = APIRouter(tags=["records"])


@router.get("/kinds")
def get_kinds():
    return KINDS


@router.get("/records")
def get_records(
    car_id: int | None = None,
    kind: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user_id: int = Depends(current_user_id),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "date_from не может быть позже date_to")

    query = (
        "SELECT r.* FROM records r JOIN cars c ON c.id = r.car_id WHERE c.user_id = %s"
    )
    args = [user_id]
    if car_id is not None:
        query += " AND r.car_id = %s"
        args.append(car_id)
    if kind:
        query += " AND r.kind = %s"
        args.append(kind)
    if date_from:
        query += " AND r.date >= %s"
        args.append(date_from)
    if date_to:
        query += " AND r.date <= %s"
        args.append(date_to)
    query += " ORDER BY r.date DESC, r.id DESC"
    return sql(query, args, many=True)


@router.get("/records/{record_id}")
def get_record(record_id: int, user_id: int = Depends(current_user_id)):
    return found(
        sql(
            "SELECT r.* FROM records r JOIN cars c ON c.id = r.car_id "
            "WHERE r.id = %s AND c.user_id = %s",
            (record_id, user_id),
        )
    )


@router.post("/records", status_code=201)
def create_record(record: Record, user_id: int = Depends(current_user_id)):
    car = own_car(record.car_id, user_id)
    check_record_date(record, car)
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


@router.put("/records/{record_id}")
def update_record(
    record_id: int, record: Record, user_id: int = Depends(current_user_id)
):
    car = own_car(record.car_id, user_id)
    check_record_date(record, car)
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


@router.delete("/records/{record_id}")
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
