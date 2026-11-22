#!/usr/bin/bash
set -e

mkdir -p logs
LOG="logs/canary.log"

echo "Запускаем трафик и запись в $LOG..."
./traffic.sh | tee "$LOG" &
TRAFFIC_PID=$!
trap 'kill "$TRAFFIC_PID" 2>/dev/null || true' EXIT INT TERM
sleep 3

# Поднимаем v2
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog

# Переключаем на 90% v1 / 10% v2
kubectl apply -f strategies/canary/httproute-90-10.yaml
sleep 20

# Переключаем на 50% v1 / 50% v2
kubectl apply -f strategies/canary/httproute-50-50.yaml
sleep 20

# Переключаем на 0% v1 / 100% v2
kubectl apply -f strategies/canary/httproute-0-100.yaml
sleep 20

# Сброс
./reset.sh
