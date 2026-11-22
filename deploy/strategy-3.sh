#!/usr/bin/bash
set -e

# 1. Поднимаем v2
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog

# 2. Переключаем на 90% v1 / 10% v2
kubectl apply -f strategies/canary/httproute-90-10.yaml
sleep 20

# 3. Переключаем на 50% v1 / 50% v2
kubectl apply -f strategies/canary/httproute-50-50.yaml
sleep 20

# 4. Переключаем на 0% v1 / 100% v2
kubectl apply -f strategies/canary/httproute-0-100.yaml
sleep 20

# 5. Сброс
./reset.sh
