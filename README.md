# Fridgestare

There are good things to cook this week. You just can't think of them while you're staring into the fridge.

Fridgestare is a meal-planning application for weekly dinner planning. It combines a FastAPI backend, a React/Vite frontend, deterministic weekly planning, chat-driven plan edits, optional recipe discovery, CSV export, and email summaries.

## Stack

- Backend: FastAPI, SQLAlchemy 2.x, Alembic, APScheduler, pytest
- Frontend: React 19, TypeScript, Vite, Vitest
- Database: MariaDB in Docker Compose, SQLite for fast local smoke tests
- Integrations: OpenRouter, Tavily, Mailgun with graceful local fallback when API keys are absent

## Features

- Local auth with HTTP-only session cookies and CSRF protection
- Bootstrap CLI for creating the first user
- User preferences and recurring planning rules
- Meal library CRUD, bulk fast-add, tags, and CSV export
- Deterministic weekly plan generation with reroll, drag-drop move support, manual replacement, takeout slots, undo, and cooked/skipped outcome tracking
- Chat-based plan edits
- Discovery suggestions with accept-into-library flow
- Email preview and Mailgun-backed or mock delivery
- Optional in-process scheduler for automatic plan generation and email delivery

## Quick Start

1. Copy the environment template.

```bash
cp .env.example .env
```

2. Create the backend virtual environment and install dependencies.

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .[dev]
```

3. Install frontend dependencies.

```bash
cd ../frontend
npm install
```

4. Start the full stack with Docker Compose.

```bash
docker compose up --build
docker compose exec backend python -m app.cli.main system init-db
docker compose exec backend python -m app.cli.main users create --email sam@example.com --password tremendous-albatross --admin
```

The frontend runs at `http://localhost:5173` and talks to the backend at `http://localhost:8000`.

## Optional Local Backend/Frontend

If you want the database in Docker but the backend and frontend on the host, keep `.env` for Compose and add host-local overrides in `.env.local`.

```bash
cat <<'EOF' > .env.local
DATABASE_URL=mysql+pymysql://fridgestare:fridgestare@localhost:3306/fridgestare?charset=utf8mb4
EOF

docker compose up db
cd backend && .venv/bin/python -m app.cli.main system init-db
cd backend && .venv/bin/python -m app.cli.main users create --email sam@example.com --password tremendous-albatross --admin
cd backend && .venv/bin/python -m uvicorn app.main:app --reload
cd frontend && npm run dev
```

`.env.local` is loaded after `.env`, so the host-local database URL overrides the Compose-only `db` hostname.

## Useful Commands

```bash
make backend-test
make backend-lint
make frontend-test
make frontend-build
make compose-up
```

## Environment Variables

- `DATABASE_URL`: backend database connection string
- `APP_SECRET_KEY`: session signing key
- `APP_BASE_URL`: public application URL used in email links
- `OPENROUTER_API_KEY`: optional, improves chat interpretation
- `OPENROUTER_MODEL`: optional, defaults to a small OpenRouter model
- `TAVILY_API_KEY`: optional, enables live web-backed discovery
- `MAILGUN_API_KEY`: optional, enables live email delivery
- `MAILGUN_DOMAIN`: optional, required with Mailgun API key
- `MAIL_FROM_ADDRESS`: sender address used for plan emails
- `BACKEND_CORS_ORIGINS`: comma-separated origins or a JSON array
- `VITE_API_PROXY_TARGET`: optional frontend dev proxy target; Compose sets this to `http://backend:8000`, host-local frontend can leave the default `http://localhost:8000`
- `SCHEDULER_ENABLED`: set to `true` to enable the background scheduler

When OpenRouter, Tavily, or Mailgun are not configured, Fridgestare still works with local fallback behavior.

## Testing

Backend:

```bash
cd backend && .venv/bin/python -m pytest -q
```

Frontend:

```bash
cd frontend && npm run typecheck
cd frontend && npm run test -- --run
cd frontend && npm run build
```

## Notes

- The scheduler is optional and safe to leave disabled for local development.
- MariaDB DDL is non-transactional, so a failed `alembic upgrade` leaves partially applied DDL with `alembic_version` unchanged. For local development, recover with `docker compose down -v` and re-run.
- Discovery and email endpoints remain usable without third-party keys; they fall back to local mock behavior.
- Weekly planner links generated in email target `/plans/{week_start}` in the SPA.
