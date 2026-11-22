#!/usr/bin/env bash
# Сбрасывает приложение между стратегиями: удаляет v2 (backend-v2), возвращает backend
# из Helm-чарта на v1.0.0 и базовый маршрут /api -> backend, НЕ трогая Gateway, мониторинг,
# namespace, frontend, auth-service и базу.
# Используйте перед переходом к следующей стратегии, чтобы селекторы не пересекались.
set -euo pipefail
NS="${NS:-carlog}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${HERE}/.." && pwd)"

echo "Удаляю v2 и возвращаю маршрут в namespace $NS ..."
# Сначала переключаем маршрут на backend v1 (без удаления, чтобы не было 404)
kubectl apply -f "${HERE}/strategies/rolling/httproute-backend.yaml"
kubectl delete deployment backend-v2 -n "$NS" --ignore-not-found
kubectl delete service backend-v2 -n "$NS" --ignore-not-found
helm upgrade carlog "${ROOT}/helm/carlog" --namespace "$NS" --reuse-values \
  -f "${HERE}/strategies/rolling/01-app-v1.yaml"
kubectl rollout status deploy/backend -n "$NS"
echo "Готово. Gateway 'eg', ServiceMonitor и monitoring на месте."
echo "Можно применять следующую стратегию."
