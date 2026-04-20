.PHONY: dev-backend dev-frontend dev test lint format generate-data docker-up docker-down clean

dev-backend: ## Start backend with auto-reload
	cd backend && uvicorn main:app --reload --port 8000

dev-frontend: ## Start frontend dev server
	cd frontend && npm run dev

dev: ## Start both backend and frontend
	make dev-backend & make dev-frontend

test: ## Run backend tests
	cd backend && python -m pytest tests/ -v

lint: ## Check code style
	cd backend && ruff check .
	cd backend && ruff format --check .

format: ## Auto-format code
	cd backend && ruff format .

generate-data: ## Generate synthetic wells and time series
	cd backend && python -m data_generator.generate_wells
	cd backend && python -m data_generator.generate_timeseries

docker-up: ## Start all services via Docker Compose
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

e2e: ## Run Playwright E2E tests
	cd frontend && npx playwright test

e2e-ui: ## Run Playwright E2E tests with UI
	cd frontend && npx playwright test --ui

clean: ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
