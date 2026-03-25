# Checkpoint - Safina Bot Project (Frontend)
Date: 2026-03-24

## 🛠 Tech Stack Summary

### Frontend
- **Core:** React 18, TypeScript, Vite
- **UI/Styling:** Tailwind CSS + Shadcn UI (Radix) + Lucide Icons + Framer Motion (animations)
- **State & API:** TanStack Query (React Query) v5, custom `useApi` hook
- **Forms:** React Hook Form + Zod
- **Features:** 
    - **Analytics**: Интерактивные графики расхода (Recharts).
    - **PDF/Docx**: Генерация отчетов и экспорт данных.
    - **Kanban**: Управление возвратами (`@hello-pangea/dnd`).

---
## 📂 Key Pages & Components
- `/dashboard`: Общая аналитика и статистика.
- `/expenses`: Список всех расходов с фильтрацией.
- `/refunds`: **[NEW]** Kanban-доска для управления возвратами.
- `/applications`: **[NEW]** Очередь заявок для админа и финансиста.
- `/blank-form`: Универсальная форма создания заявок.
- `/admin-approvals`: Центр управления подтверждениями.

---
## 🚀 Current Status
- Реализована полноценная ролевая модель (Admin / CFO / Staff).
- Интегрирована автоматическая авторизация из Telegram Mini App.
- Настроены Nginx прокси и лимиты для загрузки фото чеков.
