import logging

from fastapi import APIRouter, Depends

from backend.auth import current_user_id
from backend.db import found, sql
from backend.models import Car
from backend.services import build_car_stats, check_mileage, own_car

log = logging.getLogger("carlog.cars")
router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("")
def get_cars(user_id: int = Depends(current_user_id)):
    return sql(
        "SELECT * FROM cars WHERE user_id = %s ORDER BY id", (user_id,), many=True
    )


@router.get("/{car_id}")
def get_car(car_id: int, user_id: int = Depends(current_user_id)):
    return own_car(car_id, user_id)


@router.post("", status_code=201)
def create_car(car: Car, user_id: int = Depends(current_user_id)):
    created = sql(
        "INSERT INTO cars (brand, model, year, mileage, user_id) "
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


@router.put("/{car_id}")
def update_car(car_id: int, car: Car, user_id: int = Depends(current_user_id)):
    check_mileage(own_car(car_id, user_id), car.mileage)
    return found(
        sql(
            "UPDATE cars SET brand = %s, model = %s, year = %s, mileage = %s "
            "WHERE id = %s AND user_id = %s RETURNING *",
            (car.brand, car.model, car.year, car.mileage, car_id, user_id),
        )
    )


@router.delete("/{car_id}")
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


@router.get("/{car_id}/stats")
def car_stats(car_id: int, user_id: int = Depends(current_user_id)):
    own_car(car_id, user_id)
    return build_car_stats(car_id)
