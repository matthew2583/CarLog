## CarLog
CarLog - приложение для учёта расходов на автомобиль. Пользователь регистрируется, заводит свои автомобили и ведёт по ним журнал: ТО, ремонты, заправки, страховки, мойки и прочее. Записи можно создавать, просматривать, редактировать, удалять, фильтровать по автомобилю, типу и периоду, а также смотреть по каждой машине статистику расходов.

## Стек реализации

| Компонент | Технология |
|---|---|
| Бэкенд (API) | Python 3.14, FastAPI, Uvicorn |
| Сервис авторизации | Python, FastAPI, PyJWT, PBKDF2-HMAC-SHA256 |
| Фронтенд | HTML + CSS + JS, раздаётся простым HTTP-сервером Python |
| Шлюз | nginx  |
| БД | PostgreSQL 16 |
| Доступ к БД | psycopg |
| Миграции | Alembic |
| Конфигурация | pydantic-settings |
| Зависимости | Poetry |
| Контейнеризация | Docker, Docker Compose |
| Логи | Vector, VictoriaLogs |
| Метрики | prometheus-client, prometheus-fastapi-instrumentator, postgres-exporter, VictoriaMetrics, vmagent |

## Запуск приложения в Minikube

### Установка в Minikube

Манифесты приложения оформлены как Helm-чарт и находятся в [helm/carlog](helm/carlog).
Сначала запустите Minikube и соберите локальные образы:

```sh
minikube start
minikube image build -t carlog-backend:1.2 -f backend/Dockerfile .
minikube image build -t carlog-auth:1.1 -f auth_service/Dockerfile .
minikube image build -t carlog-frontend:1.0 -f frontend/Dockerfile frontend
minikube image build -t carlog-prober:1.1 -f prober/Dockerfile prober
```

Установите чарт:

```sh
helm upgrade --install carlog ./helm/carlog \
  --namespace carlog \
  --create-namespace
```

После установки дождитесь запуска подов:

```sh
kubectl get pods -n carlog
```

Откройте приложение:

```sh
kubectl port-forward -n carlog svc/gateway 8080:80
```

Откройте в браузере `http://localhost:8080`. Миграция базы данных запускается Helm автоматически.

## Логи в VictoriaLogs

Backend и auth-service выводят логи в stdout одной JSON-записью на строку: UTC-время, уровень, сообщение и имя сервиса. Также добавляются `logger_name`, имя pod/контейнера и `request_id`; HTTP-события содержат метод, маршрут, статус и `duration_ms`. Vector отбирает только pod-логи namespace `carlog`, разбирает JSON и отправляет события в VictoriaLogs; строки, которые не удалось разобрать, сохраняются с полем `parse_error: true`.

Установите чарт VictoriaLogs в кластер:

```sh
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
kubectl apply -f helm/victoria-logs/namespace.yml
helm upgrade --install vl vm/victoria-logs-single --namespace logging --version 0.13.10 --reuse-values -f helm/victoria-logs/values.yml
```

Для доступа к интерфейсу VictoriaLogs используйте port-forward:

```sh
kubectl port-forward -n logging svc/vl-victoria-logs-single-server 9428:9428
```

Откройте `http://localhost:9428/select/vmui/`. Срок хранения - 7 дней. Размер существующего PVC не следует менять через `helm upgrade`: Kubernetes считает `volumeClaimTemplates` StatefulSet неизменяемым.

## Метрики в VictoriaMetrics

Backend и auth-service отдают `/metrics` на своих портах, 8100 и 8101. Эти порты не проброшены ни в Service, ни в nginx, поэтому снаружи метрики не видны. Метрики Postgres отдаёт postgres-exporter на порту 9187, он работает вторым контейнером в поде `db`.

Собирает всё это vmagent. Он сам находит поды по аннотациям `prometheus.io/scrape`, `prometheus.io/port` и `prometheus.io/path` и пишет метрики в VictoriaMetrics. Порт в аннотации должен совпадать с `containerPort` в манифесте, иначе под в сборе не окажется.

Репозиторий `vm` уже добавлен в разделе про логи. Установите VictoriaMetrics и vmagent:

```sh
kubectl apply -f helm/victoria-metrics/namespace.yml
helm upgrade --install vm-single vm/victoria-metrics-single --namespace monitoring --version 0.49.0 -f helm/victoria-metrics/single-values.yml
helm upgrade --install vm-agent vm/victoria-metrics-agent --namespace monitoring --version 0.50.0 -f helm/victoria-metrics/agent-values.yml
kubectl get pods -n monitoring
```

