#!/bin/bash
echo '🚀 Начинаем деплой Safina-bot (GitHub version)'

# 1. Переходим в папку с основным кодом
cd /home/finance/Safina-bot

# --- БЭКАП БАЗЫ ДАННЫХ ПЕРЕД ДЕПЛОЕМ ---
echo '💾 Создание резервной копии базы данных...'
mkdir -p ./backups
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

if docker ps | grep -q 'finance-db'; then
    # Пробуем подтянуть переменные из .env для корректного pg_dump
    if [ -f .env ]; then
        DB_USER_BACKUP=$(grep '^DB_USER=' .env | cut -d '=' -f2 | tr -d '\r')
        DB_NAME_BACKUP=$(grep '^DB_NAME=' .env | cut -d '=' -f2 | tr -d '\r')
    fi
    
    DB_USER_BACKUP=${DB_USER_BACKUP:-postgres}
    DB_NAME_BACKUP=${DB_NAME_BACKUP:-safina_db}

    echo "📦 Дамп БД $DB_NAME_BACKUP (пользователь $DB_USER_BACKUP)..."
    docker exec finance-db pg_dump -U $DB_USER_BACKUP $DB_NAME_BACKUP > ./backups/backup_${TIMESTAMP}.sql
    
    if [ ${PIPESTATUS[0]} -eq 0 ] && [ -s ./backups/backup_${TIMESTAMP}.sql ]; then
        echo "✅ Бэкап успешно создан: ./backups/backup_${TIMESTAMP}.sql"
        # Ротация: удаляем файлы старше 7 дней
        find ./backups -name "backup_*.sql" -mtime +7 -delete
    else
        echo "❌ Ошибка при создании бэкапа! Файл пуст или команда завершилась с ошибкой."
        # Если это критично, можно добавить exit 1 здесь, но обычно деплой важнее
    fi
else
    echo "⚠️ Контейнер finance-db не запущен, бэкап невозможен. Продолжаем без бэкапа..."
fi
# ---------------------------------------

# 2. Убеждаемся, что работаем с GitHub репозиторием
echo '📦 Проверка источника кода...'
git remote set-url origin https://github.com/axatsa/Safina-bot.git

# 3. Подтягиваем свежие изменения
echo '🔄 Загрузка кода из GitHub...'
git pull origin main

# 4. Собираем backend (--no-cache чтобы гарантировать свежие миграции)
echo '🔨 Сборка backend образа...'
docker build --no-cache -t gitlab.thompson.uz:5050/finance/backend:main ./backend

# 5. Собираем frontend
echo '🔨 Сборка frontend образа (с очисткой кэша)...'
# Удаляем старые следы сборки, чтобы не было "белого экрана" из-за кэша
rm -rf ./frontend/dist
rm -rf ./frontend/node_modules/.vite

docker build --no-cache --build-arg VITE_APP_API_URL=https://finance.thompson.uz/api -t gitlab.thompson.uz:5050/finance/frontend:main ./frontend

# 6. Перезапускаем все сервисы (backend + frontend + bot)
echo '🔄 Перезапуск всех сервисов Safina-bot...'
cd /home/finance/Safina-bot
docker-compose down && docker-compose up -d

# Ждём пока приложение полностью запустится (entrypoint применит миграции автоматически)
echo '⏳ Ожидание полного запуска backend...'
for i in $(seq 1 60); do
    if docker exec finance-backend-main python3 -c "
import os
from sqlalchemy import create_engine, text, inspect
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    tables = inspect(engine).get_table_names()
    assert 'users' in tables, 'users table not found'
    conn.execute(text('SELECT 1'))
print('OK')
" 2>/dev/null | grep -q 'OK'; then
        echo '✅ Backend запущен и миграции применены!'
        break
    fi
    if [ $i -eq 60 ]; then
        echo '❌ Backend не запустился за 60 секунд! Логи:'
        docker logs finance-backend-main --tail 30
        exit 1
    fi
    echo "  Попытка $i/60..."
    sleep 2
done

# Проверяем что bot_worker не упал
echo '⏳ Проверка статуса bot_worker...'
if docker ps | grep -q 'finance-bot-worker'; then
    echo '✅ Bot worker запущен и работает!'
else
    echo '⚠️ Внимание: finance-bot-worker возможно упал. Логи:'
    docker logs finance-bot-worker --tail 15
fi

# Запускаем скрипт создания admin-пользователя
echo '🛠 Создание/обновление admin пользователя...'
docker exec finance-backend-main python3 scripts/migrate_production.py

echo '✅ Деплой успешно завершен!'
echo '💡 Не забудьте нажать Ctrl+F5 в браузере для очистки кэша на вашей стороне.'
