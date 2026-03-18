# Техническое задание: Исправление белого экрана при 401 ошибках

## 📋 Описание проблемы

### Симптомы:
- После успешного входа в систему (safina/admin123) и обновления страницы (F5) появляется белый экран
- Белый экран сохраняется даже при:
  - Смене браузера
  - Жестком обновлении (Ctrl+F5)
  - Перезагрузке компьютера
  - Использовании режима инкогнито
- После первого входа можно работать, но после refresh — всё висит

### Когда происходит:
1. Пользователь логинится → всё работает
2. Делает refresh страницы (F5)
3. Появляется белый экран навсегда

---

## 🔍 Диагностика проблемы

### Корневая причина:
**Race condition при обработке множественных 401 Unauthorized ответов**

### Технические детали:

1. **Проблема в api-client.ts:**
   ```typescript
   if (response.status === 401) {
     localStorage.removeItem("safina_token");
     localStorage.removeItem("safina_role");
     localStorage.removeItem("safina_user");
     localStorage.removeItem("safina_projectId");
     window.location.href = "/";
     return response; // ⚠️ КОД ПРОДОЛЖАЕТСЯ ПОСЛЕ РЕДИРЕКТА!
   }
   ```
   - После `window.location.href = "/"` код **не останавливается**
   - React Query пытается обработать response, получает ошибку
   - Возникает исключение, которое не обрабатывается

2. **React Query запускает несколько запросов параллельно:**
   - При загрузке Applications.tsx делается 3 запроса:
     - `getExpenses()` - основной
     - `getProjects()` - список проектов
     - `getTeam()` - команда
   - Все получают 401 одновременно
   - Каждый пытается очистить localStorage и сделать redirect
   - Возникает бесконечный цикл редиректов

3. **Отсутствие обработки ошибок в React Query:**
   - Нет глобального error handler
   - "Unauthorized" ошибки не обрабатываются
   - ErrorBoundary не ловит эти ошибки, т.к. они async

---

## ✅ Решение

### Стратегия:
1. Предотвратить множественные редиректы через `sessionStorage`
2. Останавливать выполнение кода после 401 через `throw Error`
3. Добавить глобальный error handler в React Query
4. Очищать флаг редиректа при успешном логине

---

## 📝 Изменения в коде

### Файл 1: `/frontend/src/lib/api-client.ts`

**ЧТО МЕНЯЕМ:** Обработку 401 ошибок

**БЫЛО:**
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

**СТАЛО:**
```typescript
if (response.status === 401) {
  // Предотвращаем множественные редиректы от параллельных запросов
  const isAlreadyRedirecting = sessionStorage.getItem('redirecting');
  if (!isAlreadyRedirecting) {
    sessionStorage.setItem('redirecting', 'true');
    localStorage.removeItem("safina_token");
    localStorage.removeItem("safina_role");
    localStorage.removeItem("safina_user");
    localStorage.removeItem("safina_projectId");
    window.location.href = "/";
  }
  // Останавливаем дальнейшее выполнение
  throw new Error("Unauthorized");
}
```

**ПОЧЕМУ:**
- `sessionStorage.getItem('redirecting')` - проверяем, не делаем ли уже редирект
- `sessionStorage.setItem('redirecting', 'true')` - ставим флаг
- `throw new Error("Unauthorized")` - **КРИТИЧНО!** Останавливаем код, чтобы он не пытался парсить response

---

### Файл 2: `/frontend/src/pages/Login.tsx`

**ЧТО МЕНЯЕМ:** Добавляем очистку флага при успешном логине

**БЫЛО:**
```typescript
const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault();
  setIsLoading(true);

  const success = await store.login(login, password);

  setIsLoading(false);
  if (success) {
    toast.success("Вход выполнен");
    navigate("/dashboard");
  } else {
    toast.error("Неверный логин или пароль");
  }
};
```

**СТАЛО:**
```typescript
const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault();
  setIsLoading(true);

  const success = await store.login(login, password);

  setIsLoading(false);
  if (success) {
    // Очищаем флаг, чтобы разрешить будущие редиректы при 401
    sessionStorage.removeItem('redirecting');
    toast.success("Вход выполнен");
    navigate("/dashboard");
  } else {
    toast.error("Неверный логин или пароль");
  }
};
```

**ПОЧЕМУ:**
- После успешного логина нужно сбросить флаг `redirecting`
- Иначе при следующей 401 ошибке редирект не сработает

---

### Файл 3: `/frontend/src/App.tsx`

**ЧТО МЕНЯЕМ:** Добавляем глобальный error handler для React Query

**БЫЛО:**
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

