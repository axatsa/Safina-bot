# ТЗ: Исправление багов — Telegram-бот, БД и Админка

**Проект:** Thompson Finance / Safina Bot  
**Дата:** 22.03.2026  
**Приоритет:** 🔴 Критический / 🟡 Средний / 🟢 Низкий  
**Статус:** Требует исправления

---

## Содержание

1. [Подтверждённые баги из предыдущего аудита (не исправлены)](#1-подтверждённые-баги-из-предыдущего-аудита)
2. [Новые баги — БД и ORM](#2-новые-баги--бд-и-orm)
3. [Новые баги — Telegram-бот](#3-новые-баги--telegram-бот)
4. [Новые баги — Связь бот ↔ БД](#4-новые-баги--связь-бот--бд)
5. [Новые баги — Админка (Frontend ↔ Backend)](#5-новые-баги--админка-frontend--backend)
6. [Итоговая таблица](#6-итоговая-таблица)

---

## 1. Подтверждённые баги из предыдущего аудита

> Эти баги были выявлены ранее, но **не исправлены** в текущем коде.

---

### 🔴 БАГ-01: Двойной `db.commit()` в `generate_request_id`

**Файл:** `backend/app/db/crud.py`  
**Функция:** `generate_request_id`

**Проблема:**  
Функция вызывает `db.commit()` внутри себя, а затем `create_expense_request` вызывает ещё один `db.commit()`. Это приводит к состоянию гонки при параллельных запросах — два пользователя могут получить одинаковый `request_id`.

**Текущий код (неверно):**
```python
def generate_request_id(db: Session, project_code: str):
    counter_record = db.query(models.ProjectCounter).filter(...).with_for_update().first()
    if not counter_record:
        counter_record = models.ProjectCounter(project_code=project_code, counter=1)
        db.add(counter_record)
        next_val = 1
    else:
        counter_record.counter += 1
        next_val = counter_record.counter
    db.commit()       # ← ПРОБЛЕМА: преждевременный коммит
    db.refresh(counter_record)
    return f"{project_code}-{next_val}"
```

**Исправление:**
```python
def generate_request_id(db: Session, project_code: str):
    counter_record = db.query(models.ProjectCounter).filter(
        models.ProjectCounter.project_code == project_code
    ).with_for_update().first()
    
    if not counter_record:
        counter_record = models.ProjectCounter(project_code=project_code, counter=1)
        db.add(counter_record)
        next_val = 1
    else:
        counter_record.counter += 1
        next_val = counter_record.counter
    # Убрать db.commit() и db.refresh() — коммит делает вызывающая функция
    return f"{project_code}-{next_val}"
```

---

### 🔴 БАГ-02: `usd_rate` сохраняется для UZS-заявок

**Файл:** `backend/app/db/crud.py`  
**Функция:** `create_expense_request`

**Проблема:**  
Параметр `usd_rate` передаётся снаружи и сохраняется без проверки валюты. UZS-заявки получают курс USD, что искажает аналитику.

**Исправление:**
```python
db_expense = models.ExpenseRequest(
    ...
    usd_rate=usd_rate if currency == "USD" else None,
    ...
)
```

---

### 🔴 БАГ-03: Некорректные сессии БД в `notifications.py`

**Файл:** `backend/app/services/bot/notifications.py`  
**Функции:** `get_admin_chat_id`, `set_admin_chat_id`, `_get_chat_id_by_position`

**Проблема:**  
Используется `next(database.get_db())` — это вызывает генератор, но не закрывает сессию корректно. При высокой нагрузке приводит к утечке соединений с БД.

**Текущий код (неверно):**
```python
def get_admin_chat_id() -> int | None:
    with next(database.get_db()) as db:  # ← некорректно
        ...
```

**Исправление — все три функции:**
```python
def get_admin_chat_id() -> int | None:
    from app.core import database
    from app.db import models
    with database.database_session() as db:
        setting = db.query(models.Setting).filter(
            models.Setting.key == "admin_chat_id"
        ).first()
        if setting:
            return int(setting.value)
    return None

def set_admin_chat_id(chat_id: int) -> None:
    from app.core import database
    from app.db import models
    with database.database_session() as db:
        setting = db.query(models.Setting).filter(
            models.Setting.key == "admin_chat_id"
        ).first()
        if setting:
            setting.value = str(chat_id)
        else:
            db.add(models.Setting(key="admin_chat_id", value=str(chat_id)))

def _get_chat_id_by_position(position: str) -> list[int]:
    from app.core import database
    from app.db import models
    with database.database_session() as db:
        users = db.query(models.TeamMember).filter(
            models.TeamMember.position == position,
            models.TeamMember.telegram_chat_id.isnot(None),
        ).all()
        return [u.telegram_chat_id for u in users]
```

---

### 🔴 БАГ-04: `total_amount` не передаётся в `refund_blank_wizard.py`

**Файл:** `backend/app/services/bot/handlers/refund_blank_wizard.py`  
**Функция:** `handle_refund_final_submit`

**Проблема:**  
`total_amount` не передаётся в `ExpenseRequestCreate`. В результате сумма возврата не сохраняется в заявке — в БД будет `0` или `None`.

**Исправление:**
```python
# Добавить импорт в начале файла
from decimal import Decimal

# В handle_refund_final_submit:
expense_create = schemas.ExpenseRequestCreate(
    project_id=data.get("project_id"),
    purpose=f"Возврат: {data['client_name']}",
    items=[],
    currency="UZS",
    request_type="blank_refund",
    template_key="refund",
    total_amount=Decimal(str(data.get("amount", 0))),  # ← добавить
    refund_data=data
)
```

---

### 🔴 БАГ-05: `user_id` не сохраняется в FSM-стейт в `blank_wizard.py`

**Файл:** `backend/app/services/bot/handlers/blank_wizard.py`  
**Функции:** `start_blank_wizard`, `handle_project_selection`, `handle_final_submit`

**Проблема:**  
`user.id` не сохраняется в FSM-стейт при старте визарда. В `handle_final_submit` делается повторный lookup по `telegram_chat_id`, что ненадёжно (пользователь мог сменить аккаунт, или запись не найдётся после истечения сессии).

**Исправление в `start_blank_wizard`:**
```python
with database.database_session() as db:
    user = db.query(models.TeamMember).filter(
        models.TeamMember.telegram_chat_id == message.from_user.id
    ).first()
    if not user:
        user_not_found = True
    else:
        user_id = user.id  # ← сохранить до выхода из сессии
        user_templates = list(user.templates or [])
        for p in user.projects:
            projects_data.append({
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "templates": list(p.templates or [])
            })

# После блока with:
if not user_not_found:
    await state.update_data(user_id=user_id)  # ← записать в стейт
```

**Исправление в `handle_final_submit`:**
```python
async def handle_final_submit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")  # ← брать из стейта
    
    if not user_id:
        await message.answer("Ошибка: сессия устарела. Начните заново /start")
        await state.clear()
        return
    
    usd_rate = await currency_service.get_usd_rate()
    
    with database.database_session() as db:
        items_objs = [schemas.ExpenseItemSchema(**i) for i in data["items"]]
        expense_create = schemas.ExpenseRequestCreate(
            project_id=data.get("project_id"),
            purpose=data["purpose"],
            items=items_objs,
            currency=data["currency"],
            request_type="blank_refund" if data["template"] == "refund" else "blank",
            template_key=data["template"]
        )
        expense_req = crud.create_expense_request(
            db=db, expense=expense_create, user_id=user_id, usd_rate=usd_rate
        )
        expense_req_id = expense_req.id
        request_id = expense_req.request_id
```

---

## 2. Новые баги — БД и ORM

---

### 🔴 БАГ-06: `DetachedInstanceError` при отправке уведомлений после закрытия сессии

**Файл:** `backend/app/services/bot/notifications.py`  
**Функция:** `send_admin_notification`, `send_senior_notification`, `send_ceo_notification`

**Проблема:**  
Эти функции открывают сессию, загружают объект `expense`, закрывают сессию через `with database.database_session()`, а затем обращаются к атрибутам объекта (`expense.project_name`, `expense.created_by` и т.д.) за пределами блока `with`. SQLAlchemy "отвязывает" объект при закрытии сессии — любое обращение к lazy-loaded атрибуту вызовет `DetachedInstanceError`.

**Пример проблемного кода:**
```python
async def send_admin_notification(expense_id: str, admin_chat_id: int) -> None:
    with database.database_session() as db:
        expense = db.query(models.ExpenseRequest).filter(...).first()
        # ... формирование текста с expense.project_name, expense.created_by ...
        # Всё ОК пока мы внутри блока with
    # Здесь сессия уже закрыта
    await _send_message(admin_chat_id, text, ...)  # ← если text сформирован вне блока — ОК
                                                    # Но если формирование идёт после — DetachedInstanceError
```

**Исправление:** убедиться что весь текст сообщения и все атрибуты объекта `expense` читаются **внутри** блока `with`. Все переменные для отправки формируются до выхода из `with`.

```python
async def send_admin_notification(expense_id: str, admin_chat_id: int) -> None:
    from app.core import database
    from app.db import models

    with database.database_session() as db:
        expense = db.query(models.ExpenseRequest).filter(
            models.ExpenseRequest.id == expense_id
        ).first()
        if not expense:
            return

        # ← Всё читаем ВНУТРИ блока with
        project_name = expense.project_name or "—"
        project_code = expense.project_code or "—"
        created_by = expense.created_by
        purpose = expense.purpose
        request_id = expense.request_id
        total_amount = expense.total_amount
        currency = expense.currency
        usd_rate = expense.usd_rate
        expense_id_db = expense.id
        request_type = expense.request_type

    # Формируем текст и отправляем уже с локальными переменными
    text = (
        f"🔴 *Safina Expense Tracker*\n"
        f"🟢 {project_name} ({project_code})\n"
        ...
    )
    await _send_message(admin_chat_id, text, ...)
```

---

### 🟡 БАГ-07: N+1 запросы при загрузке проектов в `blank_wizard.py`

**Файл:** `backend/app/services/bot/handlers/blank_wizard.py`  
**Функция:** `start_blank_wizard`, `handle_project_selection`

**Проблема:**  
При обращении к `user.projects` внутри сессии SQLAlchemy делает lazy load — это 1 запрос. Затем при обращении к `p.templates` для каждого проекта делается ещё один запрос. При 10 проектах — 11 запросов вместо 1.

**Исправление:** использовать `joinedload`:
```python
from sqlalchemy.orm import joinedload

user = db.query(models.TeamMember).options(
    joinedload(models.TeamMember.projects)
).filter(
    models.TeamMember.telegram_chat_id == message.from_user.id
).first()
```

---

### 🟡 БАГ-08: Отсутствует проверка существования `project_id` в `crud.create_expense_request`

**Файл:** `backend/app/db/crud.py`  
**Функция:** `create_expense_request`

**Проблема:**  
Если `project_id` передан, но проект не найден — функция поднимает `ValueError("Project not found")`. Однако при `project_id=None` (бланк без проекта) код использует `req_prefix = "REF"` или `"REQ"` — это нормально. Но если `project_id` задан как пустая строка `""` (что может прийти из веб-формы), условие `if expense.project_id:` будет `False`, и проект не загрузится — `request_id` будет `REQ-N` вместо правильного кода.

**Исправление:**
```python
project_id = expense.project_id if expense.project_id else None

if project_id:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project not found: {project_id}")
    ...
else:
    project_id = None
    ...
```

---

### 🟡 БАГ-09: `database_session` не используется единообразно в боте

**Файл:** `backend/app/services/bot/handlers/*.py`

**Проблема:**  
Разные хендлеры используют разные способы открытия сессии:
- `with database.database_session() as db:` — правильно
- `with next(database.get_db()) as db:` — неправильно (утечка)
- `db = next(database.get_db())` без закрытия — критично

**Исправление:** Провести аудит всех хендлеров и заменить на единый паттерн `with database.database_session() as db:`.

Проверить файлы:
- `auth.py` — ✅ использует `database.database_session()`
- `decisions.py` — ✅ использует `database.database_session()`
- `notifications.py` — ❌ использует `next(database.get_db())`
- `ceo.py` — ✅ использует `database.database_session()`

---

### 🟢 БАГ-10: Отсутствует индекс для частых запросов по `telegram_chat_id`

**Файл:** `backend/app/db/models.py`

**Проблема:**  
Поле `telegram_chat_id` имеет `unique=True, index=True` — это правильно. Но при каждом сообщении в бот выполняется lookup `TeamMember.telegram_chat_id == tg_id`. При большом количестве пользователей индекс есть, но запрос не использует eager loading — загружаются связи через lazy load отдельными запросами.

**Рекомендация:** уже есть индекс, дополнительно кешировать `user_id` в FSM-стейте (см. БАГ-05).

---

## 3. Новые баги — Telegram-бот

---

### 🔴 БАГ-11: FSM-состояние не сбрасывается при ошибке в `expense_wizard.py`

**Файл:** `backend/app/services/bot/handlers/expense_wizard.py`  
**Функция:** `process_finish`

**Проблема:**  
При исключении в блоке `try` вызывается `await state.clear()`, но `state.clear()` стоит **после** блока try/except — это неправильная структура. При ошибке БД состояние **не сбрасывается**, и пользователь застревает в FSM.

**Текущий код:**
```python
try:
    with database.database_session() as db:
        ...
    admin_chat_id = get_admin_chat_id()
    if admin_chat_id:
        await send_admin_notification(expense_req_id, admin_chat_id)
    await message.answer(f"✅ Заявка {request_id} создана!", ...)
except Exception as e:
    logger.error(...)
    await message.answer(f"❌ Ошибка: {e}", ...)

await state.clear()  # ← вызывается в любом случае — ОК структурно
```

На самом деле `state.clear()` стоит после `try/except` и вызывается всегда — это правильно. **Но** если исключение возникает при `send_admin_notification` (вне `with db:`), то `expense_req_id` может быть `None` (если исключение в `with db:` блоке), и уведомление отправится с `None`.

**Исправление:**
```python
expense_req_id = None
request_id = None

try:
    with database.database_session() as db:
        ...
        expense_req_id = db_expense.id
        request_id = db_expense.request_id
    
    if admin_chat_id and expense_req_id:  # ← проверка на None
        await send_admin_notification(expense_req_id, admin_chat_id)
    
    await message.answer(f"✅ Заявка {request_id} создана!", ...)
except Exception as e:
    logger.error(f"Error creating expense via bot: {e}", exc_info=True)
    await message.answer(f"❌ Ошибка при создании заявки. Попробуйте снова.", ...)
finally:
    await state.clear()  # ← всегда сбрасываем через finally
```

---

### 🔴 БАГ-12: `refund_wizard.py` — `user_id` может быть `None` при создании возврата

**Файл:** `backend/app/services/bot/handlers/refund_wizard.py`  
**Функция:** `handle_refund_submit`

**Проблема:**  
`data["user_id"]` может отсутствовать, если пользователь начал диалог не через `/start` (например, нажал кнопку после перезапуска бота — FSM в MemoryStorage сбросился). В этом случае `user_id=None`, и `crud.create_expense_request` поднимет `ValueError("User not found")`.

**Исправление:**
```python
@router.callback_query(RefundWizard.confirm, F.data == "refund_submit")
async def handle_refund_submit(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    user_id = data.get("user_id")
    if not user_id:
        await callback.message.answer(
            "❌ Сессия устарела. Пожалуйста, начните заново: /start",
            reply_markup=get_main_kb()
        )
        await state.clear()
        await callback.answer()
        return
    
    # ... остальной код
```

---

### 🔴 БАГ-13: Бот падает если `BOT_TOKEN` не задан, но `bot` инстанс создаётся при импорте

**Файл:** `backend/app/services/bot/notifications.py`

**Проблема:**  
В начале файла создаётся глобальный инстанс бота:
```python
bot = Bot(token=os.getenv("BOT_TOKEN"))
```
Если `BOT_TOKEN` не задан в `.env` (например, при первом деплое или тестировании), `Bot(token=None)` вызовет исключение **при импорте модуля**. Это обрушит весь FastAPI-сервер при старте, даже если бот не нужен.

**Исправление:**
```python
_bot: Bot | None = None

def get_bot() -> Bot | None:
    global _bot
    token = os.getenv("BOT_TOKEN")
    if not token:
        return None
    if _bot is None:
        _bot = Bot(token=token)
    return _bot

async def _send_message(chat_id: int, text: str, reply_markup=None, parse_mode: str = "Markdown") -> None:
    bot = get_bot()
    if not bot:
        logger.warning(f"BOT_TOKEN not set, cannot send message to {chat_id}")
        return
    try:
        await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
```

---

### 🟡 БАГ-14: `blank_wizard.py` — FSM не переходит в `RefundBlankWizard` корректно при выборе шаблона `refund`

**Файл:** `backend/app/services/bot/handlers/blank_wizard.py`  
**Функция:** `handle_filling_method`

**Проблема:**  
При выборе шаблона `refund` и метода "📱 Заполнить в боте" состояние переключается на `RefundBlankWizard.client_name`, но FSM остаётся в контексте `BlankWizard`. Так как роутеры разные (`blank_wizard.router` и `refund_blank_wizard.router`), состояния `RefundBlankWizard` должны перехватываться вторым роутером — это работает, но `user_id` не передаётся в новый контекст.

**Исправление:** перед переключением состояния сохранить `user_id` и `project_id` в стейт:
```python
if message.text == "📱 Заполнить в боте":
    data = await state.get_data()
    if data.get("template") == "refund":
        # user_id уже должен быть в стейте из start_blank_wizard
        await state.set_state(RefundBlankWizard.client_name)
        await message.answer("ФИО клиента (родителя):", reply_markup=get_back_kb())
```

---

### 🟡 БАГ-15: `ceo.py` — повторная отправка уведомлений CEO при `handle_ceo_update`

**Файл:** `backend/app/services/bot/handlers/ceo.py`  
**Функция:** `handle_ceo_update`

**Проблема:**  
При нажатии "🔄 Проверить новые заявки" CEO получает все заявки со статусом `pending_ceo` — даже те, о которых уже получал уведомление ранее. Нет отметки "уведомление отправлено". При большом числе заявок CEO получит дубли.

**Исправление:** добавить поле `ceo_notified: bool` в модель или фильтровать заявки, созданные не ранее последнего просмотра (хранить timestamp в `Setting`). Минимальное решение — ограничить вывод:
```python
pending_requests = db.query(models.ExpenseRequest).filter(
    models.ExpenseRequest.status == "pending_ceo"
).order_by(models.ExpenseRequest.date.desc()).limit(10).all()
```

---

### 🟡 БАГ-16: `decisions.py` — нет проверки, что заявка не была уже обработана

**Файл:** `backend/app/services/bot/handlers/decisions.py`  
**Функции:** `handle_approve_senior`, `handle_reject_senior`, `handle_approve_ceo`, `handle_reject_ceo`

**Проблема:**  
Если CFO нажмёт кнопку "Утвердить" дважды (например, из двух чатов, или при задержке сети), статус обновится второй раз и создастся дублирующая запись в `expense_status_history`. Хуже — если первый клик одобрил, а второй — уже другой пользователь отклонил.

**Исправление:** добавить проверку текущего статуса перед обновлением:
```python
@router.callback_query(F.data.startswith("approve_senior_"))
async def handle_approve_senior(callback: types.CallbackQuery):
    expense_id = callback.data.removeprefix("approve_senior_")
    with database.database_session() as db:
        user = db.query(models.TeamMember).filter(...).first()
        if not user or user.position not in ["senior_financier", "admin"]:
            await callback.answer("У вас нет прав для этого действия", show_alert=True)
            return

        expense = db.query(models.ExpenseRequest).filter(
            models.ExpenseRequest.id == expense_id
        ).first()
        
        if not expense:
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        
        # ← НОВАЯ ПРОВЕРКА
        if expense.status != "pending_senior":
            await callback.answer(
                f"Заявка уже обработана (статус: {expense.status})",
                show_alert=True
            )
            return
        
        update = schemas.ExpenseStatusUpdate(status="approved_senior", comment="Утверждено CFO")
        crud.update_expense_status(db, expense_id, update, ...)
```

---

### 🟢 БАГ-17: `auth.py` в боте — пароль логируется в plaintext через `message.text`

**Файл:** `backend/app/services/bot/handlers/auth.py`  
**Функция:** `process_login`

**Проблема:**  
После ввода логина бот запрашивает пароль. Сообщение с паролем (`message.text`) видно в логах Telegram и потенциально в логах сервера, если включён debug-режим aiogram.

**Исправление:** сразу после получения пароля попытаться удалить сообщение:
```python
@router.message(ExpenseWizard.waiting_for_auth)
async def process_login(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if "login" not in data:
        await state.update_data(login=message.text)
        await message.answer("Теперь введите пароль:")
        return

    password = message.text
    # Удаляем сообщение с паролем из чата
    try:
        await message.delete()
    except Exception:
        pass  # Нет прав на удаление — ничего страшного
    
    # ... проверка пароля
```

---

## 4. Новые баги — Связь бот ↔ БД

---

### 🔴 БАГ-18: `send_admin_notification` вызывается вне транзакции с риском race condition

**Файл:** `backend/app/api/expenses.py`  
**Функция:** `create_expense` (POST /api/expenses)

**Проблема:**  
Уведомление администратору отправляется через `background_tasks.add_task(send_admin_notification, expense_req.id, ...)`. Задача выполняется асинхронно, и к моменту её выполнения `expense_req.id` уже закоммичен. Это корректно. **Но** сама `send_admin_notification` открывает новую сессию и делает `db.query(...).filter(id == expense_id)`. Если по какой-то причине коммит ещё не виден новой сессии (read-after-write на реплике), функция вернёт `None` и уведомление не отправится.

**Исправление:** передавать в `send_admin_notification` не только `id`, но и уже необходимые данные, чтобы не делать повторный запрос к БД:

```python
# Вариант: создать упрощённую версию для фонового задания
async def send_admin_notification_data(
    admin_chat_id: int,
    expense_id: str,
    request_id: str,
    project_name: str,
    project_code: str,
    created_by: str,
    purpose: str,
    total_amount,
    currency: str,
    usd_rate=None,
    request_type: str = "expense"
) -> None:
    # Формирует и отправляет сообщение без запроса к БД
    ...
```

---

### 🔴 БАГ-19: `forward_senior` и `forward_ceo` не проверяют допустимость перехода статуса

**Файл:** `backend/app/api/expenses.py`  
**Функции:** `forward_to_senior_financier`, `forward_to_ceo`

**Проблема:**  
Можно отправить заявку в `pending_ceo` из любого статуса, включая `declined` или `archived`. Нет машины состояний — только прямая запись нового статуса.

**Исправление:** добавить разрешённые переходы:
```python
ALLOWED_TRANSITIONS = {
    "pending_senior": ["request", "review", "revision"],
    "pending_ceo": ["approved_senior", "pending_senior"],
}

def validate_transition(current_status: str, new_status: str) -> bool:
    allowed = ALLOWED_TRANSITIONS.get(new_status, [])
    return current_status in allowed

# В endpoint:
if not validate_transition(expense.status, "pending_senior"):
    raise HTTPException(
        status_code=400,
        detail=f"Нельзя перевести в pending_senior из статуса {expense.status}"
    )
```

---

### 🟡 БАГ-20: Telegram `chat_id` не обновляется при повторном логине

**Файл:** `backend/app/services/bot/handlers/auth.py`  
**Функция:** `process_login`

**Проблема:**  
При повторном логине через `/start` (если пользователь уже залогинен) `telegram_chat_id` не обновляется — используется старый. Если пользователь поменял Telegram-аккаунт или удалил бота и снова добавил, уведомления пойдут на старый `chat_id`.

Текущая проверка:
```python
user = db.query(models.TeamMember).filter(
    models.TeamMember.telegram_chat_id == tg_id
).first()
if user:
    # Пользователь уже залогинен — показываем главное меню
    return
```

Но проверка идёт **до** повторной аутентификации. Если пользователь уже зарегистрирован — бот просто показывает меню, не предлагая обновить `chat_id`.

**Исправление:** после успешной аутентификации всегда обновлять `telegram_chat_id`:
```python
# В process_login, после успешной проверки пароля:
user.telegram_chat_id = tg_id
db.commit()
```
Убедиться, что это делается и при повторном входе.

---

## 5. Новые баги — Админка (Frontend ↔ Backend)

---

### 🔴 БАГ-21: `ExpenseDetail.tsx` загружает все 1000 заявок для показа одной

**Файл:** `frontend/src/pages/ExpenseDetail.tsx`  
**Строка:** ~79

**Проблема:**  
```typescript
const { data: expensesPage } = useQuery({
    queryKey: ["expenses"],
    queryFn: () => store.getExpenses({ limit: 1000 }),
});
const expense = expenses.find((e) => e.id === id);
```
Загружается 1000 записей, чтобы найти одну по `id`. Это 100x избыточный трафик, медленная загрузка, и при более чем 1000 заявках нужная запись вообще не найдётся.

**Исправление:**

**Backend — добавить эндпоинт:**
```python
# backend/app/api/expenses.py
@router.get("/{expense_id}", response_model=schemas.ExpenseRequestSchema)
def read_expense_by_id(
    expense_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    expense = db.query(models.ExpenseRequest).filter(
        models.ExpenseRequest.id == expense_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    # Проверка доступа
    if not auth.is_admin(current_user) and expense.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return expense
```

**Frontend — добавить метод в `expenses.ts`:**
```typescript
getExpenseById: async (id: string): Promise<ExpenseRequest> => {
    const res = await apiFetch(`/expenses/${id}`);
    const e = await res.json();
    return {
        id: e.id,
        requestId: e.request_id,
        // ... маппинг полей
    };
},
```

**Frontend — обновить `ExpenseDetail.tsx`:**
```typescript
const { data: expense, isLoading } = useQuery({
    queryKey: ["expense", id],
    queryFn: () => store.getExpenseById(id),
    enabled: !!id,
});
```

---

### 🔴 БАГ-22: CORS разрешён по regex `https?://.*\.thompson\.uz` — слишком широко

**Файл:** `backend/main.py`

**Проблема:**  
```python
cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX", r"https?://.*\.thompson\.uz")
```
Этот паттерн разрешает запросы с **любого** поддомена `thompson.uz`, включая `evil.thompson.uz`, `xss.thompson.uz` и т.д. Если злоумышленник может создать поддомен (или это ошибочный поддомен) — он получит полный доступ к API.

**Исправление:**
```python
cors_origin_regex = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"https://(finance|api-finance)\.thompson\.uz"
)
```
Использовать точный список:
```python
origins = [
    "https://finance.thompson.uz",
    "https://api-finance.thompson.uz",
]
# В production убрать localhost полностью
if os.getenv("DEBUG") == "true":
    origins += ["http://localhost:3000", "http://localhost:5173"]
```

---

### 🟡 БАГ-23: `Applications.tsx` — polling каждые 10 секунд при активном SSE

**Файл:** `frontend/src/pages/Applications.tsx`  
**Строка:** ~40

**Проблема:**  
```typescript
refetchInterval: 10000,  // 10 секунд
```
В приложении есть SSE (`/api/notifications/stream`) для real-time уведомлений. Polling каждые 10 секунд при активном SSE — дублирование. При 10 открытых вкладках — 60 запросов/минуту к БД без причины.

**Исправление:**
```typescript
const { data: expensesPage, isLoading, isFetching } = useQuery({
    queryKey: ["expenses", skip],
    queryFn: () => store.getExpenses({ skip, limit: LIMIT }),
    // Убрать refetchInterval, обновлять через SSE:
    refetchOnWindowFocus: true,
    staleTime: 30000, // 30 секунд — данные считаются свежими
});

// При получении SSE-уведомления об обновлении:
// queryClient.invalidateQueries({ queryKey: ["expenses"] })
```

---

### 🟡 БАГ-24: `ExpenseDetail.tsx` не проверяет историю статусов — показывает пустой Timeline

**Файл:** `frontend/src/pages/ExpenseDetail.tsx`  
**Компонент:** `HistoryTimeline`

**Проблема:**  
```typescript
const { data: history = [] } = useQuery({
    queryKey: ["expense-history", id],
    queryFn: () => store.getExpenseHistory(id),
    enabled: !!id,
});
```
Если запрос к `/api/expenses/{id}/history` вернёт ошибку (403, 404), `history` будет `[]` (дефолт), и компонент просто не покажет историю. Пользователь не получит сообщения об ошибке — молчаливый фейл.

**Исправление:**
```typescript
const { data: history = [], isError: historyError } = useQuery({...});

// В JSX:
{historyError && (
    <p className="text-xs text-destructive">Не удалось загрузить историю</p>
)}
```

---

### 🟡 БАГ-25: `AdminApprovals.tsx` — загружает все заявки без фильтра по статусу

**Файл:** `frontend/src/pages/AdminApprovals.tsx`

**Проблема:**  
```typescript
const { data: expensesPage, isLoading } = useQuery({
    queryKey: ["admin-expenses-approvals"],
    queryFn: () => store.getExpenses({ limit: 100 }),  // ← нет фильтра по статусу
});
```
Загружаются все 100 последних заявок включая `confirmed`, `archived`, `declined`. Для отображения в Kanban-колонках они фильтруются на клиенте. Это избыточно — `archived` и `confirmed` не нужны на этой странице.

**Исправление:**
```typescript
queryFn: () => store.getExpenses({
    limit: 100,
    status: "request,review,revision,pending_senior,approved_senior,rejected_senior,pending_ceo,approved_ceo,rejected_ceo"
}),
```

---

### 🟢 БАГ-26: `store.ts` — `exportDocx` для бланков использует неправильный эндпоинт

**Файл:** `frontend/src/lib/services/expenses.ts`  
**Функция:** `exportDocx`

**Проблема:**  
```typescript
exportDocx: async (expenseId: string, isBlank: boolean = false) => {
    const endpoint = isBlank 
        ? `/expenses/${expenseId}/export-blank-docx` 
        : `/expenses/${expenseId}/export-docx`;
```

В `ExpenseCard.tsx` вызов:
```typescript
const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    store.exportDocx(expense.id);  // ← isBlank не передаётся!
};
```
Для бланков (`requestType === "blank"`) `isBlank` не передаётся — всегда `false`. Бланк скачивается через неправильный эндпоинт.

**Исправление в `ExpenseCard.tsx`:**
```typescript
const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    const isBlank = expense.requestType === "blank" || expense.requestType === "blank_refund";
    store.exportDocx(expense.id, isBlank);
};
```

---

## 6. Итоговая таблица

| # | Баг | Приоритет | Файл | Исправлено? |
|---|-----|-----------|------|-------------|
| 01 | Двойной `db.commit()` в `generate_request_id` | 🔴 Критический | `crud.py` | ❌ |
| 02 | `usd_rate` сохраняется для UZS | 🔴 Критический | `crud.py` | ❌ |
| 03 | Утечка сессий в `notifications.py` | 🔴 Критический | `notifications.py` | ❌ |
| 04 | `total_amount=0` в `refund_blank_wizard` | 🔴 Критический | `refund_blank_wizard.py` | ❌ |
| 05 | `user_id` не в FSM-стейте | 🔴 Критический | `blank_wizard.py` | ❌ |
| 06 | `DetachedInstanceError` в уведомлениях | 🔴 Критический | `notifications.py` | ❌ |
| 07 | N+1 запросы при загрузке проектов | 🟡 Средний | `blank_wizard.py` | ❌ |
| 08 | Пустой `project_id=""` не обрабатывается | 🟡 Средний | `crud.py` | ❌ |
| 09 | Разные паттерны сессий в хендлерах | 🟡 Средний | `handlers/*.py` | ❌ |
| 10 | Нет eager loading при работе с user.projects | 🟢 Низкий | `blank_wizard.py` | ❌ |
| 11 | FSM не сбрасывается при ошибке `expense_wizard` | 🔴 Критический | `expense_wizard.py` | ❌ |
| 12 | `user_id=None` при устаревшей FSM-сессии в refund | 🔴 Критический | `refund_wizard.py` | ❌ |
| 13 | `Bot(token=None)` ломает старт сервера | 🔴 Критический | `notifications.py` | ❌ |
| 14 | `user_id` не передаётся в `RefundBlankWizard` | 🟡 Средний | `blank_wizard.py` | ❌ |
| 15 | Дублирование уведомлений CEO | 🟡 Средний | `ceo.py` | ❌ |
| 16 | Двойное нажатие кнопок в `decisions.py` | 🟡 Средний | `decisions.py` | ❌ |
| 17 | Пароль логируется в plaintext | 🟢 Низкий | `auth.py` (bot) | ❌ |
| 18 | Race condition при уведомлении через background_task | 🟡 Средний | `expenses.py` (api) | ❌ |
| 19 | Нет валидации переходов статусов | 🔴 Критический | `expenses.py` (api) | ❌ |
| 20 | `chat_id` не обновляется при повторном логине | 🟡 Средний | `auth.py` (bot) | ❌ |
| 21 | `ExpenseDetail` загружает 1000 заявок вместо 1 | 🔴 Критический | `ExpenseDetail.tsx` | ❌ |
| 22 | CORS regex слишком широкий | 🟡 Средний | `main.py` | ❌ |
| 23 | Polling + SSE — двойная нагрузка | 🟡 Средний | `Applications.tsx` | ❌ |
| 24 | Молчаливый фейл истории статусов | 🟢 Низкий | `ExpenseDetail.tsx` | ❌ |
| 25 | `AdminApprovals` грузит лишние статусы | 🟡 Средний | `AdminApprovals.tsx` | ❌ |
| 26 | `exportDocx` не передаёт `isBlank` для бланков | 🟢 Низкий | `ExpenseCard.tsx` | ❌ |

---

## Рекомендуемый порядок исправления

### День 1 — Критические (блокирующие работу)
1. **БАГ-13** — `Bot(token=None)` — сервер не стартует
2. **БАГ-03** — утечка сессий — падение под нагрузкой
3. **БАГ-06** — `DetachedInstanceError` — уведомления не работают
4. **БАГ-01** — двойной коммит — дубли request_id
5. **БАГ-04** — `total_amount=0` — данные теряются

### День 2 — Критические (данные и UX)
6. **БАГ-05** — `user_id` в FSM — бланки не создаются
7. **БАГ-12** — FSM устаревает — возврат не создаётся
8. **БАГ-11** — FSM не сбрасывается — пользователь застревает
9. **БАГ-19** — переходы статусов — можно одобрить закрытую заявку
10. **БАГ-21** — ExpenseDetail 1000 записей — медленная загрузка

### День 3 — Средние
11. **БАГ-02** — usd_rate для UZS
12. **БАГ-16** — двойное нажатие кнопок
13. **БАГ-20** — обновление chat_id
14. **БАГ-09** — унификация сессий
15. **БАГ-23** — polling + SSE

### День 4 — Низкие / Улучшения
16. Остальные баги (07, 08, 10, 14, 15, 17, 18, 22, 24, 25, 26)
