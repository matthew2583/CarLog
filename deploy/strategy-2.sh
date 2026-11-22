#!/usr/bin/bash
set -e

# 1. Поднимаем v2 рядом с v1
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog
kubectl apply -f strategies/blue-green/httproute-green.yaml
sleep 10

# 2. Мгновенно переключаем 100% трафика на Blue (v2)
kubectl apply -f strategies/blue-green/httproute-blue.yaml
sleep 15

# 3. Мгновенный откат обратно на Green (v1)
kubectl apply -f strategies/blue-green/httproute-green.yaml
sleep 10

# 4. Сброс
./reset.sh