**СТАЛО:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
      onError: (error: any) => {
        // Если это Unauthorized ошибка, она уже обработана в api-client.ts
        if (error?.message === 'Unauthorized') {
          return;
        }
        // Логируем другие ошибки для отладки
        console.error('Query error:', error);
      },
    },
    mutations: {
      onError: (error: any) => {
        // Если это Unauthorized ошибка, она уже обработана в api-client.ts
        if (error?.message === 'Unauthorized') {
          return;
        }
        // Логируем другие ошибки для отладки
        console.error('Mutation error:', error);
      },
    },
  },
});
```

**ПОЧЕМУ:**
- React Query должен знать, как обрабатывать "Unauthorized" ошибки
- Без этого handler'а React Query может показывать error UI
- Логируем другие ошибки для debugging

---

## 🧪 План тестирования

### Тест 1: Нормальный флоу с refresh
```
1. Открыть браузер (обычный режим)
2. Зайти на http://thompson.uz (или localhost)
3. Войти: safina / admin123
4. Проверить, что открылась админка
5. Нажать F5 (refresh)
6. ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Страница нормально обновилась, всё работает
```

### Тест 2: Множественные refresh
```
1. Войти в систему
2. Быстро нажать F5 несколько раз подряд (5-10 раз)
3. ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Страница обновляется нормально, без зависаний
```

### Тест 3: Тест с истекшим токеном (симуляция 401)
```
1. Войти в систему
2. Открыть DevTools → Application → Local Storage
3. Удалить вручную "safina_token"
4. Обновить страницу (F5)
5. ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Редирект на страницу логина, без белого экрана
```

### Тест 4: Разные браузеры
```
1. Повторить Тест 1 в Chrome
2. Повторить Тест 1 в Firefox
3. Повторить Тест 1 в Edge
4. ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Везде работает одинаково
```

### Тест 5: Режим инкогнито
```
1. Открыть браузер в режиме инкогнито
2. Войти в систему
3. Нажать F5
4. ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Всё работает
```

### Тест 6: Тест после выхода и повторного входа
```
1. Войти в систему
2. Поработать (открыть несколько страниц)
3. Выйти (logout)
4. Войти снова
5. Нажать F5
6. ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Всё работает
```

---

## 🚀 Инструкция по применению

### Вариант 1: Через Git (рекомендуется)

```bash
# 1. Перейти в папку проекта
cd /path/to/Safina-bot

# 2. Убедиться, что нет незакоммиченных изменений
git status

# 3. Создать новую ветку для фикса
git checkout -b fix/white-screen-401

# 4. Применить изменения вручную (см. секцию "Изменения в коде")
# Или использовать патч, если он есть

# 5. Проверить изменения
git diff

# 6. Закоммитить
git add frontend/src/lib/api-client.ts
git add frontend/src/pages/Login.tsx
git add frontend/src/App.tsx
git commit -m "fix: resolve white screen issue on 401 responses

- Add sessionStorage flag to prevent multiple redirects
- Throw error after 401 to stop code execution
- Add global error handlers in React Query
- Clear redirect flag on successful login

Fixes white screen issue after page refresh"

# 7. Запушить в GitLab
git push origin fix/white-screen-401

# 8. Создать Merge Request в GitLab
```

### Вариант 2: Прямое редактирование (быстрый способ)

```bash
# 1. Подключиться к серверу по SSH
ssh your-user@thompson.uz

# 2. Перейти в папку проекта
cd /path/to/Safina-bot

# 3. Создать бэкап текущих файлов
cp frontend/src/lib/api-client.ts frontend/src/lib/api-client.ts.backup
cp frontend/src/pages/Login.tsx frontend/src/pages/Login.tsx.backup
cp frontend/src/App.tsx frontend/src/App.tsx.backup

# 4. Отредактировать файлы (используй nano или vim)
nano frontend/src/lib/api-client.ts
nano frontend/src/pages/Login.tsx
nano frontend/src/App.tsx

# 5. Пересобрать frontend
cd frontend
npm run build

# 6. Перезапустить контейнеры (если используешь Docker)
cd ..
docker-compose restart frontend

# 7. Проверить логи
docker-compose logs -f frontend
```

### Вариант 3: Локальная разработка и деплой

```bash
# 1. На локальном компьютере
cd C:\path\to\Safina-bot

# 2. Применить изменения из секции "Изменения в коде"

# 3. Протестировать локально
cd frontend
npm run dev

# 4. Открыть http://localhost:5173 и протестировать

# 5. Если всё работает - собрать production build
npm run build

# 6. Закоммитить и запушить
git add .
git commit -m "fix: white screen on 401"
git push

