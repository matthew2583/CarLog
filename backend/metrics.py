from prometheus_client import Counter

from backend.models import KINDS

CARS_CREATED = Counter("carlog_cars_created", "Создано автомобилей")
RECORDS_CREATED = Counter(
    "carlog_records_created", "Создано записей обслуживания", ["kind"]
)
RECORDS_COST = Counter(
    "carlog_records_cost", "Суммарная стоимость записей обслуживания", ["kind"]
)
REJECTED = Counter("carlog_rejected", "Отклонено запросов", ["reason"])

for kind in KINDS:
    RECORDS_CREATED.labels(kind=kind)
    RECORDS_COST.labels(kind=kind)
for reason in ("mileage_decrease", "date_before_car_year"):
    REJECTED.labels(reason)
