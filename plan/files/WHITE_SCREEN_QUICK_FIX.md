# 🚀 QUICK FIX: Белый экран при refresh

## Проблема
После логина и refresh (F5) → белый экран навсегда

## Причина
Множественные 401 ответы создают race condition → код не останавливается после redirect

## Решение за 3 шага

### 1️⃣ Файл: `frontend/src/lib/api-client.ts`

Найди эти строки (21-27):
```typescript
if (response.status === 401) {
  localStorage.removeItem("safina_token");
  localStorage.removeItem("safina_role");
  localStorage.removeItem("safina_user");
  localStorage.removeItem("safina_projectId");
  window.location.href = "/";
  return response;
}
```

Замени на:
```typescript
if (response.status === 401) {
  const isAlreadyRedirecting = sessionStorage.getItem('redirecting');
  if (!isAlreadyRedirecting) {
    sessionStorage.setItem('redirecting', 'true');
    localStorage.removeItem("safina_token");
    localStorage.removeItem("safina_role");
    localStorage.removeItem("safina_user");
    localStorage.removeItem("safina_projectId");
    window.location.href = "/";
  }
  throw new Error("Unauthorized");
}
```

### 2️⃣ Файл: `frontend/src/pages/Login.tsx`

Найди функцию `handleLogin` (строки 16-29), в блоке `if (success)` добавь одну строку:

```typescript
if (success) {
  sessionStorage.removeItem('redirecting'); // ← ДОБАВЬ ЭТУ СТРОКУ
  toast.success("Вход выполнен");
  navigate("/dashboard");
}
```

### 3️⃣ Файл: `frontend/src/App.tsx`

Найди `queryClient` (строки 22-29):
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});
```

Замени на:
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
      onError: (error: any) => {
        if (error?.message === 'Unauthorized') {
          return;
        }
        console.error('Query error:', error);
      },
    },
    mutations: {
      onError: (error: any) => {
        if (error?.message === 'Unauthorized') {
          return;
        }
        console.error('Mutation error:', error);
      },
    },
  },
});
```

## Применение на сервере

```bash
# 1. SSH на сервер
ssh user@thompson.uz

# 2. Перейди в проект
cd /path/to/Safina-bot

# 3. Создай backup
cp frontend/src/lib/api-client.ts frontend/src/lib/api-client.ts.backup
cp frontend/src/pages/Login.tsx frontend/src/pages/Login.tsx.backup
cp frontend/src/App.tsx frontend/src/App.tsx.backup

# 4. Отредактируй файлы (nano или vim)
nano frontend/src/lib/api-client.ts
nano frontend/src/pages/Login.tsx
nano frontend/src/App.tsx

# 5. Пересобери
cd frontend && npm run build

# 6. Перезапусти
cd .. && docker-compose restart frontend
```

## Тестирование

```
1. Зайди на сайт
2. Логин: safina / admin123
3. Нажми F5 несколько раз
4. ✅ Должно работать без белого экрана
```

## Если не работает

```bash
# Очисти кэш браузера: Ctrl+Shift+R

# Проверь, что build обновился:
ls -lh frontend/dist/assets/*.js

# Проверь логи:
docker-compose logs -f frontend
```

## Rollback (если что-то пошло не так)

```bash
# Вернуть backup файлы
cp frontend/src/lib/api-client.ts.backup frontend/src/lib/api-client.ts
cp frontend/src/pages/Login.tsx.backup frontend/src/pages/Login.tsx
cp frontend/src/App.tsx.backup frontend/src/App.tsx

# Пересобрать
cd frontend && npm run build

# Перезапустить
cd .. && docker-compose restart frontend
```

---

**Время на фикс:** 10-15 минут
**Критичность:** Высокая
**Статус:** Готово к применению