# 7. На сервере сделать git pull
# (или подождать, пока GitLab CI/CD задеплоит автоматически)
```

---

## 🔍 Что проверить после деплоя

### Checklist:
- [ ] Вход в систему работает
- [ ] Refresh страницы (F5) не вызывает белый экран
- [ ] При неверном токене происходит редирект на логин
- [ ] Нет ошибок в консоли браузера (F12 → Console)
- [ ] Нет бесконечных редиректов
- [ ] В консоли не появляются error'ы типа "Unauthorized"
- [ ] После logout и повторного login всё работает
- [ ] В разных браузерах ведет себя одинаково

### Где смотреть ошибки:

1. **Браузер (DevTools):**
   ```
   F12 → Console
   Искать: красные ошибки, warnings
   ```

2. **Network tab:**
   ```
   F12 → Network
   Проверить: 401 ответы не создают loop
   ```

3. **Application/Storage:**
   ```
   F12 → Application → Local Storage
   Проверить: токены очищаются при 401
   
   F12 → Application → Session Storage
   Проверить: флаг 'redirecting' появляется при 401
   ```

4. **Backend логи:**
   ```bash
   docker-compose logs -f backend | grep "401\|Unauthorized"
   ```

---

## 📊 Метрики успеха

### До фикса:
- ❌ White screen rate: 100% после refresh
- ❌ User complaints: высокие
- ❌ Session stability: низкая

### После фикса:
- ✅ White screen rate: 0%
- ✅ User complaints: нет
- ✅ Session stability: высокая
- ✅ Refresh работает без проблем

---

## 🐛 Возможные проблемы и их решение

### Проблема 1: Белый экран всё ещё появляется
```
Причина: Браузер кэширует старый JavaScript
Решение:
1. Hard refresh: Ctrl+Shift+R (Windows) или Cmd+Shift+R (Mac)
2. Очистить кэш браузера
3. Проверить, что новый build задеплоен:
   - Посмотреть timestamp файлов в /frontend/dist
   - Проверить версию в package.json
```

### Проблема 2: Редирект не работает
```
Причина: sessionStorage не очищается
Решение:
1. Проверить, что в Login.tsx есть sessionStorage.removeItem('redirecting')
2. Вручную очистить sessionStorage в DevTools
```

### Проблема 3: Бесконечный редирект
```
Причина: Неправильная логика проверки токена
Решение:
1. Проверить логи backend на наличие 401 ошибок
2. Убедиться, что токен правильно сохраняется в localStorage
3. Проверить expiry time токена (в core/auth.py)
```

---

## 📚 Дополнительная информация

### Архитектура решения:
```
User Action (F5)
    ↓
React Router загружается
    ↓
AppLayout проверяет роль
    ↓
React Query делает запросы:
    - getExpenses()
    - getProjects()  
    - getTeam()
    ↓
api-client.ts обрабатывает ответы
    ↓
Если 401:
    1. Проверяет флаг 'redirecting'
    2. Если флага нет → очищает localStorage
    3. Ставит флаг 'redirecting'
    4. Делает redirect на "/"
    5. Бросает Error("Unauthorized")
    ↓
React Query ловит ошибку
    ↓
onError handler в App.tsx
    ↓
Если error.message === "Unauthorized":
    - Ничего не делает (уже обработано)
Иначе:
    - Логирует ошибку
    ↓
Redirect на login страницу
    ↓
User вводит логин/пароль
    ↓
Login успешен:
    - sessionStorage.removeItem('redirecting')
    - Разрешаем будущие 401 редиректы
```

### Техническая документация:
- React Query error handling: https://tanstack.com/query/latest/docs/react/guides/query-invalidation
- sessionStorage vs localStorage: https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage
- JWT token expiry: RFC 7519

---

## ✅ Критерии приёмки

Фикс считается успешным, если:

1. ✅ После refresh страницы не появляется белый экран
2. ✅ При истекшем токене происходит корректный редирект на login
3. ✅ Нет бесконечных редиректов при 401 ошибках
4. ✅ Несколько параллельных 401 запросов обрабатываются корректно
5. ✅ После logout и повторного login всё работает
6. ✅ Работает во всех браузерах (Chrome, Firefox, Edge)
7. ✅ Работает в режиме инкогнито
8. ✅ Нет ошибок в консоли браузера
9. ✅ Backend логи не показывают аномалий

---

## 👤 Ответственные

- **Разработчик:** Axat
- **Тестирование:** Axat
- **Деплой:** Axat
- **Код-ревью:** Требуется перед мержем в main

---

## 📅 Временные рамки

- Разработка: ✅ Выполнено
- Код-ревью: 15 минут
- Деплой на сервер: 30 минут
- Тестирование: 1 час
- **Итого:** ~2 часа

---

## 🎯 Приоритет

**КРИТИЧЕСКИЙ** - блокирует работу пользователей

---

*Документ создан: 2026-03-18*
*Версия: 1.0*
*Статус: Ready for Implementation*
