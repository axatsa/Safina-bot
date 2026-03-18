# 📝 ПРАВИЛЬНОЕ СОДЕРЖИМОЕ ФАЙЛОВ

## ФАЙЛ 1: backend/.gitlab-ci.yml

**ПОЛНОСТЬЮ ЗАМЕНИТЬ СОДЕРЖИМОЕ НА:**

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

---

## ФАЙЛ 2: frontend/frontend/.gitlab-ci.yml

**ИЗМЕНЕНИЯ:**

### Строка 18 (в секции build-frontend):

**Было:**
```yaml
    - docker build -t $FRONTEND_IMAGE ./frontend/frontend
```

**Стало:**
```yaml
    - docker build -t $FRONTEND_IMAGE ./frontend
```

### Строки 40-41 (в секции deploy-frontend):

**Было:**
```yaml
        docker-compose pull frontend &&
        docker-compose up -d frontend
```

**Стало:**
```yaml
        docker-compose pull app &&
        docker-compose up -d app
```

---

## ПОЛНАЯ ВЕРСИЯ frontend/frontend/.gitlab-ci.yml

**Если хочешь заменить весь файл целиком:**

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
    - docker build -t $FRONTEND_IMAGE ./frontend
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
        docker-compose up -d app
      "
  only:
    - main
  dependencies:
    - build-frontend
  tags:
    - docker
```
