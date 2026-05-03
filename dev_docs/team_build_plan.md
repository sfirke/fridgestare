# Fridgestare Build Plan

## Purpose

This document turns the initial idea into an implementation plan that a team of coding agents can execute with limited ambiguity. It is opinionated where needed, calls out explicit product and architecture decisions, and isolates remaining open questions so implementation can proceed in a controlled way.

## Product Definition

Fridgestare is a multi-user dinner planning service that helps a user decide what to cook for the upcoming week. It combines:

- A user-owned meal library.
- A weekly planner that respects user preferences, recurring rules, complexity, seasonality, and takeout frequency.
- Optional AI-assisted recipe discovery for novel meals.
- A web UI for reviewing and editing the generated plan.
- Email delivery of proposed weekly plans with a secure link back into the app.

The initial deployment target is one operator on a laptop with intermittent uptime, then one Docker Compose deployment on a single cloud VM. The architecture should support multiple users and later public signup, but v1 remains invite-only or admin-created.

## Locked Decisions

These decisions are treated as settled for v1 unless explicitly changed later.

### Product Scope

- Support dinner only in v1.
- Mandatory v1 features:
  - Local auth.
  - Admin-created first user.
  - Weekly plan generation in the UI.
  - Email summary with secure edit link.
  - Drag and drop weekly calendar editing.
  - Chat-based edits.
  - Novel recipe discovery from the web.
  - CSV export of recipes.
  - Takeout frequency support.
- Out of scope for v1:
  - Shared recipe libraries between users.
  - Paprika import.
  - Recipe import from arbitrary URL.
  - Grocery list automation.
  - Admin UI for invitations.
  - Calendar integration with external providers.

### Planning Behavior

- Planning window is user-configurable by start day.
- Planner uses best-effort soft constraints with explanations rather than hard-failing on conflicts.
- Planner is hybrid:
  - Deterministic candidate generation and scoring.
  - LLM used to finalize and explain choices among structured candidates.
- Chat is allowed to edit the current plan immediately.
- Undo supports only the single most recent user-visible plan mutation in v1.
- Past weekly plans are retained and influence future meal selection to reduce excessive repetition.
- Accepted novel meals become first-class meal records with source URL and an `agent_sourced` flag.

### Discovery Behavior

- Novel recipe discovery returns meal suggestions with source URLs.
- The system does not scrape and store full copyrighted recipe text in v1.
- Discovery should honor dietary restrictions, complexity preferences, seasonality, and user taste profile.
- Discovery uses Tavily in v1 behind a provider-agnostic adapter so it can be swapped later.

### Auth and Multi-User Posture

- Canonical login identifier is email address.
- No public self-signup in v1.
- Public self-signup is a future possibility and the data model and service boundaries should not block it.
- First-user bootstrap must be possible via CLI.
- Admin remains a hidden bootstrap capability in v1, not a first-class product surface.

### Delivery and Deployment

- Docker Compose from the beginning.
- App must remain fully usable even if scheduled jobs are missed because the laptop is off.
- Weekly generation can be triggered both manually and by an app-managed scheduler.
- Frontend stack is an SPA with React and TypeScript, built with Vite, backed by a FastAPI JSON API.

## Opinionated Defaults Chosen Here

These were not fully specified, so this plan makes explicit choices to keep implementation moving.

- Use React + TypeScript SPA because drag and drop, chat, optimistic plan edits, and plan diff/undo behavior are materially easier there than with server-rendered templates.
- Use FastAPI with SQLAlchemy 2.x and Alembic.
- Use PostgreSQL for all environments, including local Docker Compose.
- Use Redis only if background jobs or rate limiting genuinely need it. Do not add it in the first scaffold by default.
- Use APScheduler inside the backend container for v1 scheduled generation. Manual regeneration remains available in UI and CLI.
- Use JWT-backed session cookies for browser auth, not localStorage tokens.
- Use password reset only after email infrastructure is stable; do not block v1 on it.
- Store user schedule guidance as structured text plus optional normalized recurring rules rather than forcing a complex calendar model up front.
- Prefer a rules-and-scores planner core that can run without the LLM if OpenRouter is unavailable.
- Keep tags as a lightweight first-class feature in v1 because they unlock better planning rules and discovery prompts with modest schema and UI cost.
- Use freeform tags plus a small set of suggested starter tags in the UI to reduce friction without imposing a rigid taxonomy.
- Track whether a planned meal was actually cooked or skipped, and let that feedback improve future scoring and unlock basic analytics.

