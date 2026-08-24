# Fridgestare

There are good things to cook this week. You just can't think of them while you're staring into the fridge.

Fridgestare is a meal-planning application for weekly dinner planning. It combines a FastAPI backend, a React/Vite frontend, weighted weekly planning, chat-driven plan edits, optional recipe discovery, CSV export, and email summaries.

Deploying it for real is a separate document: see [DEPLOYMENT.md](DEPLOYMENT.md).

## Stack

- Backend: FastAPI, SQLAlchemy 2.x, Alembic, APScheduler, pytest
- Frontend: React 19, TypeScript, Vite, Vitest
- Database: MariaDB in Docker Compose, SQLite for fast local smoke tests
- Integrations: OpenRouter, Tavily, Mailgun with graceful local fallback when API keys are absent

## Features

- Local auth with HTTP-only session cookies and CSRF protection
- Bootstrap CLI for creating the first user, rotating a password, and listing accounts
- User preferences and recurring planning rules
- Meal library CRUD, bulk fast-add, tags, and CSV export
- Weekly plan generation with reroll, drag-drop move support, manual replacement, takeout slots, undo, and cooked/skipped outcome tracking. Selection is weighted by recurrence tier, seasonal overrides, day rules, and recent history, with a random draw among close candidates so regenerating a week gives a genuinely different plan
- Chat-based plan edits
- Discovery suggestions with accept-into-library flow
- Email preview and Mailgun-backed or mock delivery
- Optional in-process scheduler that generates the coming week and emails it once, at the weekday and local time set in preferences

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
docker compose exec backend python -m app.cli.main users create --email sam@example.com --password tremendous-albatross --admin
```

The backend container runs `system bootstrap-db` (`alembic upgrade head`) on start,
so the schema is already in place by the time you create the first user.

The frontend runs at `http://localhost:5173` and talks to the backend at `http://localhost:8000`.

## Optional Local Backend/Frontend

If you want the database in Docker but the backend and frontend on the host, keep `.env` for Compose and add host-local overrides in `.env.local`.

```bash
cat <<'EOF' > .env.local
DATABASE_URL=mysql+pymysql://fridgestare:fridgestare@localhost:3306/fridgestare?charset=utf8mb4
EOF

docker compose up db
cd backend && .venv/bin/python -m app.cli.main system bootstrap-db
cd backend && .venv/bin/python -m app.cli.main users create --email sam@example.com --password tremendous-albatross --admin
cd backend && .venv/bin/python -m uvicorn app.main:app --reload
cd frontend && npm run dev
```

`.env.local` is loaded after `.env`, so the host-local database URL overrides the Compose-only `db` hostname.

## Useful Commands

```bash
make check          # everything CI runs
make backend-test
make backend-lint
make frontend-lint
make frontend-test
make frontend-build
make compose-up      # development stack
```

The production stack is a separate compose file:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## Environment Variables

- `DATABASE_URL`: backend database connection string
- `APP_ENV`: `development` (default) or `production`. Production refuses to start on a
  placeholder secret key, an http base URL, secure-cookies-off over https, or a scheduler
  with no way to send mail
- `APP_SECRET_KEY`: session signing key
- `APP_BASE_URL`: public URL of the frontend. Plan emails link to `<APP_BASE_URL>/plans/<week_start>`, an SPA route, so this points at the frontend rather than the API
- `COOKIE_SECURE`: set to `true` when serving over HTTPS so session cookies carry the `Secure` flag
- `OPENROUTER_API_KEY`: optional, improves chat interpretation
- `OPENROUTER_MODEL`: optional, defaults to a small OpenRouter model
- `TAVILY_API_KEY`: optional, enables live web-backed discovery
- `MAILGUN_API_KEY`: optional, enables live email delivery
- `MAILGUN_DOMAIN`: optional, required with Mailgun API key
- `MAILGUN_BASE_URL`: Mailgun region endpoint; `https://api.eu.mailgun.net` for EU domains
- `MAIL_FROM_ADDRESS`: sender address used for plan emails
- `BACKEND_CORS_ORIGINS`: comma-separated origins or a JSON array
- `VITE_API_PROXY_TARGET`: optional frontend dev proxy target; Compose sets this to `http://backend:8000`, host-local frontend can leave the default `http://localhost:8000`
- `SCHEDULER_ENABLED`: set to `true` to enable the background scheduler
- `LOG_LEVEL`: backend log level, default `INFO`
- `DOCS_ENABLED`: force `/docs` on or off; unset follows `APP_ENV`

When OpenRouter, Tavily, or Mailgun are not configured, Fridgestare still works with local fallback behavior.

## Testing

Backend:

```bash
cd backend && .venv/bin/python -m pytest -q
```

Frontend:

```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run test -- --run
cd frontend && npm run build
```

## Notes

- The backend keeps the scheduler and the login rate limiter in process memory, so it runs as a
  single uvicorn worker. Running more workers would give you one scheduler per worker.
- The scheduler is optional and safe to leave disabled for local development. When enabled it wakes every 30 minutes but only sends once the user's configured weekday and local send time have passed, and it sends a given week's plan at most once.
- MariaDB DDL is non-transactional, so a failed `alembic upgrade` leaves partially applied DDL with `alembic_version` unchanged. For local development, recover with `docker compose down -v` and re-run.
- Discovery and email endpoints remain usable without third-party keys; they fall back to local mock behavior.
- Weekly planner links generated in email target `/plans/{week_start}` in the SPA.
- `system init-db` creates tables directly with SQLAlchemy and is a convenience for throwaway local databases. Anything you intend to migrate later should be brought up with `system bootstrap-db` so Alembic owns the schema.
