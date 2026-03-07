# Finance Thompson v4 Upgrade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the existing monolithic expense tracking system to a microservices-oriented v4 architecture, adding a two-level confirmation workflow, Excel template generation, and real-time frontend notifications.

**Architecture:** We will adopt a hybrid approach. The core CRUD operations remain in FastAPI. The Telegram Bot will be enhanced to handle Senior Financier interactions. We will add a Notification Service (Redis Pub/Sub + SSE) for pushing real-time updates to the React frontend. A Worker Service (Celery) will handle background generation of Excel reports to prevent blocking the main API.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery, Aiogram 3, React, Tailwind CSS, Shadcn/UI, Pandas/OpenPyXL.

---

### Task 1: Database Schema Expansion

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/db/schemas.py`
- Modify: `frontend/src/lib/types.ts`

**Step 1: Write the failing tests (or define schema checks)**
Define that the models must support the required new fields and statuses.

**Step 2: Write minimal implementation**
1. In `backend/app/db/models.py`, we need to ensure the system supports the Senior Financier role. Since we decided to generate a login/password for them, we modify `TeamMember` (if needed) or just rely on the existing structure and handle the role via logic (e.g., specific `login` or a new `role` field). Let's add an explicit `role` field to `TeamMember` (defaulting to "user", can be "admin", "senior_fin").
2. In `ExpenseRequest`, the `status` Enum string needs to accommodate `pending_senior`, `approved_senior`, `rejected_senior`.
3. In `frontend/src/lib/types.ts`, update `ExpenseStatus` and `STATUS_LABELS` to include the new statuses. Update `TeamMember` interface.

**Step 3: Commit**
```bash
git add backend/app/db/models.py backend/app/db/schemas.py frontend/src/lib/types.ts
git commit -m "feat: expand DB schema and TS types for v4 workflow"
```

---

### Task 2: Core API Workflow Updates

**Files:**
- Modify: `backend/app/api/expenses.py`
- Modify: `backend/app/db/crud.py`

**Step 1: Write the failing test**
Ensure that forwarding an expense to the Senior Financier changes its status correctly.

**Step 2: Write minimal implementation**
1. Add a new endpoint `POST /api/expenses/{expense_id}/forward_senior` in `expenses.py`.
2. This endpoint updates the status to `pending_senior` and triggers a background task to notify the bot service (via Redis Pub/Sub or direct call).
3. Update `crud.update_expense_status` to handle the new state transitions safely.

**Step 3: Commit**
```bash
git add backend/app/api/expenses.py backend/app/db/crud.py
git commit -m "feat: add forward_senior endpoint and CRUD logic"
```

---

### Task 3: Redis & Notification Service (SSE) Setup

**Files:**
- Create: `backend/app/services/notifications/sse.py`
- Modify: `backend/main.py`
- Create: `frontend/src/hooks/useNotifications.ts`

**Step 1: Write the failing test**
Verify clients can connect to the SSE endpoint and receive events.

**Step 2: Write minimal implementation**
1. Add `redis.asyncio` to `requirements.txt`.
2. Create an endpoint in `main.py` (e.g., `GET /api/notifications/stream`) that returns an `EventSourceResponse` listening to a Redis channel.
3. In `backend/app/services/notifications/sse.py`, implement the Redis Pub/Sub listener.
4. In `frontend/src/hooks/useNotifications.ts`, create a React hook that connects to `/api/notifications/stream` and triggers `toast` notifications when events arrive.

**Step 3: Commit**
```bash
git add backend/ requirements.txt frontend/src/hooks/
git commit -m "feat: setup SSE notification service via Redis"
```

---

### Task 4: Senior Financier Telegram Bot Workflow

**Files:**
- Modify: `backend/app/services/bot/handlers.py`
- Modify: `backend/app/services/bot/notifications.py`

**Step 1: Write the failing test**
Ensure the bot handles the new callbacks.

**Step 2: Write minimal implementation**
1. In `notifications.py`, implement `send_senior_fin_notification(expense_id)` which formats the message and adds InlineKeyboard buttons: `[📄 Скачать смету]`, `[✅ Одобрить]`, `[❌ Отклонить]`.
2. In `handlers.py`, add `CallbackQuery` handlers for these buttons.
3. The approve/reject handlers will call internal API logic to update the DB status to `approved_senior`/`rejected_senior`, and then publish an event to Redis so the Notification Service alerts Safina.
4. The download handler will trigger the Excel generation task and send the document back.

**Step 3: Commit**
```bash
git add backend/app/services/bot/
git commit -m "feat: implement Senior Financier bot workflow and callbacks"
```

---

### Task 5: Excel Template Generation (Worker)

**Files:**
- Create: `backend/app/services/excel/generator.py`
- Create: `backend/app/services/excel/template.xlsx` (Requires manual placement or basic generation first)
- Modify: `backend/app/api/expenses.py`

**Step 1: Write the failing test**
Generate a file and verify its headers and rows.

**Step 2: Write minimal implementation**
1. Build `backend/app/services/excel/generator.py` using `openpyxl`. It must load a template or programmatically create the exact yellow-header design shown in the requirements.
2. The function `generate_excel_smeta(expense_id)` will fetch the expense, fill the rows (ID, Date, Project, Name, Qty, Amount, Currency, Total), and return a `BytesIO` object.
3. Connect this to the Bot's download handler from Task 4.

**Step 3: Commit**
```bash
git add backend/app/services/excel/ backend/app/api/expenses.py
git commit -m "feat: implement Excel template generation"
```

---

### Task 6: Frontend ExpenseDetail Modifications

**Files:**
- Modify: `frontend/src/pages/ExpenseDetail.tsx`

**Step 1: Write the failing test**
Verify the new "Send to Senior" button appears only when appropriate.

**Step 2: Write minimal implementation**
1. Add the `[Отправить на согласование]` button. It should be visible to Admins/Safina when the expense needs it (e.g., status is `request` or `review`).
2. Implement the API call to `/api/expenses/{id}/forward_senior`.
3. Ensure the UI gracefully handles the new `pending_senior`, `approved_senior`, and `rejected_senior` statuses in the `actionButtons` and badges.

**Step 3: Commit**
```bash
git add frontend/src/pages/ExpenseDetail.tsx
git commit -m "feat: update ExpenseDetail UI for two-level confirmation"
```

---

### Task 7: Dashboard & Statistics Module

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Modify: `backend/app/api/expenses.py` (Add stats endpoint)

**Step 1: Write the failing test**
Verify charts load data correctly based on time filters.

**Step 2: Write minimal implementation**
1. Build a new endpoint `GET /api/expenses/statistics` supporting `time_filter` (month, 3m, 6m, year) returning aggregated data (totals by project/school, approval rates).
2. Install `recharts` in the frontend if not already present (`npm install recharts`).
3. Update `Dashboard.tsx` to include time filter toggles.
4. Add line charts for monthly dynamics and pie charts for project/branch distribution.

**Step 3: Commit**
```bash
git add frontend/src/pages/Dashboard.tsx backend/app/api/expenses.py package.json
git commit -m "feat: implement statistics dashboard with charts"
```

---

### Task 8: Infrastructure Updates & Pre-computation

**Files:**
- Modify: `backend/main.py` (CORS)
- Modify: `.env.example`
- Modify: `backend/app/db/crud.py` (Initial user generation)

**Step 1: Write the failing test**
Verify system boots with correct domains and default users.

**Step 2: Write minimal implementation**
1. Update `main.py` CORS origins to ensure `finance.thompson.uz` is correctly prioritized.
2. In `init_db_with_retry` (or a dedicated init script), add logic to auto-generate the `senior_fin` user alongside the `admin` user if they don't exist.
3. Ensure `.env.example` reflects any new required variables (e.g., REDIS_URL).

**Step 3: Commit**
```bash
git add backend/main.py .env.example backend/app/db/crud.py
git commit -m "chore: update infra config and user auto-generation"
```