## User Journeys

### Core Journey: Weekly Planning

1. User logs in.
2. User views upcoming week plan or generates one if missing.
3. Planner proposes dinners for each day using library meals, takeout rules, and optional novel meal quota.
4. User receives an email summary with a secure link.
5. User opens the weekly plan UI.
6. User drags meals between days, rerolls a slot, manually replaces a meal, or chats with the planner.
7. User accepts a discovered meal, which adds it to their library.

### Bootstrapping Journey

1. Operator brings up Docker Compose.
2. Operator runs CLI command to create the first user with email and password.
3. User logs in and bulk-adds a starter meal library with a fast-entry form.
4. User configures planning preferences, schedule guidance, dietary constraints, timezone, and weekly email timing.

### Ongoing Library Growth

1. User adds meals quickly using just a title.
2. User optionally adds complexity, seasonality, source notes, URL, and lightweight tags.
3. Accepted discovered meals enrich the library over time.
4. User can optionally record whether a past planned meal was actually cooked or skipped to improve future recommendations.
5. User exports the library as CSV at any time.

## Functional Requirements

### Accounts

- Admin or CLI can create users.
- Users authenticate with email and password.
- Passwords stored with Argon2 or bcrypt; Argon2 preferred.
- Each user has isolated data.
- Each user has timezone, preferred week start day, weekly email day/time, and planning preferences.

### Meal Library

- Create, edit, archive, and list meals.
- Fast-add mode supports entering many meals with minimal metadata.
- Archiving a meal removes it from future planning candidates but does not erase its past appearances in historical weekly plans.
- Meal fields:
  - Title.
  - Description or notes.
  - Meal type enum, default `dinner`.
  - Complexity enum: simple, intermediate, complex.
  - Recurrence tier enum: staple, regular, treat.
  - Seasonality preferences.
  - Dietary exclusions.
  - Optional user-defined tags such as `soup`, `tacos`, `company`, `comfort-food`, or `uses-red-potatoes`.
  - Source note.
  - Source URL.
  - Agent sourced boolean.
  - Active or archived status.
- CSV export includes all user-visible metadata.

### Preferences and Constraints

- User can specify:
  - Novel meal percentage.
  - Takeout frequency.
  - Allowed complexity levels.
  - Dietary restrictions.
  - Freeform planning guidance.
  - Recurring day rules like "Tuesday tacos" or "Thursday takeout".
- Planner should explain when constraints conflict or are not fully satisfied.

### Weekly Plan

- One current editable plan per target week per user.
- Historical weekly plans are retained indefinitely unless a later retention policy is introduced.
- A plan contains one dinner slot per configured day.
- Each slot can be one of:
  - Library meal.
  - Agent-sourced meal suggestion.
  - Takeout placeholder.
  - Empty or unplanned.
- Plan supports manual edit, reroll one day, reroll entire week, drag and drop reorder, and chat-driven modifications.
- Activity log records meaningful changes and supports undo of the last plan mutation only in v1.
- Historical slots can optionally be annotated with an outcome of `cooked` or `skipped` after the fact.
- If no outcome is logged, the slot still counts as a prior planned suggestion, but with weaker influence than a confirmed `cooked` result.

### Email

- Send scheduled weekly plan summary.
- Send on-demand plan summary from UI.
- Include secure deep link to the exact week plan.
- If the user is not authenticated when opening the email link, redirect them to login with a `next` parameter pointing back to the target plan.

### Discovery

- Discovery can be invoked during weekly generation or during reroll.
- Suggest URLs and summary metadata only.
- User must accept before adding a discovered meal to library.
- Discovery results should be cached per request window to control costs.

## Non-Functional Requirements

- Multi-user data isolation from day one.
- Local-first developer experience with Python venv supported.
- Compose-based deployment with one command startup.
- Planner remains useful when LLM provider is unavailable.
- Clear auditability of automated and chat-driven edits.
- Testable domain logic separated from HTTP and UI concerns.
- Minimal operational footprint suitable for a single VM.

## High-Level Architecture

### Services

- `frontend`: React/Vite SPA served as static assets by a lightweight web server or by FastAPI in production.
- `backend`: FastAPI app exposing REST endpoints, auth, planner orchestration, CSV export, and email triggers.
- `db`: PostgreSQL.
- Optional later:
  - `worker`: background jobs if APScheduler inside backend becomes insufficient.
  - `redis`: queue, caching, rate limiting.

