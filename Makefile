.PHONY: help up down restart logs status migrate seed knowledge test test-ai test-security test-e2e test-all demo clean lint run-api run-web run-worker start stop restore

help:
	@echo "=================================================================="
	@echo "OpsPilot — Local Autonomous Business Operations Agent"
	@echo "Company: UrbanThread (Synthetic Fashion / Clothing E-Commerce)"
	@echo "=================================================================="
	@echo ""
	@echo "One-Command Shell Automation (sh/):"
	@echo "  make start          Start all services (FastAPI + Next.js web)"
	@echo "  make stop           Stop all services and free ports"
	@echo "  make restart        Restart all services gracefully"
	@echo "  make restore        Backup and restore/re-seed demo database"
	@echo "  make status         Inspect service health, telemetry, and ports"
	@echo ""
	@echo "Local Infrastructure & Lifecycle Commands:"
	@echo "  make up             Start Docker Compose stack"
	@echo "  make down           Stop Docker Compose stack"
	@echo "  make logs           Follow local container or process logs"
	@echo "  make clean          Clean temporary files, caches, and test artifacts"
	@echo ""
	@echo "Database & Knowledge Initialization:"
	@echo "  make migrate        Run database migrations (Alembic / SQLite init)"
	@echo "  make seed           Seed UrbanThread demo data (users, catalog, inventory)"
	@echo "  make knowledge      Ingest knowledge base, SOPs, and policies into RAG"
	@echo ""
	@echo "Automated Test Lab & Validation:"
	@echo "  make test           Run unit, integration, and API test suites"
	@echo "  make test-ai        Run AI evaluation benchmarks (200+ cases)"
	@echo "  make test-security  Run security, prompt injection, and multi-tenant tests"
	@echo "  make test-e2e       Run end-to-end customer AI and order flow tests"
	@echo "  make test-all       Run complete comprehensive test lab suite"
	@echo "  make lint           Check code quality and type safety"
	@echo ""
	@echo "Demonstration Scenarios:"
	@echo "  make demo           One-command startup, seeding, and demo scenario run"
	@echo "=================================================================="

start:
	./sh/start.sh

stop:
	./sh/stop.sh

restart:
	./sh/restart.sh

restore:
	./sh/restore.sh

status:
	./sh/status.sh

up:
	docker compose up -d

down:
	docker compose down

migrate:
	.venv/bin/python -c "from apps.api.app.core.database_init import init_db; init_db()"

seed:
	.venv/bin/python scripts/seed_urbanthread_demo.py

knowledge:
	.venv/bin/python scripts/seed_synthetic_documents.py
	.venv/bin/python scripts/seed_synthetic_website.py

test:
	PYTHONPATH=. .venv/bin/pytest tests/unit apps/api/tests -v

test-ai:
	PYTHONPATH=. .venv/bin/pytest tests/ai -v
	PYTHONPATH=. .venv/bin/python scripts/evaluate_ai.py

test-security:
	PYTHONPATH=. .venv/bin/pytest tests/security -v

test-e2e:
	PYTHONPATH=. .venv/bin/pytest tests/e2e -v

test-all: test test-ai test-security test-e2e
	@echo "All test lab suites passed successfully."

demo: migrate seed knowledge
	@echo "UrbanThread OpsPilot demo environment initialized."
	.venv/bin/python scripts/run_demo_scenarios.py

clean:
	rm -rf .pytest_cache
	rm -rf apps/api/.pytest_cache
	rm -rf tests/**/__pycache__
	rm -rf apps/**/__pycache__
	rm -rf storage/temp/*
	@echo "Cleaned temporary files and caches."

lint:
	.venv/bin/ruff check apps/api tests || true
	cd apps/web && npm run lint || true

run-api:
	.venv/bin/uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload

run-web:
	cd apps/web && npm run dev

run-worker:
	.venv/bin/celery -A apps.api.app.core.celery_app worker --loglevel=info

n8n-up:
	docker compose -f docker-compose.n8n.yml up -d
	@echo "n8n started at http://localhost:5678"

n8n-down:
	docker compose -f docker-compose.n8n.yml down
