# Как применить патч white-screen-fix.patch

## Способ 1: Автоматическое применение через git apply

```bash
# 1. Перейди в корень проекта
cd /path/to/Safina-bot

# 2. Проверь статус (должен быть чистый)
git status

# 3. Примени патч
git apply white-screen-fix.patch

# 4. Проверь изменения
git diff

# 5. Если всё ок - закоммить
git add frontend/src/lib/api-client.ts frontend/src/pages/Login.tsx frontend/src/App.tsx
git commit -m "fix: resolve white screen issue on 401 responses"
```

## Способ 2: Применение через patch команду

```bash
# 1. Перейди в корень проекта
cd /path/to/Safina-bot

# 2. Примени патч
patch -p1 < white-screen-fix.patch

# 3. Проверь результат
git diff
```

## Способ 3: Ручное применение (самый надежный)

Просто открой файлы и внеси изменения вручную:
- Смотри WHITE_SCREEN_QUICK_FIX.md
- Или WHITE_SCREEN_FIX_TZ.md (раздел "Изменения в коде")

## После применения

```bash
# 1. Собери frontend
cd frontend
npm run build

# 2. Перезапусти контейнеры
cd ..
docker-compose restart frontend

# 3. Протестируй (открой сайт, залогинься, нажми F5)
```

## Проверка применения

```bash
# Проверь что изменения применились:
grep -A5 "isAlreadyRedirecting" frontend/src/lib/api-client.ts
grep "sessionStorage.removeItem" frontend/src/pages/Login.tsx
grep -A3 "onError:" frontend/src/App.tsx
```

## Если патч не применяется

Возможные причины:
1. Файлы уже изменены (конфликт)
2. Неправильная версия файлов
3. Патч устарел

Решение: Примени изменения вручную по WHITE_SCREEN_QUICK_FIX.md
