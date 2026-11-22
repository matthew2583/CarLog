#!/usr/bin/bash
set -e

mkdir -p logs
LOG="logs/ab.log"
> "$LOG"

# Применяем v2 и маршрут A/B
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog
kubectl apply -f strategies/ab/httproute-ab.yaml

echo "=== Обычные запросы (без заголовка -> v1.0.0) ==="
./traffic.sh 15 | tee -a "$LOG"

echo "=== Запросы с заголовком beta (-> v2.0.0) ==="
HEADER='x-user-group: beta' ./traffic.sh 25 | tee -a "$LOG"

# Сброс
./reset.sh
