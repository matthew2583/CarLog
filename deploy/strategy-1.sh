#!/usr/bin/bash
set -e

# 1. Накатываем v2
helm upgrade carlog ../helm/carlog -n carlog --reuse-values -f strategies/rolling/02-app-v2.yaml
kubectl rollout status deploy/backend -n carlog
sleep 15

# 2. Откат обратно на v1
kubectl rollout undo deploy/backend -n carlog
kubectl rollout status deploy/backend -n carlog
sleep 10

# 3. Сброс
./reset.sh