Если приложение уже запущено, после `kubectl apply` обновлённых манифестов перезапустите поды, чтобы подтянулись аннотации и новые образы:

```sh
kubectl rollout restart deployment/backend deployment/auth-service -n carlog
kubectl delete pod db-0 -n carlog
```

Чтобы посмотреть метрики нужно пробросьте порт хранилища и откройте `http://localhost:8428/vmui`:

```sh
kubectl port-forward svc/vm-single-victoria-metrics-single-server -n monitoring 8428:8428
```

Чтобы проверить, что vmagent видит все таргеты нужно пробросить порт агента и откройть `http://localhost:8429/targets`. В `kubernetes-pods` должны быть три пода `carlog`: backend, auth-service и db-0.

```sh
kubectl port-forward svc/vm-single-victoria-metrics-agent -n monitoring 8429:8429
```

### Алерты

Правила алертов находятся в [monitoring/alerts.yml](monitoring/alerts.yml), Secret
с настройками Alertmanager - в [monitoring/alertmanager-secret.yml](monitoring/alertmanager-secret.yml),
а учебный SMTP-сервис MailHog - в [monitoring/mailhog.yml](monitoring/mailhog.yml).

Создайте ConfigMap и установите vmalert вместе с Alertmanager:

```sh
kubectl -n monitoring create configmap carlog-alerts \
  --from-file=alert-rules.yaml=monitoring/alerts.yml
kubectl apply -f monitoring/mailhog.yml
kubectl apply -f monitoring/alertmanager-secret.yml
helm upgrade --install vm-single vm/victoria-metrics-alert \
  --namespace monitoring \
  -f helm/victoria-metrics/vmalert-values.yml
```

Откройте интерфейс MailHog:

```sh
kubectl port-forward -n monitoring svc/mailhog 8025:8025
```

После этого письма доступны по адресу `http://localhost:8025`.

Для проверки можно временно установить `getMethodFailRate=1` при обновлении
чарта, дождаться письма `CarLogProbeFailed`, а затем вернуть значение `0`:

```sh
helm upgrade carlog ./helm/carlog --namespace carlog --set getMethodFailRate=1
helm upgrade carlog ./helm/carlog --namespace carlog --set getMethodFailRate=0
```

### Какие метрики есть

Метрики рантайма и фреймворка отдают `prometheus-client` и `prometheus-fastapi-instrumentator`: память и CPU процесса, сборщик мусора Python, число и длительность HTTP-запросов. Метрики Postgres начинаются с `pg_`.

Бизнес-метрики приложения:

| Метрика | Что считает |
|---|---|
| `carlog_auth_registrations_total` | зарегистрированных пользователей |
| `carlog_auth_logins_total{result}` | попытки входа, `success` или `failed` |
| `carlog_cars_created_total` | созданные автомобили |
| `carlog_records_created_total{kind}` | созданные записи по типам: ТО, ремонт, заправка и так далее |
| `carlog_records_cost_total{kind}` | сумма расходов в созданных записях по типам |
| `carlog_operations_rejected_total{reason}` | отклонённые операции: `mileage_decrease` (пробег уменьшили) и `date_before_car_year` (дата раньше года выпуска) |

## Основные сущности

- **User** - пользователь (`id`, `username` - уникален, `password_hash`).
- **Car** - автомобиль (`id`, `user_id` -> User, `brand`, `model`, `year`, `mileage`).
- **Record** - запись обслуживания (`id`, `car_id` -> Car, `date`, `kind`, `cost`, `note`).

Связи: User 1-N Car, Car 1-N Record; удаление каскадное (`ON DELETE CASCADE`).

### CRUD и бизнес-логика

CRUD (REST) реализован для `Car` (`/cars`) и `Record` (`/records`). Дополнительно:

- **Аутентификация и изоляция данных.** Каждый пользователь видит и изменяет только свои машины и записи; чужие объекты возвращают 404.
- **Правила предметной области:**
  - пробег автомобиля нельзя уменьшить (409);
  - дата записи не может быть в будущем и раньше года выпуска автомобиля (422);
  - тип записи - из справочника (`GET /kinds`);
  - запись можно привязать только к своей машине.
- **Статистика** `GET /cars/{id}/stats`: число записей, общая сумма, средние траты в месяц, последняя запись, разбивка по типам и по месяцам (агрегация в SQL).
- **Фильтрация записей**: `GET /records` с параметрами `car_id`, `kind`, `date_from` и `date_to`.
- **Валидация** входных данных (Pydantic) и обработка ошибок БД (409 при нарушении целостности, 503 при недоступности БД).
