from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

KINDS = ["ТО", "Ремонт", "Заправка", "Страховка", "Мойка", "Другое"]
MIN_YEAR = 1950


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class Car(BaseModel):
    brand: str = Field(max_length=50)
    model: str = Field(max_length=50)
    year: int | None = None
    mileage: int = Field(default=0, ge=0, le=2000000)

    @field_validator("brand", "model")
    @classmethod
    def not_blank(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError("не может быть пустым")
        return v

    @field_validator("year")
    @classmethod
    def year_in_range(cls, v: int | None):
        max_year = date.today().year + 1
        if v is not None and not (MIN_YEAR <= v <= max_year):
            raise ValueError(f"год должен быть от {MIN_YEAR} до {max_year}")
        return v


class Record(BaseModel):
    car_id: int
    date: date
    kind: str
    cost: Decimal = Field(default=Decimal(0), ge=0, max_digits=10, decimal_places=2)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("date")
    @classmethod
    def not_in_future(cls, v: date):
        if v > date.today():
            raise ValueError("дата не может быть в будущем")
        return v

    @field_validator("kind")
    @classmethod
    def known_kind(cls, v: str):
        if v not in KINDS:
            raise ValueError("допустимые типы: " + ", ".join(KINDS))
        return v
