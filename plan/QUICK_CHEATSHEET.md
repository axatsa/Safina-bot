# 🚀 БЫСТРАЯ ШПАРГАЛКА - SAFINA-BOT FIX

## ПЛАН A: Исправление (5 минут)

### 1. Исправить backend/.gitlab-ci.yml
```bash
nano backend/.gitlab-ci.yml
```
**Удалить все строки с:** `<<<<<<< HEAD`, `=======`, `>>>>>>>`
**Оставить только правильную версию с:** `docker build -t $BACKEND_IMAGE ./backend` и `docker-compose pull app`

### 2. Исправить frontend/frontend/.gitlab-ci.yml
```bash
nano frontend/frontend/.gitlab-ci.yml
```
**Строка 18:** `./frontend/frontend` → `./frontend`
**Строки 40-41:** `frontend` → `app`

### 3. Коммит и пуш
```bash
git add backend/.gitlab-ci.yml frontend/frontend/.gitlab-ci.yml
git commit -m "Fix: Resolve git conflicts and correct GitLab CI paths"
git push origin main
```

### 4. Проверка (через 5 минут)
```bash
# Статус контейнеров
ssh finance@thompson.uz -p 2222 "cd /home/finance/frontend/main && docker-compose ps"

# Должно быть: Up (НЕ Restarting)
# Должно быть: nginx (НЕ uvicorn)
```

---

## ПЛАН B: Откат (если ПЛАН A не помог)

```bash
# 1. Откат на рабочую версию
git checkout -b rollback-to-working
git checkout 4b1aea2 -- .

# 2. Создать новые CI конфиги (см. полный план)

# 3. Коммит и пуш
git add -A
git commit -m "Rollback to working version"
git push origin rollback-to-working

# 4. Merge на GitHub вручную
```

---

## КРИТИЧЕСКИЕ ПРОВЕРКИ

### ✅ Контейнер работает правильно:
```bash
ssh finance@thompson.uz -p 2222
cd /home/finance/frontend/main
docker-compose ps
# Вывод: finance-frontend-main ... Up 80/tcp
```

### ❌ Контейнер сломан:
```bash
docker-compose ps
# Вывод: finance-frontend-main ... Restarting
# ИЛИ: uvicorn main:app (это Python, а не Nginx!)
```

---

## ЭКСТРЕННЫЙ ПЕРЕЗАПУСК

```bash
ssh finance@thompson.uz -p 2222
cd /home/finance/frontend/main
docker-compose down
docker-compose pull app
docker-compose up -d app
docker-compose logs app --tail=50
```

---

## ПРОВЕРКА САЙТА

**URL:** https://finance.thompson.uz

**✅ Работает:** Видна страница логина
**❌ Не работает:** 404 page not found

**DevTools (F12):**
- Не должно быть красных 404 ошибок
- Желтые предупреждения - нормально
