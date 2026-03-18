# ✅ Чек-лист проверки WHITE SCREEN FIX

## 📋 Перед применением фикса

- [ ] Создан backup текущих файлов
  ```bash
  cp frontend/src/lib/api-client.ts frontend/src/lib/api-client.ts.backup
  cp frontend/src/pages/Login.tsx frontend/src/pages/Login.tsx.backup
  cp frontend/src/App.tsx frontend/src/App.tsx.backup
  ```

- [ ] Проверено, что все 3 файла существуют
  ```bash
  ls -lh frontend/src/lib/api-client.ts
  ls -lh frontend/src/pages/Login.tsx
  ls -lh frontend/src/App.tsx
  ```

- [ ] Git статус чистый (или изменения закоммичены)
  ```bash
  git status
  ```

---

## 🔧 Проверка применения изменений

### Файл 1: api-client.ts

- [ ] Найдена строка: `if (response.status === 401) {`
- [ ] Добавлена проверка: `const isAlreadyRedirecting = sessionStorage.getItem('redirecting');`
- [ ] Добавлен if блок с `sessionStorage.setItem('redirecting', 'true');`
- [ ] Добавлена строка: `throw new Error("Unauthorized");`
- [ ] Удалена строка: `return response;`

**Проверка синтаксиса:**
```bash
cd frontend
npx tsc --noEmit src/lib/api-client.ts
```

### Файл 2: Login.tsx

- [ ] Найдена функция `handleLogin`
- [ ] Найден блок `if (success) {`
- [ ] Добавлена строка: `sessionStorage.removeItem('redirecting');`
- [ ] Строка добавлена ПЕРЕД `toast.success("Вход выполнен");`

**Проверка синтаксиса:**
```bash
cd frontend
npx tsc --noEmit src/pages/Login.tsx
```

### Файл 3: App.tsx

- [ ] Найден объект `queryClient`
- [ ] В `queries` добавлен `onError` handler
- [ ] В `mutations` добавлен `onError` handler
- [ ] Оба handler'а проверяют `error?.message === 'Unauthorized'`

**Проверка синтаксиса:**
```bash
cd frontend
npx tsc --noEmit src/App.tsx
```

---

## 🏗️ Сборка и деплой

- [ ] Frontend собирается без ошибок
  ```bash
  cd frontend
  npm run build
  ```

- [ ] Нет TypeScript ошибок
  ```bash
  npm run type-check
  # Или
  npx tsc --noEmit
  ```

- [ ] Размер bundle'а не сильно изменился
  ```bash
  ls -lh dist/assets/*.js
  ```

- [ ] Контейнеры перезапущены
  ```bash
  docker-compose restart frontend
  # Или
  docker-compose up -d --build frontend
  ```

- [ ] Логи не показывают ошибок
  ```bash
  docker-compose logs -f frontend | head -50
  ```

---

## 🧪 Функциональное тестирование

