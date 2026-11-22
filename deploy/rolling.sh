#!/usr/bin/bash
set -e

mkdir -p logs
LOG="logs/rolling.log"

echo "Запускаем трафик и запись в $LOG..."
./traffic.sh | tee "$LOG" &
TRAFFIC_PID=$!
trap 'kill "$TRAFFIC_PID" 2>/dev/null || true' EXIT INT TERM
sleep 3

# Накатываем v2
helm upgrade carlog ../helm/carlog -n carlog --reuse-values -f strategies/rolling/02-app-v2.yaml
kubectl rollout status deploy/backend -n carlog
sleep 15

# Откат обратно на v1
kubectl rollout undo deploy/backend -n carlog
kubectl rollout status deploy/backend -n carlog
sleep 10

# Сброс
./reset.sh
