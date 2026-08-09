#!/bin/bash
set -e

cd /opt/star-burger

echo "Обновляем код репозитория..."
git pull

echo "Устанавливаем Python-зависимости..."
venv/bin/pip install -r requirements.txt --no-input

echo "Устанавливаем Node.js-зависимости..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 16.16.0
npm ci --dev

echo "Пересобираем JS-код..."
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

echo "Пересобираем статику Django..."
venv/bin/python manage.py collectstatic --noinput

echo "Накатываем миграции..."
venv/bin/python manage.py migrate --noinput

echo "Перезапускаем Gunicorn..."
systemctl restart star-burger

echo " Done!"
