# 🚨 ПОДРОБНЫЙ ПЛАН ИСПРАВЛЕНИЯ SAFINA-BOT 404 ОШИБКИ

Репозиторий: https://github.com/axatsa/Safina-bot

## 📋 ТЕКУЩАЯ ПРОБЛЕМА

**Симптом:** Сайт finance.thompson.uz возвращает 404
**Причина:** Frontend контейнер постоянно перезапускается из-за неправильного пути сборки в GitLab CI
**Диагноз:** GitLab CI пытается собрать образ из `./frontend/frontend/`, но код в `./frontend/`

---

# 🎯 ПЛАН A: ИСПРАВЛЕНИЕ ТЕКУЩЕЙ ВЕРСИИ (РЕКОМЕНДУЕТСЯ)

## ШАГ 1: Подготовка рабочей среды

### 1.1 Клонировать репозиторий (если еще не сделано)
```bash
cd ~
git clone https://github.com/axatsa/Safina-bot.git
cd Safina-bot
```

### 1.2 Проверить текущую ветку и статус
```bash
git branch
git status
```

**Ожидаемый результат:**
```
* main
On branch main
```

---

## ШАГ 2: Применение исправлений

### 2.1 Создать резервную ветку (на всякий случай)
```bash
git checkout -b backup-before-fix
git checkout main
```

### 2.2 Применить исправления вручную

#### ФАЙЛ 1: `backend/.gitlab-ci.yml`

**Открыть файл:**
```bash
nano backend/.gitlab-ci.yml
```

**Найти и удалить ВСЕ строки с конфликтами:**
- Удалить все строки содержащие `<<<<<<< HEAD`
- Удалить все строки содержащие `=======`
- Удалить все строки содержащие `>>>>>>> f665100`

**Полностью заменить содержимое файла на:**

```yaml
stages:
  - 🔨 build
  - 🧪 test  
  - 🚀 deploy

variables:
  BACKEND_IMAGE: $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_REF_NAME
  DOCKER_DRIVER: overlay2

# ========================================
# BUILD STAGE - Build & Push Docker Image
# ========================================
build-backend:
  stage: 🔨 build
  image: docker:24-dind
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - echo "Building backend image..."
    - docker build -t $BACKEND_IMAGE ./backend
    - echo "Pushing backend image to registry..."
    - docker push $BACKEND_IMAGE
  only:
    - main
  tags:
    - docker

# ========================================
# DEPLOY STAGE - Deploy to Server
# ========================================
deploy-backend:
  stage: 🚀 deploy
  image: alpine:3.20
  before_script:
    - apk add --no-cache openssh-client
    - mkdir -p ~/.ssh
    - echo "$SSH_KEY" | tr -d '\r' > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh-keyscan -H "$SSH_HOST" >> ~/.ssh/known_hosts
  script:
    - |
      ssh -o StrictHostKeyChecking=no -p $SSH_PORT $SSH_USER@$SSH_HOST "
        cd /home/finance/backend/main &&
        docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY &&
        docker-compose pull app &&
        docker-compose up -d app
      "
  only:
    - main
  dependencies:
    - build-backend
  tags:
    - docker
```

**Сохранить и выйти:**
- Ctrl+O (сохранить)
- Enter
- Ctrl+X (выйти)

---

#### ФАЙЛ 2: `frontend/frontend/.gitlab-ci.yml`

**Открыть файл:**
```bash
nano frontend/frontend/.gitlab-ci.yml
```

**Найти строку 18 (примерно):**
```yaml
    - docker build -t $FRONTEND_IMAGE ./frontend/frontend
```

**Заменить на:**
```yaml
    - docker build -t $FRONTEND_IMAGE ./frontend
```

**Найти строки 40-41 (примерно):**
```yaml
        docker-compose pull frontend &&
        docker-compose up -d frontend
```

**Заменить на:**
```yaml
        docker-compose pull app &&
        docker-compose up -d app
```

**Сохранить и выйти:**
- Ctrl+O, Enter, Ctrl+X

---

### 2.3 Проверить изменения

```bash
git diff backend/.gitlab-ci.yml
git diff frontend/frontend/.gitlab-ci.yml
```