### Backend Modules

- `auth`: login, logout, password hashing, session management, bootstrap user creation.
- `users`: profiles, preferences, schedule settings.
- `meals`: CRUD, fast-add, export.
- `plans`: weekly plan creation, retrieval, update, reroll, undo log.
- `planner`: deterministic scoring engine, conflict handling, candidate generation.
- `llm`: OpenRouter client, prompts, response validation, model fallback.
- `discovery`: candidate external recipes, result normalization, acceptance flow.
- `email`: Mailgun integration and deep links.
- `scheduler`: weekly trigger evaluation.
- `audit`: activity log entries and undo operations.

### Frontend Areas

- Auth screens.
- Meal library management.
- Fast-add onboarding form.
- Preferences and schedule settings.
- Weekly planner board or calendar.
- Chat panel attached to current week.
- Export and account settings.

## Data Model

The schema should be normalized enough for multi-user correctness, but not prematurely overdesigned.

### Core Tables

#### `users`

- `id`
- `email` unique
- `password_hash`
- `is_admin`
- `is_active`
- `timezone`
- `week_starts_on`
- `created_at`
- `updated_at`

#### `user_preferences`

- `user_id`
- `novel_meal_ratio`
- `takeout_frequency_per_week`
- `allow_simple`
- `allow_intermediate`
- `allow_complex`
- `planning_guidance_text`
- `dietary_notes`
- `email_enabled`
- `email_day_of_week`
- `email_local_time`

#### `recurring_rules`

- `id`
- `user_id`
- `day_of_week`
- `rule_type` such as `must_include_tag`, `prefer_tag`, `takeout`, `avoid_complex`
- `rule_payload` JSONB
- `priority`
- `active`

#### `meals`

- `id`
- `user_id`
- `title`
- `notes`
- `meal_type`
- `complexity`
- `recurrence_tier`
- `seasonality_mode`
- `source_note`
- `source_url`
- `agent_sourced`
- `is_archived`
- `created_at`
- `updated_at`

#### `meal_tags`

- `id`
- `user_id`
- `name`

Tags remain user-owned and freeform. The UI should suggest a starter set such as `soup`, `taco`, `quick`, `cozy`, `company`, and `takeout-inspired`.

#### `meal_tag_links`

- `meal_id`
- `tag_id`

#### `meal_season_preferences`

- `meal_id`
- `season`
- `weight`

Use weights rather than booleans so the planner can score "often in summer, rarely in winter" instead of forcing binary seasonality.

#### `weekly_plans`

- `id`
- `user_id`
- `week_start_date`
- `status` such as `draft`, `scheduled_sent`, or `superseded`
- `generation_source` such as `manual`, `scheduled`, `chat`, `reroll`
- `planner_explanation`
- `created_at`
- `updated_at`

Keep one current plan record per user and week. Preserve past weeks so the planner can score against actual prior suggestions and avoid near-term repetition.

#### `plan_slots`

- `id`
- `plan_id`
- `slot_date`
- `slot_order`
- `slot_type` such as `meal`, `discovered_meal`, `takeout`, `empty`
- `meal_id` nullable
- `discovered_candidate_id` nullable
- `title_snapshot`
- `notes_snapshot`
- `outcome_status` nullable, such as `cooked` or `skipped`
- `outcome_logged_at` nullable

Snapshots protect the plan from later meal edits changing historical intent.

The existence of a past plan slot already means the meal was planned. `outcome_status` is only for optional post-hoc user feedback.

#### `discovered_recipe_candidates`

- `id`
- `user_id`
- `title`
- `summary`
- `source_url`
- `complexity`
- `reasoning`
- `accepted_meal_id` nullable
- `created_at`

#### `activity_log`

- `id`
- `user_id`
- `plan_id` nullable
- `event_type`
- `actor_type` such as `user`, `scheduler`, `llm`
- `actor_id` nullable
- `payload` JSONB
- `undo_payload` JSONB nullable
- `created_at`

Only the most recent reversible plan mutation needs a valid `undo_payload` in v1.

## Planner Design

### Principle

Do not let the LLM own the entire planning process. Use a deterministic planner for correctness and repeatability, then use the LLM for taste-sensitive selection and human-readable explanations.

### Deterministic Candidate Generation

For each slot, compute candidate meals from the user library by filtering and scoring on:

