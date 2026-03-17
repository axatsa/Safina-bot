# Checkpoint - Safina Bot Project
Date: 2026-02-25

## 🛠 Tech Stack Summary

### Frontend
- **Core:** React 18, TypeScript, Vite
- **UI/Styling:** Tailwind CSS + Shadcn UI (Radix) + Lucide Icons
- **State & API:** TanStack Query (React Query) v5
- **Forms:** React Hook Form + Zod
- **Features:** Analytics (Recharts), PDF Generation (jsPDF)

### Backend
- **Framework:** FastAPI (Python), SQLAlchemy ORM, Pydantic
- **Database:** PostgreSQL (primary) / SQLite (local/test)
- **Auth:** JWT + Bcrypt
- **Docs:** docxtpl (docx generation)

### Telegram Bot
- **Framework:** aiogram (Async)
- **Status:** Integrated with shared backend models and CRUD logic.

### Infrastructure
- **Deployment:** Docker / Docker Compose
- **Web Server:** Nginx
- **CI/CD:** GitLab CI

---
## 📂 Project Structure
- `/expense-tracker-pro`: Main frontend application.
- `/expense-tracker-pro/finance-backend`: FastAPI server & shared logic.
- `/expense-tracker-pro/finance-backend/bot`: Telegram bot implementation.