**Убедиться что:**
- ✅ Нет строк с `<<<<<<< HEAD`
- ✅ В frontend: путь `./frontend` (НЕ `./frontend/frontend`)
- ✅ В deploy: команды используют `app` (НЕ `backend` или `frontend`)

---

## ШАГ 3: Коммит и пуш изменений

### 3.1 Добавить файлы в staging
```bash
git add backend/.gitlab-ci.yml
git add frontend/frontend/.gitlab-ci.yml
```

### 3.2 Проверить что добавлено
```bash
git status
```

**Ожидаемый результат:**
```
Changes to be committed:
  modified:   backend/.gitlab-ci.yml
  modified:   frontend/frontend/.gitlab-ci.yml
```

### 3.3 Создать коммит
```bash
git commit -m "Fix: Resolve git conflicts and correct GitLab CI paths

- Resolved all merge conflicts in backend/.gitlab-ci.yml
- Fixed frontend build path: ./frontend/frontend → ./frontend
- Fixed deploy commands to use 'app' service name
- This fixes 404 error caused by frontend container restarting"
```

### 3.4 Запушить в GitHub
```bash
git push origin main
```

**ВАЖНО:** Введи свои учетные данные GitHub если попросит

---

## ШАГ 4: Ожидание и мониторинг GitLab CI

### 4.1 Открыть GitLab CI
1. Открой браузер
2. Перейди на: `https://gitlab.thompson.uz/finance/finance`
3. Слева: CI/CD → Pipelines

### 4.2 Отследить пайплайн

**Ожидаемая последовательность:**
1. ⏳ Pipeline запустится автоматически (через 10-30 секунд после пуша)
2. 🔨 build-frontend (зеленый) ← должен собрать образ успешно
3. 🔨 build-backend (зеленый)
4. 🚀 deploy-frontend (зеленый) ← должен задеплоить на сервер
5. 🚀 deploy-backend (зеленый)

**Время выполнения:** 3-5 минут

### 4.3 Если пайплайн зеленый - переходи к ШАГ 5

### 4.4 Если пайплайн красный:

**Кликни на красный job → посмотри логи → скопируй последние 20 строк**

Возможные ошибки:
- **"authentication required"** → проблема с GitLab registry credentials
- **"no such file or directory"** → проблема с путями (вернись к ШАГ 2.2)
- **"connection refused"** → проблема с SSH доступом к серверу

---

## ШАГ 5: Проверка на сервере

### 5.1 Подключиться к серверу
```bash
ssh finance@thompson.uz -p 2222
```

**Введи пароль сервера**

### 5.2 Проверить frontend контейнер
```bash
cd /home/finance/frontend/main
docker-compose ps
```

**Ожидаемый результат (ПРАВИЛЬНО):**
```
        Name                     Command               State      Ports
-------------------------------------------------------------------------
finance-frontend-main   /docker-entrypoint.sh ngin ...   Up      80/tcp
```

**НЕ ДОЛЖНО БЫТЬ (НЕПРАВИЛЬНО):**
```
finance-frontend-main   uvicorn main:app ...   Restarting
```

### 5.3 Проверить логи frontend
```bash
docker-compose logs app --tail=50
```

**Ожидаемый вывод (фрагменты):**
```
nginx: [notice] start worker processes
server listening on 0.0.0.0:80
```

**НЕ ДОЛЖНО БЫТЬ:**
```
uvicorn
python
ModuleNotFoundError
```

### 5.4 Проверить backend контейнер
```bash
cd /home/finance/backend/main
docker-compose ps
```

**Ожидаемый результат:**
```
        Name                      Command               State    Ports
------------------------------------------------------------------------
finance-backend-main   uvicorn main:app --host 0. ...   Up      8000/tcp
```

### 5.5 Выйти с сервера
```bash
exit
```

---

## ШАГ 6: Проверка сайта

### 6.1 Открыть сайт в браузере

**URL:** https://finance.thompson.uz

### 6.2 Ожидаемый результат

✅ **УСПЕХ:** Страница логина загружается (форма логина, без 404)

❌ **ПРОБЛЕМА:** Все еще 404

### 6.3 Проверка в DevTools (F12)

