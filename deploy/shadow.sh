#!/usr/bin/bash
set -e

mkdir -p logs
LOG="logs/shadow.log"

# Применяем v2 и маршрут Shadow
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog
kubectl apply -f strategies/shadow/httproute-shadow.yaml

echo "Запускаем трафик..."
./traffic.sh 30 | tee "$LOG"

echo "Логи backend-v2:"
sleep 2
kubectl logs -n carlog -l app=backend-v2 --tail=15 | tee -a "$LOG"

# Сброс
./reset.sh
