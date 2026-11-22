# Стратегии деплоя CarLog на Gateway API + minikube

Локальное окружение для ДЗ «Kubernetes. Стратегии деплоя». Всё поднимается на
вашей машине: **minikube** → **Envoy Gateway** (реализация Gateway API) →
**kube-prometheus-stack** (Prometheus + Grafana) → приложение **CarLog** в двух версиях
(`backend` v1.0.0 из Helm-чарта и `backend-v2` v2.0.0).

Показываем пять стратегий — **Rolling**, **Blue/Green**, **Canary**, **A/B**, **Shadow**. Трафик между версиями дробит **Gateway API**
(`HTTPRoute`), а не Ingress и не Istio VirtualService.

> Версии v1.0.0 и v2.0.0 отличаются только переменной `APP_VERSION` (образ один,
> `carlog-backend:1.3`). Версия видна в заголовке `X-App-Version`, в `GET /api/version`,
> в метрике `carlog_app_info` и в поле `app.version` JSON-логов.

---

## Что нужно

- Docker (запущен)
- `minikube`, `kubectl`, `helm` в `PATH`
- ~4 CPU и ~8 GB RAM для minikube, ~40 GB диска
- Доступ в интернет (тянем образы и чарты)

Проверить: `minikube version && kubectl version --client && helm version --short`.

---

## Быстрый старт

```bash
cd deploy

# 1. Поднять окружение: minikube + Envoy Gateway + Prometheus/Grafana + CarLog (v1)
./setup.sh

# 2. В отдельном терминале — генератор трафика через Envoy-прокси
./traffic.sh
```

`traffic.sh` сам найдёт Envoy-прокси, пробросит локальный порт `:8888` и будет
печатать версию и под, которые ответили на `GET /api/version` (сайт при этом открыт
в браузере на `http://localhost:8888`):

```text
21:04:11 | {"version":"v1.0.0","pod":"backend-6d4f7c9b8-x2k4p"}
```

`setup.sh` ставит базу: namespace, Gateway, ServiceMonitor, Helm-чарт CarLog (frontend,
auth-service, backend v1, db, prober) и маршруты. Вторая версия и маршруты каждой
стратегии применяются отдельно — см. ниже.

> **Правило: одна стратегия за раз.** Все стратегии используют namespace
> `carlog` и один Gateway `eg`. Перед переходом к следующей стратегии
> выполните `./reset.sh` — он удалит v2, вернёт backend на v1.0.0 и базовый маршрут,
> оставив Gateway, мониторинг и остальное приложение на месте.

---

## Доступ к Grafana

```bash
kubectl port-forward -n monitoring svc/kps-grafana 3001:80   # admin / admin
```

Откройте http://localhost:3001 → **Dashboards** → «CarLog Deployment Strategies
(Gateway API)». Дашборд провиженится автоматически (`setup.sh` создаёт ConfigMap
с меткой `grafana_dashboard=1` — sidecar Grafana подхватывает его сам), ручной
импорт `monitoring/grafana-dashboard.json` не нужен.

> Порт именно **3001**: на `localhost:3000` обычно уже висит Grafana
> демо-окружения прошлого семинара «Логи и метрики» (docker-compose), и
> port-forward на 3000 либо не поднимется, либо вы попадёте не в ту Grafana.

Дашборд строит `sum(rate(http_requests_total{namespace="carlog",handler!~"/health|/ready"}[2m])) by (version)`
— доли трафика между v1 и v2. Именно на нём видна разница стратегий.

---

## Стратегия 1 — Rolling (постепенный)

Один Deployment `backend` (из Helm-чарта), Kubernetes сам заменяет поды по одному.
Gateway API не дробит трафик — `HTTPRoute` всегда смотрит на сервис `backend`.
Версия меняется values-файлом для Helm (вместо `kubectl apply`, т.к. backend живёт в чарте).

```bash
# стартовая версия v1 (setup.sh уже поставил её; так можно вернуть вручную)
helm upgrade carlog ../helm/carlog -n carlog --reuse-values -f strategies/rolling/01-app-v1.yaml
kubectl rollout status deploy/backend -n carlog

# в другом терминале уже крутится ./traffic.sh — видно только v1.0.0
# накатываем v2:
helm upgrade carlog ../helm/carlog -n carlog --reuse-values -f strategies/rolling/02-app-v2.yaml

# наблюдаем постепенную замену подов
kubectl get pods -n carlog -l app=backend -w
```

В `traffic.sh` версии v1 и v2 будут чередоваться, пока все поды не станут v2.
На графике — плавный спад v1 и рост v2. `maxSurge: 1` / `maxUnavailable: 0`
означают обновление без простоя.

Откат: `kubectl rollout undo deploy/backend -n carlog` (или `helm rollback carlog -n carlog`).

```bash
./reset.sh   # перед следующей стратегией
```

---

## Стратегия 2 — Blue/Green

Обе версии подняты одновременно, трафик переключается одним движением.

```bash
# green (v1) уже работает (Deployment backend), blue (v2) поднимаем рядом
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog

# весь трафик на green (v1)
kubectl apply -f strategies/blue-green/httproute-green.yaml
# traffic.sh показывает только v1.0.0

# МГНОВЕННОЕ переключение на blue (v2)
kubectl apply -f strategies/blue-green/httproute-blue.yaml
# traffic.sh тут же показывает только v2.0.0

# мгновенный откат — снова green
kubectl apply -f strategies/blue-green/httproute-green.yaml
```

