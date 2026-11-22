#!/usr/bin/bash
set -e

mkdir -p logs
LOG="logs/blue-green.log"

echo "Запускаем трафик и запись в $LOG..."
./traffic.sh | tee "$LOG" &
TRAFFIC_PID=$!
trap 'kill "$TRAFFIC_PID" 2>/dev/null || true' EXIT INT TERM
sleep 3

# Поднимаем v2 рядом с v1
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog
kubectl apply -f strategies/blue-green/httproute-green.yaml
sleep 10

# Мгновенно переключаем 100% трафика на Blue (v2)
kubectl apply -f strategies/blue-green/httproute-blue.yaml
sleep 15

# Мгновенный откат обратно на Green (v1)
kubectl apply -f strategies/blue-green/httproute-green.yaml
sleep 10

# Сброс
./reset.sh
