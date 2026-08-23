# Деплой Star Burger на сервер (Docker)

Прод-версия сайта работает через Docker Compose: PostgreSQL и Django (под Gunicorn) — в контейнерах, Nginx — на самом сервере, вне контейнеров.

## Первоначальная настройка сервера (один раз)

Понадобится Ubuntu-сервер с установленным Docker:

```sh
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y
```

Также нужны Nginx и Certbot на самом сервере (не в контейнере — Nginx общий для всех сайтов на машине):

```sh
apt install nginx certbot python3-certbot-nginx -y
```

Склонируйте репозиторий:
```sh
cd /opt
git clone git@github.com:Pavelwell7/star-burger.git
cd star-burger
```

Создайте `deploy/.env` со своими значениями:
```sh
SECRET_KEY=сгенерированный_секретный_ключ
YANDEX_GEOCODER_API_KEY=ваш_ключ
DEBUG=False
ALLOWED_HOSTS=ваш_IP,ваш_домен,127.0.0.1,localhost,backend
ROLLBAR_ACCESS_TOKEN=ваш_токен

POSTGRES_DB=starburger_db
POSTGRES_USER=starburger_user
POSTGRES_PASSWORD=надёжный_пароль_отличный_от_локального

DATABASE_URL=postgres://starburger_user:надёжный_пароль_отличный_от_локального@db:5432/starburger_db
```

Настройте Nginx (`/etc/nginx/sites-available/star-burger`):
```nginx
server {
    server_name ваш_IP ваш_домен;

    location /media/ {
        alias /opt/star-burger/media/;
    }
    location /static/ {
        alias /opt/star-burger/frontend_dist/staticfiles/;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
```sh
ln -s /etc/nginx/sites-available/star-burger /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
certbot --nginx -d ваш_домен
```

Сделайте деплойный скрипт исполняемым:
```sh
chmod +x deploy/deploy.sh
```

## Обновление кода (после каждого изменения)

Локально:
```sh
git add .
git commit -m "..."
git push
```

На сервере:
```sh
ssh ваш_сервер
cd /opt/star-burger
./deploy/deploy.sh
```

Скрипт сам:
1. Подтянет свежий код (`git pull`)
2. Соберёт образ фронтенда и запустит сборку бандлов Parcel
3. Соберёт образ бэкенда — внутри сборки образа выполняется `collectstatic`
4. Скопирует собранную статику из образа в `frontend_dist/staticfiles/` (её раздаёт Nginx)
5. Перезапустит контейнеры (`db`, `backend`)
6. Уведомит Rollbar о деплое с хэшем коммита

Если модели менялись — миграции применяются вручную, отдельной командой:
```sh
cd deploy
docker compose --env-file .env exec backend python manage.py migrate
```

## Полезные команды на сервере

Логи:
```sh
docker compose -f deploy/docker-compose.yaml --env-file deploy/.env logs -f backend
```

Статус контейнеров:
```sh
docker compose -f deploy/docker-compose.yaml --env-file deploy/.env ps
```

Зайти в контейнер бэкенда (например, для management-команд):
```sh
docker compose -f deploy/docker-compose.yaml --env-file deploy/.env exec backend bash
```