- Allowed complexity.
- Recurring day rules.
- Seasonality weights.
- Time since last cooked.
- Presence of helpful tags for day-specific requests such as `soup`, `taco`, or `quick`.
- Recurrence tier target frequency.
- Takeout quotas.
- User dietary restrictions.
- Already selected meals in the same week to avoid repeats.
- Prior plan history across recent weeks to avoid monotony.
- Logged `cooked` versus `skipped` outcomes from prior weeks when available.

The deterministic layer should also generate explicit constraint notes, for example:

- "Thursday rule prefers takeout."
- "User disallows complex meals on weekdays."
- "No eligible soup meals found for Tuesday request."

Scoring guidance:

- Recent `cooked` meals should incur the strongest repeat penalty.
- Recent planned slots without logged outcomes should incur a weaker repeat penalty.
- Recent `skipped` meals should first reduce confidence in that specific meal for similar contexts, and only after repeated same-context skips should the planner weakly reduce confidence in adjacent patterns such as tags or complexity.

### LLM Finalization

The LLM receives structured candidate lists, user guidance, and conflict notes. It returns:

- Selected candidate per day.
- Short explanation for each choice.
- Any constraint conflicts it could not satisfy.
- Suggested discovered-meal requests when candidate pool is weak.

All LLM responses must be schema-validated. Reject or repair malformed output.

### Reroll Behavior

- Single-slot reroll should preserve the rest of the week.
- Reroll may pull from library or discovery depending on user novelty settings and available candidates.
- Reroll explanation should mention why the new choice differs from the old one.

### Chat Editing

Chat commands should be mapped into structured intents before executing mutations.

Examples:

- Replace day meal.
- Move meal to another day.
- Make a day takeout.
- Request a category like soup.
- Ask for simpler meals this week.

The safe path is:

1. Parse intent with LLM into structured action.
2. Validate action against the current plan and available data.
3. Execute mutation.
4. Write activity log and return explanation.

## Discovery Design

### v1 Discovery Contract

- Input: user preferences, liked meals, exclusions, allowed complexity, season, current week context.
- Output: title, short description, source URL, why it fits, estimated complexity.
- No full recipe storage.

### Discovery Sources

v1 uses Tavily plus LLM summarization of result snippets and page metadata where available.

Implementation constraints:

- Keep the provider behind a discovery adapter.
- Persist only normalized suggestion metadata, not full recipe text.
- Allow later replacement with a curated provider or allowlist without changing downstream planner APIs.

Rationale for choosing Tavily:

- Fast to integrate.
- Built for LLM workflows.
- Good enough search quality for v1 without building a heavier search stack first.

## API Shape

Use REST for v1. Keep request and response schemas stable and explicit.

