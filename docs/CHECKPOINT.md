# Checkpoint - Safina Bot Project (Backend)
Date: 2026-03-24

## ⚙️ Backend Architecture

### Core Stack
- **Framework**: FastAPI (Python 3.10+)
- **ORM**: SQLAlchemy 2.0 (Async-ready)
- **Database**: 
    - Production: PostgreSQL
    - Development: SQLite (`backend/media/safina.db`)
- **Migrations**: Alembic
- **Validation**: Pydantic v2

### Telegram Bot
- **Framework**: Aiogram 3.x
- **Key Modules**:
    - `blank_wizard`: Пошаговое создание заявок.
    - `refund_wizard`: Логика оформления возвратов.
    - `handlers`: Обработка команд и callback-кнопок.
- **Integration**: Бот работает в том же asyncio-цикле, что и FastAPI (через `lifespan`).

### API Endpoints (`/api`)
- `auth/`: JWT авторизация, регистрация, Telegram-логин.
- `expenses/`: CRUD операций с расходами, загрузка фото.
- `blanks/`: Работа с универсальными бланками.
- `refunds/`: Специализированная логика возвратов.
- `analytics/`: Агрегация данных для графиков.
- `notifications/`: Рассылка уведомлений админам.

### File Generation
- **Word**: Генерация по шаблонам `template.docx` с использованием `docxtpl`.
- **Excel**: Экспорт смет и отчетов через `pandas` / `openpyxl`.

---
## 🚀 Features & Stability
- **Global Error Handling**: Единый формат ответов для всех ошибок.
- **Background Tasks**: Генерация документов и уведомления не блокируют API.
- **Environment Driven**: Полная настройка через `.env` (CORS, DB, Bot Token).
