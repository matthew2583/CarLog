#!/usr/bin/bash
set -e

# 1. Применяем v2 и маршрут Shadow
kubectl apply -f app/app-v2.yaml
kubectl rollout status deploy/backend-v2 -n carlog
kubectl apply -f strategies/shadow/httproute-shadow.yaml

# 2. Показываем логи v2 (копия зеркалируется)
sleep 5
echo "Логи backend-v2:"
kubectl logs -n carlog -l app=backend-v2 --tail=15

# 3. Сброс
./reset.sh
