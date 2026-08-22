# Fridgestare Build Progress

## Coordination Notes

- Main orchestrator retains architectural context and integration decisions.
- Subagents are used for scoped research and checkpoint review.
- Each milestone ends with validation and a git commit.

## Milestones

### Phase 0: Scaffold and Tooling

- [x] Create backend and frontend folders.
- [x] Add Docker Compose, env template, Makefile, CI, and pre-commit config.
- [x] Add minimal FastAPI and Vite entrypoints.
- [x] Validate scaffold.
- [x] Commit milestone.

### Phase 1: Core Domain and Auth

- [x] Implement database models and Alembic migration.
- [x] Add bootstrap CLI and auth/session flow.
- [x] Add user preferences and recurring rules endpoints.
- [x] Validate backend domain slice.
- [ ] Commit milestone.

### Phase 2: Meals and Planning Backend

- [x] Implement meal CRUD, fast-add, tags, CSV export.
- [x] Implement deterministic planner, weekly plans, reroll, move, set, undo, and outcomes.
- [ ] Add discovery acceptance persistence.
- [x] Validate backend feature slice.
- [x] Commit milestone.

### Phase 3: LLM, Discovery, Email, Scheduler

- [x] Add OpenRouter and Tavily adapters with safe fallbacks.
- [x] Add chat intent parsing and plan mutation pipeline.
- [x] Add Mailgun integration and scheduler flow.
- [x] Validate integration slice.
- [x] Commit milestone.

### Phase 4: Frontend SPA

- [x] Implement auth, preferences, meal library, planner board, discovery, and chat UI.
- [x] Add drag and drop and outcome logging UX.
- [x] Connect frontend to API.
- [x] Validate frontend slice.
- [x] Commit milestone.

### Phase 5: Hardening and Docs

- [x] Add targeted tests and smoke coverage.
- [x] Update root documentation and deployment notes.
- [x] Run focused validation across backend and frontend.
- [x] Commit milestone.

## Decisions Made During Build

- Keep plan slots as a normalized table, matching the build plan.
- Use synchronous SQLAlchemy sessions for v1 to reduce moving parts during initial delivery.
- Use JWT-backed HTTP-only cookies plus a separate CSRF cookie/header pair for browser mutations.
- Database: PostgreSQL replaced by MariaDB, driven through PyMySQL (`mysql+pymysql://`), a pure-Python driver so the backend image needs no compiler or client libraries. Three things had to change beyond the connection strings: a `UtcDateTime` type decorator (`app/models/base.py`) keeps timestamps timezone-aware UTC because MariaDB's `DATETIME` carries no offset; `novel_meal_ratio` and `takeout_frequency_per_week` moved from `Float` to `Double`, since MariaDB's `FLOAT` is only 4 bytes and would round `0.15` to `0.15000000596`; and the two email lookups dropped `ILIKE`, which MariaDB compiles to a non-sargable `lower() LIKE lower()`. Alembic history was collapsed to a single MariaDB-native initial revision, and CI now runs `upgrade`/`check`/`downgrade` against a real MariaDB service.
