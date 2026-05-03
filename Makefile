.PHONY: backend-install backend-dev backend-test backend-lint frontend-install frontend-dev frontend-test frontend-build compose-up compose-down

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

frontend-test:
	cd frontend && npm run test

frontend-build:
	cd frontend && npm run build

compose-up:
	docker compose up --build

compose-down:
	docker compose down