На графике — прямоугольная ступенька: доля v2 скачком 0 → 100%.

```bash
./reset.sh
```

---

## Стратегия 3 — Canary (по весу)

Постепенно увеличиваем долю новой версии. Обе версии уже подняты.

```bash
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog

# 90% v1 / 10% v2
kubectl apply -f strategies/canary/httproute-90-10.yaml
# смотрим traffic.sh и график: v2 ~10%

# 50 / 50
kubectl apply -f strategies/canary/httproute-50-50.yaml

# 0 / 100 — полный перекат на v2
kubectl apply -f strategies/canary/httproute-0-100.yaml
```

Откат на любом шаге — применить файл с меньшим весом v2. На графике — плавная
рампа доли v2: 10% → 50% → 100%.

```bash
./reset.sh
```

---

## Справочно: A/B testing (по заголовку)

Не «случайные 10%», а точно выбранная аудитория. Здесь — по HTTP-заголовку.

```bash
kubectl apply -f app/app-v2.yaml
kubectl apply -f strategies/ab/httproute-ab.yaml

GW=http://localhost:8888   # порт уже проброшен traffic.sh
curl -s "$GW/api/version"                          # -> v1.0.0
curl -s -H 'x-user-group: beta' "$GW/api/version"  # -> v2.0.0
HEADER='x-user-group: beta' ./traffic.sh          # поток только для beta
```

Заголовок `x-user-group: beta` на пути `/api` уводит на v2, все остальные — на v1. Так же можно
матчить query-параметры, метод, cookie.

```bash
./reset.sh
```

---

## Справочно: Shadow (зеркалирование)

Пользователь получает ответ с v1, а копия запроса уходит на v2. Новая версия
проверяется боевым трафиком, не влияя на пользователей.

```bash
kubectl apply -f app/app-v2.yaml
kubectl apply -f strategies/shadow/httproute-shadow.yaml

# traffic.sh по-прежнему показывает только v1.0.0 (ответы идут с v1),
# но метрики и логи v2 растут — туда зеркалируется копия каждого запроса:
kubectl logs -n carlog -l app=backend-v2 --tail=20
```

> Зеркалируются только GET (запись задвоилась бы: обе версии работают с одной БД).

> `RequestMirror` проверен вживую на Envoy Gateway v1.10 со стандартными CRD —
> работает без experimental-канала. Если у вас более старая версия Gateway API и
> фильтр не принимается, поставьте experimental-канал CRD:
> ```bash
> kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.7.0/experimental-install.yaml
> ```

```bash
./reset.sh
```

---

## Структура

```text
setup.sh            minikube + Envoy Gateway + kube-prometheus-stack + CarLog (Helm) + маршруты
teardown.sh         разобрать всё (./teardown.sh --minikube — ещё и удалить minikube)
reset.sh            сбросить приложение между стратегиями (Gateway/мониторинг целы)
traffic.sh          генератор трафика через Envoy-прокси + port-forward
00-namespace.yaml   namespace carlog
01-gateway.yaml     GatewayClass `eg` + Gateway `eg` (HTTP :80)
02-carlog-routes.yaml  постоянные маршруты: /api/auth -> auth-service, / -> frontend
app/
  app-v2.yaml       Deployment+Service backend-v2 (blue / canary); v1 — backend из helm/carlog
strategies/
  rolling/          01-app-v1.yaml, 02-app-v2.yaml (values для Helm), httproute-backend.yaml
  blue-green/       httproute-green.yaml, httproute-blue.yaml
  canary/           httproute-90-10.yaml, -50-50.yaml, -0-100.yaml
  ab/               httproute-ab.yaml
  shadow/           httproute-shadow.yaml
logs/               сюда пишем логи стратегий: ./traffic.sh | tee logs/<стратегия>.log
monitoring/
  servicemonitor.yaml      ServiceMonitor для Prometheus Operator
  grafana-dashboard.json   дашборд «RPS по версиям»
```

---

## Как это устроено (коротко)

- **GatewayClass `eg`** говорит: «этот класс обслуживает контроллер Envoy Gateway».
- **Gateway `eg`** — точка входа (слушатель HTTP :80). Envoy Gateway поднимает под
  него Envoy-прокси в namespace `envoy-gateway-system`.
- **HTTPRoute `backend`** — правила маршрутизации для `/api`: на какие сервисы и в какой доле
  (`weight`) слать трафик. Меняя только этот ресурс, мы реализуем blue/green,
  canary, A/B и shadow — приложение не трогаем.
- **ServiceMonitor** объясняет Prometheus, где снимать метрики; метрика
  `http_requests_total` приходит из самого приложения (prometheus-fastapi-instrumentator),
  а `version` добавляется relabeling-ом из метки пода.

Состояние приложения вынесено из подов (PostgreSQL + общий JWT-секрет), пробы — `/health` и
`/ready`, реплики: backend — 4, auth-service и frontend — 2.

---

## Разбор окружения

```bash
./teardown.sh              # удалить CarLog, Prometheus/Grafana, Envoy Gateway, namespace
./teardown.sh --minikube   # ...и остановить/удалить minikube
```
