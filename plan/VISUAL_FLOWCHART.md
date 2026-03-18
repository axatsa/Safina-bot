# 🔄 ВИЗУАЛЬНАЯ КАРТА ИСПРАВЛЕНИЯ

## ТЕКУЩЕЕ СОСТОЯНИЕ (СЛОМАНО)

```
┌─────────────────────────────────────────┐
│   GitLab CI Pipeline                    │
│                                         │
│  build-frontend:                        │
│    docker build ./frontend/frontend ❌   │
│         ↓                               │
│    Собирает ПУСТОЙ образ                │
│         ↓                               │
│    push в registry                      │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Сервер: thompson.uz                   │
│                                         │
│  docker-compose pull frontend ❌        │
│         ↓                               │
│    Скачивает битый образ                │
│         ↓                               │
│  docker-compose up frontend ❌          │
│         ↓                               │
│    Контейнер пытается запустить Python  │
│         ↓                               │
│    ПАДАЕТ → RESTARTING → ПАДАЕТ         │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Результат                             │
│                                         │
│   finance.thompson.uz → 404 ❌          │
└─────────────────────────────────────────┘
```

---

## ПОСЛЕ ИСПРАВЛЕНИЯ (РАБОТАЕТ)

```
┌─────────────────────────────────────────┐
│   GitLab CI Pipeline                    │
│                                         │
│  build-frontend:                        │
│    docker build ./frontend ✅            │
│         ↓                               │
│    Собирает ПРАВИЛЬНЫЙ образ с Nginx    │
│         ↓                               │
│    push в registry                      │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Сервер: thompson.uz                   │
│                                         │
│  docker-compose pull app ✅              │
│         ↓                               │
│    Скачивает рабочий образ              │
│         ↓                               │
│  docker-compose up app ✅                │
│         ↓                               │
│    Контейнер запускает Nginx            │
│         ↓                               │
│    РАБОТАЕТ → UP → СТАБИЛЬНО            │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Результат                             │
│                                         │
│   finance.thompson.uz → Логин ✅        │
└─────────────────────────────────────────┘
```

---

## АЛГОРИТМ ПРИНЯТИЯ РЕШЕНИЙ

```
START
  ↓
┌─────────────────────┐
│ Применить ПЛАН A    │
│ (исправить текущее) │
└──────────┬──────────┘
           ↓
    ┌──────────────┐
    │ GitLab CI OK?│
    └──────┬───────┘
           │
    ┌──────┴──────┐
    │             │
   ДА            НЕТ
    │             │
    ↓             ↓
┌──────────┐  ┌──────────────┐
│Проверить │  │Посмотреть    │
│контейнер │  │логи pipeline │
└────┬─────┘  └──────┬───────┘
     │               │
┌────┴────┐          ↓
│ UP?     │     ┌──────────┐
└────┬────┘     │Исправить │
     │          │ошибку    │
┌────┴────┐     └────┬─────┘
│         │          │
ДА       НЕТ         ↓
│         │      [Повтор]
↓         │
┌──────┐  │
│Сайт  │  ↓
│работ?│ ┌──────────┐
└──┬───┘ │ПЛАН B    │
   │     │(откат)   │
┌──┴──┐  └────┬─────┘
│     │       │
ДА   НЕТ      ↓
│     │   [Повтор проверок]
↓     │
SUCCESS│
        ↓
    ┌──────────┐
    │Экстренные│
    │меры      │
    └──────────┘
```

---

## ТРИ КЛЮЧЕВЫХ ИЗМЕНЕНИЯ

### 1. ПУТЬ СБОРКИ FRONTEND

```diff
# frontend/frontend/.gitlab-ci.yml

- docker build -t $FRONTEND_IMAGE ./frontend/frontend
+ docker build -t $FRONTEND_IMAGE ./frontend

Почему: ./frontend/frontend/ - это пустая папка
        ./frontend/ - там лежит весь код
```

### 2. ИМЯ СЕРВИСА В DEPLOY

```diff
# frontend/frontend/.gitlab-ci.yml

- docker-compose pull frontend
- docker-compose up -d frontend
+ docker-compose pull app
+ docker-compose up -d app

Почему: На сервере в docker-compose.yml сервис называется 'app'
```

### 3. КОНФЛИКТЫ СЛИЯНИЯ

```diff
# backend/.gitlab-ci.yml

- <<<<<<< HEAD
- некоторый код
- =======
- другой код
- >>>>>>> commit_hash
+ ОДИН правильный вариант кода

Почему: Git конфликты ломают YAML парсинг
```

---

## ВРЕМЕННАЯ ШКАЛА ИСПРАВЛЕНИЯ

```
T+0min  │ Применить изменения в файлах (5 мин)
        ↓
T+5min  │ git commit + push
        ↓
T+6min  │ GitLab CI автоматически запускается
        ↓
T+8min  │ build-frontend завершается (2-3 мин)
        ↓
T+10min │ deploy-frontend завершается (1-2 мин)
        ↓
T+11min │ Контейнер на сервере перезапускается
        ↓
T+12min │ Nginx стартует и сайт работает ✅
```

---

## КОНТРОЛЬНЫЕ ТОЧКИ ПРОВЕРКИ

### ✅ Checkpoint 1: Локальные изменения
```bash
git diff backend/.gitlab-ci.yml
# Должно показать: удаление конфликтов
```

### ✅ Checkpoint 2: GitLab CI
```
Pipeline: 🟢 build-frontend
Pipeline: 🟢 deploy-frontend
```

### ✅ Checkpoint 3: Сервер
```bash
docker-compose ps
# finance-frontend-main ... Up
```

### ✅ Checkpoint 4: Логи
```bash
docker-compose logs app
# nginx ... start worker processes
```

### ✅ Checkpoint 5: Сайт
```
https://finance.thompson.uz → 200 OK
```

---

## ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК

### Проблема: GitLab CI красный
```
Действие:
1. Кликнуть на красный job
2. Прочитать последние 20 строк
3. Если ошибка пути → проверить ШАГ 2.2
4. Если ошибка auth → проверить GitLab variables
```

### Проблема: Контейнер Restarting
```
Действие:
1. ssh на сервер
2. docker-compose logs app --tail=100
3. Найти строку с ошибкой
4. Если "ModuleNotFoundError" → ПЛАН B
5. Если "port already in use" → перезапустить
```

### Проблема: Сайт 404 но контейнер Up
```
Действие:
1. Проверить docker-compose.yml на сервере
2. Проверить traefik labels
3. curl http://localhost внутри контейнера
4. Если localhost работает → проблема в traefik
```
