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
- [ ] Commit milestone.

### Phase 3: LLM, Discovery, Email, Scheduler

- [ ] Add OpenRouter and Tavily adapters with safe fallbacks.
- [ ] Add chat intent parsing and plan mutation pipeline.
- [ ] Add Mailgun integration and scheduler flow.
- [ ] Validate integration slice.
- [ ] Commit milestone.

### Phase 4: Frontend SPA

- [ ] Implement auth, preferences, meal library, planner board, discovery, and chat UI.
- [ ] Add drag and drop and outcome logging UX.
- [ ] Connect frontend to API.
- [ ] Validate frontend slice.
- [ ] Commit milestone.

### Phase 5: Hardening and Docs

- [ ] Add targeted tests and smoke coverage.
- [ ] Update root documentation and deployment notes.
- [ ] Run focused validation across backend and frontend.
- [ ] Commit milestone.

## Decisions Made During Build

- Keep plan slots as a normalized table, matching the build plan.
- Use synchronous SQLAlchemy sessions for v1 to reduce moving parts during initial delivery.
- Use JWT-backed HTTP-only cookies plus a separate CSRF cookie/header pair for browser mutations.