**Открыть консоль:**
1. Нажми F12
2. Перейди на вкладку Console

**Ожидаемый результат (если работает):**
- Нет красных ошибок 404
- Может быть пару предупреждений (желтые) - это нормально

**Если видишь ошибки:**
- Скопируй все красные ошибки
- Переходи к ПЛАНУ B

---

# 🎯 ПЛАН B: ОТКАТ НА ПОСЛЕДНЮЮ РАБОЧУЮ ВЕРСИЮ

**Используй ТОЛЬКО если ПЛАН A не помог**

## ШАГ 1: Подготовка к откату

### 1.1 Определить последний рабочий коммит

**Запустить на локальной машине:**
```bash
cd ~/Safina-bot
git log --oneline -30
```

**Найти коммит ПЕРЕД рефакторингом:**
```
4b1aea2 Critical Fixes: RBAC for Safina, SSE Stability, CI Redirections, and Crash Prevention
```

### 1.2 Создать новую ветку для отката
```bash
git checkout -b rollback-to-working
```

---

## ШАГ 2: Откат кода

### 2.1 Откатить файлы на коммит 4b1aea2

```bash
git checkout 4b1aea2 -- .
```

**Эта команда:**
- Возвращает ВСЕ файлы на состояние коммита 4b1aea2
- НЕ удаляет новые файлы (они останутся)
- Сохраняет .git историю

### 2.2 Проверить что откатилось
```bash
git status
```

**Должно показать много измененных файлов**

---

## ШАГ 3: Адаптация CI/CD для сервера

### 3.1 Проблема с откатом

**Коммит 4b1aea2 использовал внешние CI шаблоны:**
```yaml
include:
  - project: base/ci-cd
    file: frontend.yml
```

**Эти шаблоны могут не работать.**

### 3.2 Создать standalone CI конфиг для frontend

**Создать файл:**
```bash
nano frontend/frontend/.gitlab-ci.yml
```

**Вставить содержимое:**
```yaml
stages:
  - 🔨 build
  - 🚀 deploy

variables:
  FRONTEND_IMAGE: $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_REF_NAME
  DOCKER_DRIVER: overlay2

build-frontend:
  stage: 🔨 build
  image: docker:24-dind
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - echo "Building frontend image..."
    - cd frontend/frontend
    - docker build -t $FRONTEND_IMAGE .
    - echo "Pushing frontend image to registry..."
    - docker push $FRONTEND_IMAGE
  only:
    - main
  tags:
    - docker

deploy-frontend:
  stage: 🚀 deploy
  image: alpine:3.20
  before_script:
    - apk add --no-cache openssh-client
    - mkdir -p ~/.ssh
    - echo "$SSH_KEY" | tr -d '\r' > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh-keyscan -H "$SSH_HOST" >> ~/.ssh/known_hosts
  script:
    - |
      ssh -o StrictHostKeyChecking=no -p $SSH_PORT $SSH_USER@$SSH_HOST "
        cd /home/finance/frontend/main &&
        docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY &&
        docker-compose pull app &&
        docker-compose down &&
        docker-compose up -d app
      "
  only:
    - main
  dependencies:
    - build-frontend
  tags:
    - docker
```

**Сохранить: Ctrl+O, Enter, Ctrl+X**

### 3.3 Создать standalone CI конфиг для backend

**Создать файл:**
```bash
nano backend/.gitlab-ci.yml
```

**Вставить содержимое:**
```yaml
stages:
  - 🔨 build
  - 🚀 deploy

variables:
  BACKEND_IMAGE: $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_REF_NAME
  DOCKER_DRIVER: overlay2

build-backend:
  stage: 🔨 build
  image: docker:24-dind
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - echo "Building backend image..."
    - cd backend
    - docker build -t $BACKEND_IMAGE .
    - echo "Pushing backend image to registry..."
    - docker push $BACKEND_IMAGE
  only:
    - main
  tags:
    - docker

deploy-backend:
  stage: 🚀 deploy
  image: alpine:3.20
  before_script:
    - apk add --no-cache openssh-client
    - mkdir -p ~/.ssh
    - echo "$SSH_KEY" | tr -d '\r' > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh-keyscan -H "$SSH_HOST" >> ~/.ssh/known_hosts
  script:
    - |
      ssh -o StrictHostKeyChecking=no -p $SSH_PORT $SSH_USER@$SSH_HOST "
        cd /home/finance/backend/main &&
        docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY &&
        docker-compose pull app &&
        docker-compose down &&
        docker-compose up -d app &&
        sleep 5 &&
        docker-compose exec -T app alembic upgrade head
      "
  only:
    - main
  dependencies:
    - build-backend
  tags:
    - docker
```

