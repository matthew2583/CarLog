#!/usr/bin/bash
set -e

# 1. Применяем v2 и маршрут A/B
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog
kubectl apply -f strategies/ab/httproute-ab.yaml

echo "Обычный запрос (-> v1.0.0):"
curl -s http://localhost:8888/api/version
echo ""

echo "Запрос с заголовком beta (-> v2.0.0):"
curl -s -H 'x-user-group: beta' http://localhost:8888/api/version
echo ""

# 2. Сброс
./reset.sh