### Auth

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /login?next=...` frontend route for post-auth redirect handling

### Users and Preferences

- `GET /api/me`
- `PATCH /api/me/preferences`
- `PATCH /api/me/schedule-rules`

### Meals

- `GET /api/meals`
- `POST /api/meals`
- `POST /api/meals/bulk-fast-add`
- `GET /api/meals/{meal_id}`
- `PATCH /api/meals/{meal_id}`
- `DELETE /api/meals/{meal_id}` as archive
- `GET /api/meals/export.csv`
- `GET /api/tags/suggestions`

### Plans

- `GET /api/plans/current`
- `GET /api/plans/week/{week_start}`
- `POST /api/plans/generate`
- `POST /api/plans/{plan_id}/reroll-slot`
- `POST /api/plans/{plan_id}/move-slot`
- `POST /api/plans/{plan_id}/set-slot`
- `POST /api/plans/{plan_id}/undo`
- `POST /api/plans/{plan_id}/send-email`
- `POST /api/plans/{plan_id}/slots/{slot_id}/outcome-status`

### Chat

- `POST /api/plans/{plan_id}/chat`

### Discovery

- `POST /api/discovery/suggest`
- `POST /api/discovery/{candidate_id}/accept`

### Admin and CLI

- CLI command: `fridgestare users create --email ... --password ... [--admin]`
- Optional protected admin endpoint later, but not required in v1.

## Frontend UX Plan

### Visual Direction

- Dark-first whimsical UI.
- Avoid generic SaaS look.
- Calendar or board view should feel tactile and playful without obscuring information density.

### Key Screens

#### Login

- Minimal auth UI.

#### First-Run Setup

- Timezone.
- Week start day.
- Email timing.
- Allowed complexities.
- Novel meal percentage.
- Takeout frequency.
- Dietary restrictions.
- Freeform guidance.

#### Meal Library

- Table or card list with filter by complexity, recurrence tier, tag, and source.
- Bulk fast-add widget.
- Inline edit for minimal friction.
- Tags should be visible but lightweight: freeform chips, not a heavily managed taxonomy.
- Offer a few suggested starter tags in the add and edit flows, but always allow arbitrary user-defined tags.

#### Weekly Planner

- Seven-day horizontal or vertical board depending on viewport.
- Drag and drop between days.
- Slot actions: reroll, manual replace, mark takeout, clear.
- Explanation affordance per slot.
- Chat panel docked beside or below the planner.
- After a day passes, offer a lightweight dismissible prompt to mark the meal as cooked or skipped.
- Also offer a weekly catch-up prompt when the user revisits the planner so outcome logging is encouraged without being required.

#### Discovery Acceptance

- Show title, why it fits, source URL, and minimal metadata.
- One-click accept into library and plan.

### Accessibility and Responsiveness

- Desktop first, mobile usable.
- Keyboard support for core actions.
- Drag and drop must have accessible fallback controls.

## Security and Privacy

- Passwords hashed with Argon2.
- Use secure HTTP-only cookies.
- CSRF protection for session-authenticated mutations.
- Rate limit login and chat endpoints.
- Tenant scoping at the query layer for every user-owned record.
- Secrets only via environment variables or Docker secrets later.
- Log enough for debugging, but never log raw passwords or secret tokens.

The email link is a convenience deep link, not a passwordless login mechanism in v1.

## Reliability and Failure Modes

- If scheduled generation is missed because the app is offline, user can generate the week manually with identical planner behavior.
- If Mailgun fails, the plan is still persisted and visible in the UI.
- If OpenRouter fails, planner falls back to deterministic-only mode and informs the user that explanations or discovery may be degraded.
- If discovery fails, reroll can still choose from local meals.

## Development Environment

### Local Development Posture

- Docker Compose for services.
- Python backend can also run in a local venv for fast iteration.
- Frontend runs in Vite dev server locally.

This is not a contradiction. The recommended developer workflow is:

- Run PostgreSQL via Compose.
- Run backend in a venv on the host during active backend work.
- Run frontend dev server on the host during UI work.
- Use full Compose when validating the integrated stack.

### Tooling

- Python:
  - FastAPI
  - SQLAlchemy 2.x
  - Alembic
  - Pydantic v2
  - pytest
  - ruff
  - pylint
- Frontend:
  - React
  - TypeScript
  - Vite
  - Vitest
  - Playwright or Cypress, with Playwright preferred
- Git hooks and automation:
  - pre-commit
  - GitHub Actions CI

### Quality Gates

- Ruff lint.
- Ruff format check.
- Pylint on backend package.
- pytest for backend unit and integration tests.
- Frontend typecheck.
- Frontend unit tests.
- Basic end-to-end smoke test.

## Deployment Plan

### Compose Services

- `postgres`
- `backend`
- `frontend` or static asset serving through backend

### Environment Variables

- `DATABASE_URL`
- `APP_SECRET_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `MAILGUN_API_KEY`
- `MAILGUN_DOMAIN`
- `MAIL_FROM_ADDRESS`
- `APP_BASE_URL`
- `SCHEDULER_ENABLED`

### Operations

- Run Alembic migrations at deploy time.
- Back up PostgreSQL volume.
- Use a reverse proxy with TLS in cloud deployment.
- Prefer one always-on VM in production.

## Testing Strategy

### Backend

- Unit tests for scoring and constraint logic.
- Integration tests for plan generation.
- Contract tests for schema-validated LLM responses.
- Auth tests for tenant isolation.
- Login redirect tests for `next` handling.
- Plan history tests to verify recent weeks affect scoring.
- Outcome-status tests to verify `cooked` and `skipped` feedback affect planner weights correctly.

### Frontend

- Component tests for planner interactions.
- End-to-end flows:
  - Login.
  - Fast-add meals.
  - Generate week.
  - Reroll one slot.
  - Drag and drop.
  - Chat change.
  - Mark a meal cooked or skipped.
  - Accept discovered meal.
  - Export CSV.

## Execution Plan by Phase

### Phase 0: Repository and Scaffolding

- Create backend and frontend app skeletons.
- Add Compose, env templates, and Makefile or task runner.
- Add pre-commit, lint, format, test, and CI config.
- Add base documentation.

