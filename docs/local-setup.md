# Local Setup Guide — OpsPilot

This guide explains how to install, configure, run, and validate **OpsPilot** on your local machine with **zero cloud dependencies**.

---

## 1. Prerequisites

- **macOS / Linux / WSL2**
- **Python 3.12+**
- **Node.js 18+ (Node 20+ recommended)**
- **Docker & Docker Compose** (Optional, for running PostgreSQL/Redis locally)
- **Make** (`make` command line utility)

---

## 2. One-Command Setup

OpsPilot provides helper targets in the [Makefile](file:///Users/milindverma/Desktop/opsPilot/Makefile):

```bash
# 1. Clone repository
git clone https://github.com/Milindverma24/opsPilot.git
cd opsPilot

# 2. Complete setup and seed demonstration data
make seed
```

This command:
1. Installs Python and Node.js dependencies.
2. Initializes the local SQLite/PostgreSQL schema.
3. Seeds UrbanThread organization, departments, users, inventory, and AI employees.
4. Generates synthetic evaluation and security test datasets.

---

## 3. Running Locally (Direct Process Mode)

To start both the FastAPI backend and Next.js frontend without Docker:

```bash
# Terminal 1 — Start FastAPI API Backend (Port 8000)
make run-api

# Terminal 2 — Start Next.js Frontend Web App (Port 3000)
make run-web

# Terminal 3 (Optional) — Start Celery Background Worker
make run-worker
```

### URLs
- **Web Dashboard**: [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 4. Running via Local Docker Infrastructure

If you prefer running services inside local containers:

```bash
# Start all local containers (Postgres, Redis, API, Web, Worker, Scheduler)
make up

# View logs
make logs

# Stop containers
make down
```

---

## 5. Configuration (`.env`)

The application starts 100% locally with zero external API keys. Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Key environment configuration variables:
```ini
APP_ENV=development
DEMO_MODE=true

# Database & Cache (Local)
DATABASE_URL=sqlite:///./opspilot.db
REDIS_URL=redis://localhost:6379/0

# Autonomous Workforce Settings
AI_WORKFORCE_ENABLED=true
AUTOMATED_ACTIONS_ENABLED=true
HIGH_RISK_ACTIONS_ENABLED=true
CELERY_ALWAYS_EAGER=True

# Zero Cloud Mock Integrations
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=mock
PAYMENT_PROVIDER=mock
SHIPPING_PROVIDER=mock
EMAIL_PROVIDER=mock
```

---

## 6. Demo Credentials

| Role | Email | Password | Primary Functions |
|---|---|---|---|
| **UrbanThread Admin** | `admin@urbanthread.local` | `DemoPassword123!` | System configuration, Kill Switch, Full Admin |
| **Warehouse Employee** | `warehouse@acme.test` | `DemoPassword123!` | Pick & Pack Task Dispatcher (`/employee/tasks`) |
| **Finance Manager** | `finance@urbanthread.local` | `DemoPassword123!` | High-Risk Refund Approvals (> ₹2,000) |
| **Customer Support** | `support@urbanthread.local` | `DemoPassword123!` | Tickets & Customer Inquiries |