### Тест 1: Базовая функциональность
- [ ] Открыт сайт (http://thompson.uz или localhost)
- [ ] Страница логина отображается
- [ ] Логин работает (safina/admin123)
- [ ] Редирект на /dashboard происходит
- [ ] Данные загружаются

### Тест 2: Refresh страницы (ГЛАВНЫЙ ТЕСТ)
- [ ] Залогинен в систему
- [ ] Нажат F5 (обычный refresh)
- [ ] Страница обновляется БЕЗ белого экрана ✅
- [ ] Данные загружаются корректно
- [ ] Нет ошибок в консоли

### Тест 3: Множественные refresh
- [ ] Залогинен в систему
- [ ] Быстро нажат F5 несколько раз (5-10 раз)
- [ ] Ни разу не появился белый экран ✅
- [ ] Страница нормально обновляется

### Тест 4: Симуляция 401 (истекший токен)
- [ ] Залогинен в систему
- [ ] Открыт DevTools (F12)
- [ ] Application → Local Storage → удален "safina_token"
- [ ] Обновлена страница (F5)
- [ ] Произошел редирект на страницу логина ✅
- [ ] НЕ появился белый экран ✅
- [ ] Можно залогиниться снова

### Тест 5: Повторный вход после выхода
- [ ] Залогинен в систему
- [ ] Выполнен logout
- [ ] Выполнен login снова
- [ ] Нажат F5
- [ ] Всё работает нормально ✅

### Тест 6: Разные браузеры
- [ ] Протестировано в Chrome
- [ ] Протестировано в Firefox
- [ ] Протестировано в Edge
- [ ] Везде работает одинаково ✅

### Тест 7: Режим инкогнито
- [ ] Открыт браузер в режиме инкогнито
- [ ] Выполнен логин
- [ ] Нажат F5
- [ ] Работает нормально ✅

---

## 🔍 Проверка консоли браузера

### DevTools Console (F12 → Console)
- [ ] Нет красных ошибок
- [ ] Нет warnings о "Unauthorized"
- [ ] Нет ошибок типа "Cannot read property"
- [ ] Нет ошибок React Query

### DevTools Network (F12 → Network)
- [ ] При refresh идут нормальные запросы
- [ ] Запросы с 401 не создают loop
- [ ] После 401 происходит один redirect на "/"
- [ ] Нет бесконечных запросов

### DevTools Application (F12 → Application)

**Local Storage:**
- [ ] При успешном логине сохраняются:
  - `safina_token`
  - `safina_role`
  - `safina_user`
- [ ] При 401 всё очищается

**Session Storage:**
- [ ] При 401 появляется ключ `redirecting` = `"true"`
- [ ] После успешного логина ключ `redirecting` удаляется
- [ ] При нормальной работе ключа `redirecting` нет

---

## 📊 Проверка логов на сервере

### Backend логи
```bash
docker-compose logs -f backend | grep -E "401|Unauthorized|Login"
```

- [ ] При истекшем токене видны 401 ответы
- [ ] При успешном логине видна запись "User login successful"
- [ ] Нет массовых 401 ошибок (loop)

### Frontend логи
```bash
docker-compose logs -f frontend | tail -50
```

- [ ] Нет ошибок при сборке
- [ ] Нет runtime ошибок
- [ ] Nginx отдает файлы нормально

---

## 🎯 Финальная проверка

### Критерии успеха (ВСЕ должны быть выполнены):

✅ **Основная функциональность:**
- [ ] Логин работает
- [ ] Dashboard загружается
- [ ] Данные отображаются
- [ ] Навигация работает

✅ **Проблема решена:**
- [ ] Refresh (F5) НЕ вызывает белый экран
- [ ] Множественные refresh работают нормально
- [ ] При истекшем токене корректный redirect

✅ **Нет регрессий:**
- [ ] Logout работает
- [ ] Повторный login работает
- [ ] Все страницы открываются
- [ ] Все функции работают

✅ **Кроссбраузерность:**
- [ ] Работает в Chrome
- [ ] Работает в Firefox
- [ ] Работает в Edge
- [ ] Работает в инкогнито

✅ **Отсутствие ошибок:**
- [ ] Нет ошибок в консоли браузера
- [ ] Нет ошибок в логах сервера
- [ ] Нет warnings в DevTools

---

## 🚨 Если что-то не работает

### Rollback процедура:
```bash
# 1. Восстановить backup
cp frontend/src/lib/api-client.ts.backup frontend/src/lib/api-client.ts
cp frontend/src/pages/Login.tsx.backup frontend/src/pages/Login.tsx
cp frontend/src/App.tsx.backup frontend/src/App.tsx

# 2. Пересобрать
cd frontend && npm run build

# 3. Перезапустить
cd .. && docker-compose restart frontend

# 4. Проверить
curl http://localhost:5173  # или http://thompson.uz
```

### Диагностика:
```bash
# Проверить версию файлов
head -30 frontend/src/lib/api-client.ts | grep -A5 "401"

# Проверить build
ls -lh frontend/dist/assets/*.js

# Проверить логи
docker-compose logs --tail=100 frontend
```

---

## 📝 Заметки

**Дата применения:** _______________

**Кто применил:** _______________

**Результат тестирования:**
- [ ] Успешно
- [ ] Требуется доработка
- [ ] Откачено (rollback)

**Комментарии:**
_________________________________
_________________________________
_________________________________

---

## ✅ ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ

Я подтверждаю, что:
- Все чек-боксы отмечены
- Все тесты пройдены
- Белый экран больше не появляется
- Нет регрессий в функциональности
- Изменения задеплоены на production

**Подпись:** _______________
**Дата:** _______________

---

*Версия чек-листа: 1.0*
*Последнее обновление: 2026-03-18*
