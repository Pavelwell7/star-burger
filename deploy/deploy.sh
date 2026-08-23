#!/bin/bash
set -e

cd /opt/star-burger

echo "Обновляем код репозитория..."
git pull

cd deploy

echo "Собираем образ фронтенда..."
docker compose --env-file .env build frontend

echo "Собираем бандлы Parcel..."
docker compose --env-file .env run --rm frontend

echo "Собираем образ бэкенда "
docker compose --env-file .env build backend

echo "Копируем собранную статику Django из образа в общую папку..."
mkdir -p ../frontend_dist/staticfiles
docker compose --env-file .env run --rm --no-deps \
  -v "$(pwd)/../frontend_dist/staticfiles:/mnt/staticfiles" \
  backend sh -c "cp -r /app/staticfiles/. /mnt/staticfiles/"

echo "Перезапускаем контейнеры..."
docker compose --env-file .env up -d

echo "Уведомляем Rollbar о деплое..."
ROLLBAR_ACCESS_TOKEN=$(grep ROLLBAR_ACCESS_TOKEN .env | cut -d '=' -f2)
COMMIT_HASH=$(git -C .. rev-parse HEAD)

curl -s https://api.rollbar.com/api/1/deploy/ \
  -F access_token="$ROLLBAR_ACCESS_TOKEN" \
  -F environment=production \
  -F revision="$COMMIT_HASH" \
  -F local_username="$(whoami)"

echo ""
echo "Деплой успешно завершён!"
echo "Не забыть применить миграции вручную, если модели менялись:"
echo "  docker compose --env-file .env exec backend python manage.py migrate"