**Сохранить: Ctrl+O, Enter, Ctrl+X**

---

## ШАГ 4: Коммит и пуш отката

### 4.1 Добавить все изменения
```bash
git add -A
```

### 4.2 Создать коммит
```bash
git commit -m "Rollback: Return to working version (4b1aea2) with updated CI/CD configs"
```

### 4.3 Запушить в новую ветку
```bash
git push origin rollback-to-working
```

### 4.4 Создать Pull Request на GitHub

1. Открой https://github.com/axatsa/Safina-bot
2. Кликни "Compare & pull request"
3. Выбери: `rollback-to-working` → `main`
4. Напиши: "Rollback to last working version"
5. Кликни "Create pull request"
6. Кликни "Merge pull request"

### 4.5 Подождать GitLab CI (3-5 минут)

### 4.6 Проверить сайт (как в ПЛАНЕ A, ШАГ 6)

---

# 📋 ФИНАЛЬНАЯ ПРОВЕРКА

## Чек-лист успеха

После ПЛАНА A или ПЛАНА B, выполни:

### ✅ Контейнеры
- [ ] Frontend контейнер в статусе `Up` (НЕ `Restarting`)
- [ ] Backend контейнер в статусе `Up`
- [ ] В логах frontend видно `nginx` (НЕ `uvicorn`)

### ✅ Сайт
- [ ] https://finance.thompson.uz открывается
- [ ] Видна страница логина (НЕ 404)
- [ ] Нет красных ошибок в Console (F12)

### ✅ API
- [ ] Можно залогиниться (если есть учетка)
- [ ] После логина нет белого экрана

---

# 🆘 ЕСЛИ НИЧЕГО НЕ ПОМОГЛО

## Критический откат (последний резерв)

### Вариант 1: Ручной билд и деплой

```bash
# На локальной машине
cd ~/Safina-bot/frontend
docker build -t manual-frontend .
docker tag manual-frontend gitlab.thompson.uz:5050/finance/frontend:manual
docker push gitlab.thompson.uz:5050/finance/frontend:manual

# На сервере
ssh finance@thompson.uz -p 2222
cd /home/finance/frontend/main
nano .env
# Изменить: IMAGE_URL=gitlab.thompson.uz:5050/finance/frontend:manual
docker-compose pull app
docker-compose down
docker-compose up -d app
```

### Вариант 2: Временный локальный запуск

```bash
cd ~/Safina-bot/frontend
npm install
npm run dev
# Сайт будет на http://localhost:5173
```

---

# 📞 КОНТАКТЫ ДЛЯ ЭСКАЛАЦИИ

Если оба плана провалились:
1. Скопируй все логи контейнеров
2. Скопируй вывод `docker-compose ps`
3. Скопируй последние 50 строк GitLab CI pipeline
4. Обратись к тому кто настраивал сервер

---

# ⚡ БЫСТРЫЕ КОМАНДЫ (для копипаста)

```bash
# Проверка статуса контейнеров
ssh finance@thompson.uz -p 2222 "cd /home/finance/frontend/main && docker-compose ps && docker-compose logs app --tail=20"

# Полный перезапуск контейнеров
ssh finance@thompson.uz -p 2222 "cd /home/finance/frontend/main && docker-compose down && docker-compose up -d app"

# Просмотр логов в реальном времени
ssh finance@thompson.uz -p 2222 "cd /home/finance/frontend/main && docker-compose logs -f app"

# Проверка образов
ssh finance@thompson.uz -p 2222 "docker images | grep frontend"
```

---

**ВАЖНО:** Выполняй команды последовательно. Не пропускай шаги. Проверяй результат каждого шага.
