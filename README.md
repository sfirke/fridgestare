# Fridgestare

There are good things to cook this week. You just can't think of them while you're staring into the fridge.

Fridgestare is a meal-planning application for weekly dinner planning. It combines a FastAPI backend, a React/Vite frontend, deterministic weekly planning, chat-driven plan edits, optional recipe discovery, CSV export, and email summaries.

## Stack

- Backend: FastAPI, SQLAlchemy 2.x, Alembic, APScheduler, pytest
- Frontend: React 19, TypeScript, Vite, Vitest
- Database: PostgreSQL in Docker Compose, SQLite for fast local smoke tests
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

4. Start PostgreSQL with Docker Compose, then run the backend and frontend locally.

```bash
docker compose up db
cd backend && .venv/bin/python -m app.cli.main system init-db
cd backend && .venv/bin/python -m app.cli.main users create --email you@example.com --password change-me --admin
cd backend && .venv/bin/python -m uvicorn app.main:app --reload
cd frontend && npm run dev
```

The frontend runs at `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

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
- Discovery and email endpoints remain usable without third-party keys; they fall back to local mock behavior.
- Weekly planner links generated in email target `/plans/{week_start}` in the SPA.
