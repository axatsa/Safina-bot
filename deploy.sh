#!/bin/bash
echo '🚀 Начинаем деплой Safina-bot (GitHub version)'

# 1. Переходим в папку с основным кодом
cd /home/finance/Safina-bot

# 2. Убеждаемся, что работаем с GitHub репозиторием
echo '📦 Проверка источника кода...'
git remote set-url origin https://github.com/axatsa/Safina-bot.git

# 3. Подтягиваем свежие изменения
echo '🔄 Загрузка кода из GitHub...'
git pull origin main

# 4. Собираем backend
echo '🔨 Сборка backend образа...'
docker build -t gitlab.thompson.uz:5050/finance/backend:main ./backend

# 5. Собираем frontend
echo '🔨 Сборка frontend образа (с очисткой кэша)...'
# Удаляем старые следы сборки, чтобы не было "белого экрана" из-за кэша
rm -rf ./frontend/dist
rm -rf ./frontend/node_modules/.vite

docker build --build-arg VITE_APP_API_URL=https://finance.thompson.uz/api -t gitlab.thompson.uz:5050/finance/frontend:main ./frontend

# 6. Перезапускаем контейнеры backend
echo '🔄 Перезапуск backend сервисов...'
cd /home/finance/backend/main
docker-compose down && docker-compose up -d app
echo '🛠 Применение миграций базы данных...'
docker-compose exec -T app python3 scripts/migrate_production.py

# 7. Перезапускаем контейнеры frontend
echo '🔄 Перезапуск frontend сервисов...'
cd /home/finance/frontend/main
docker-compose down && docker-compose up -d app

echo '✅ Деплой успешно завершен!'
echo '💡 Не забудьте нажать Ctrl+F5 в браузере для очистки кэша на вашей стороне.'