### Phase 1: Core Domain and Auth

- Implement database schema and Alembic migrations.
- Implement user bootstrap CLI.
- Implement auth and user preferences.
- Implement tenant-safe data access patterns.
- Implement post-login redirect flow using `next`.

### Phase 2: Meal Library

- Implement meal CRUD.
- Implement fast-add UX and bulk endpoint.
- Implement lightweight tags with starter suggestions.
- Implement CSV export.

### Phase 3: Planner Core

- Implement deterministic scoring engine.
- Implement recurring rules and takeout handling.
- Implement weekly plan persistence, slot mutations, and historical-plan-aware scoring.
- Implement optional outcome tracking for `cooked` and `skipped` on historical slots.
- Implement planner explanations without LLM first.

### Phase 4: LLM and Discovery

- Add OpenRouter integration with structured outputs.
- Add discovery suggestions with source URLs.
- Add acceptance flow into library.

### Phase 5: Planner UI

- Build weekly planner screen.
- Add drag and drop and reroll controls.
- Add explanation surfaces.
- Add optional cooked versus skipped logging UX.

### Phase 6: Chat Edits and Email

- Add chat intent parsing and mutation pipeline.
- Add Mailgun integration.
- Add scheduled generation and email sending.

### Phase 7: Hardening

- Add last-action undo using audit log payloads.
- Improve failure handling.
- Add end-to-end tests.
- Add deployment docs.

## Agent Workstream Split

This split is intended for parallel execution by a team of agents.

### Agent A: Platform and Tooling

- Repo scaffolding.
- Compose.
- pre-commit.
- CI.
- Env handling.

### Agent B: Backend Domain

- SQLAlchemy models.
- Alembic migrations.
- Pydantic schemas.
- CRUD services.

### Agent C: Planner Engine

- Scoring model.
- Recurring rules.
- Plan generation.
- Reroll behavior.
- Historical repetition avoidance.
- Planned-history versus cooked/skipped outcome weighting.
- Undo payload definitions for last-action revert.

### Agent D: LLM and Discovery

- OpenRouter client.
- Prompt schemas.
- Response validation.
- Discovery adapters.

### Agent E: Frontend

- App shell.
- Auth pages.
- Meal library.
- Weekly planner UI.
- Chat panel.

### Agent F: Integration and Ops

- Mailgun integration.
- Scheduler.
- Deployment docs.
- E2E tests.

## Significant Risks and Mitigations

### Risk: LLM output becomes brittle

Mitigation:

- Keep planner core deterministic.
- Use strict schemas.
- Add fallback mode.

### Risk: Discovery quality is poor

Mitigation:

- Keep discovery contract provider-agnostic.
- Log accepted and rejected suggestions for future tuning.
- Start with user-visible explanation and explicit acceptance.

### Risk: Multi-user security regressions

Mitigation:

- Enforce user scoping in repository or service layer.
- Add tests for cross-user access.

### Risk: Chat mutations become unsafe

Mitigation:

- Use intent parsing to structured actions.
- Validate before mutation.
- Maintain undo log.

### Risk: Scheduler on intermittent laptop is unreliable

Mitigation:

- Keep manual generation as first-class behavior.
- Treat scheduled generation as convenience, not the sole path.

## Final Decisions and Handoff Notes

The previously open decisions below are now resolved:

1. Recipe discovery uses Tavily in v1.
2. Admin remains a hidden bootstrap capability for now.
3. Email links deep-link to the target plan and rely on normal login, with `next` redirect support.
4. Undo supports only the last action in v1.
5. Historical weekly plans are retained and used to reduce repetition. Archived meals still count in that history, but are not eligible future candidates while archived.
6. Tags are a lightweight visible feature in v1 with freeform entry and starter suggestions because they materially improve planner expressiveness, user organization, and chat/discovery quality.
7. Historical weeks always record what was planned. Users can optionally log whether a planned meal was actually `cooked` or `skipped` to improve recommendations and enable future analytics.
8. `Skipped` should lower confidence in the specific meal first, and only weakly influence adjacent tags or patterns after repeated same-context skips.
9. The app should prompt for cooked versus skipped logging in two lightweight ways: after a day passes and as a weekly catch-up prompt.

This document is implementation-ready for repository scaffolding and task decomposition.

## Recommended Immediate Next Step

Build the repository scaffold and backend schema first. The planner quality, chat safety, and frontend complexity all depend on having a stable domain model and API contract early.