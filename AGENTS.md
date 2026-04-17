# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository layout
- `frontend/`: React + Vite + TypeScript SPA.
- `backend/`: FastAPI API, SQLAlchemy models/repositories, Telegram bot (Aiogram), Redis-backed notifications.
- Root `docker-compose.yml`: production-like deployment wiring for frontend, backend, postgres, redis.
- `backend/docker-compose.yml`: local backend stack (app + db + redis).

## Core development commands
Run commands from the directory noted in each section.

### Frontend (`frontend/`)
- Install deps: `npm install`
- Dev server: `npm run dev`
  - Vite runs on port `8080` and proxies `/api` to `http://localhost:8000` (see `frontend/vite.config.ts`).
- Build: `npm run build`
- Lint: `npm run lint`
- Tests (all): `npm run test`
- Tests (single file): `npm run test -- src/test/example.test.ts`
- Tests (single test name): `npm run test -- -t "example"`

### Backend (`backend/`)
- Create venv + install deps:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Run FastAPI locally: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Run Bot worker locally: `python bot_worker.py`
- Run migrations: `alembic upgrade head`
- Local backend stack via Docker: `docker compose up --build`
  - Uses `backend/docker-compose.yml` and starts app + bot_worker + postgres + redis.

### Full stack with Docker (repo root)
- Start all services: `docker compose up -d --build`
- Tail backend logs: `docker logs -f finance-backend-main`

## Testing reality in this repo
- Frontend test setup is present and wired through Vitest (`frontend/vitest.config.ts`).
- Backend does not currently include a standard `tests/` suite/config in this repository snapshot.
- There is a backend script-like check at `backend/test_analytics.py` that can be run directly:
  - `python test_analytics.py` (from `backend/`)

## High-level architecture
### Backend request flow and boundaries
- FastAPI app entrypoint is `backend/main.py`.
  - Registers all API routers under `/api`.
  - Adds global exception handlers, CORS, and request logging middleware.
  - Uses lifespan startup/shutdown to seed initial users and run the Telegram bot in a background watchdog loop.
- Router layer (`backend/app/api/*.py`) handles HTTP concerns, auth dependencies, and response shaping.
- Service layer (`backend/app/services/core/*.py`, plus docx/excel/currency/refund services) owns business logic.
- Repository layer (`backend/app/db/repository/*.py`) encapsulates DB querying/mutations and status history writes.
- ORM/data layer:
  - Models in `backend/app/db/models.py`.
  - Pydantic schemas/contracts in `backend/app/db/schemas.py`.
  - DB session wiring in `backend/app/core/database.py`.

### Expense workflow model
- `ExpenseRequest` is the central aggregate (`backend/app/db/models.py`) used for:
  - Normal expenses (`request_type="expense"`),
  - Refunds (`request_type="refund"` / `blank_refund`),
  - Blank document flows (`request_type="blank"`).
- Status transitions are enforced in API/service logic (`backend/app/api/expenses.py` + `expense_service` + repository history updates).
- Human-readable request IDs are generated per project/branch prefix via `ProjectCounter` in `expense_repository.generate_request_id`.
- Document exports are generated server-side:
  - DOCX via `app/services/docx/*`
  - XLSX via `app/services/analytics/export.py` / `app/services/excel/*`.
- **Future Roadmap**:
  - Implement self-service template uploading for financiers. Currently, templates are hardcoded/semi-manual. Goal: allow .docx template uploads per project/branch in the admin panel.

### Notifications and bot integration
- The bot logic lives under `backend/app/services/bot/`.
- The bot runs in its own dedicated microservice/process (e.g. `docker-compose up bot_worker` or `python bot_worker.py`), decoupled from the main FastAPI app.
- Real-time web notifications use SSE endpoint `/api/notifications/stream`, backed by Redis pub/sub (`backend/app/services/notifications/sse.py`).

### Frontend architecture and data access
- App bootstrap: `frontend/src/main.tsx` -> `App.tsx`.
- Routing is centralized in `App.tsx`:
  - Public login route `/`,
  - Protected dashboard nested routes under `/dashboard`,
  - Public submission flows under `/submit` and `/blank`.
- Data fetching/caching uses React Query in pages; API calls are centralized behind `store`.
  - `frontend/src/lib/store.ts` is a facade that merges modular domain services (`auth`, `projects`, `team`, `expenses`, `analytics`) and RBAC helpers.
  - `frontend/src/lib/api-client.ts` standardizes auth headers, API base URL (`VITE_APP_API_URL` or `/api`), and 401/error handling.
- Role behavior is largely client-side via localStorage-backed RBAC helpers in `frontend/src/lib/rbac.ts`; backend still enforces authorization on protected endpoints.

## Conventions to preserve when changing code
- Keep API field compatibility between backend snake_case and frontend mapping logic in `frontend/src/lib/services/*` (many services transform response shapes).
- For new expense statuses or request types, update both:
  - Backend transition/validation logic and enums (`backend/app/db/schemas.py`, `backend/app/api/expenses.py`),
  - Frontend status labels/boards/filters in `frontend/src/lib/types` and page components.
- If modifying startup/runtime behavior, verify both direct `uvicorn main:app` and container startup via `backend/scripts/entrypoint.sh` (which runs migrations before launching).
