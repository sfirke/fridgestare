.PHONY: backend-install backend-dev backend-test backend-lint frontend-install frontend-dev \
	frontend-lint frontend-test frontend-typecheck frontend-build compose-up compose-down check

backend-install:
	cd backend && pip install -e .[dev]

backend-dev:
	cd backend && uvicorn app.main:app --reload

backend-test:
	cd backend && pytest

backend-lint:
	cd backend && ruff check . && ruff format --check . && pylint app

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-lint:
	cd frontend && npm run lint

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-test:
	cd frontend && npm run test -- --run

frontend-build:
	cd frontend && npm run build

# Everything CI runs, in one command.
check: backend-lint backend-test frontend-lint frontend-typecheck frontend-test frontend-build

compose-up:
	docker compose up --build

compose-down:
	docker compose down
