# OpsPilot Shell Management Scripts (`sh/`)

This directory contains standalone, zero-dependency shell scripts for managing the lifecycle of the **OpsPilot** autonomous business operations platform.

All scripts can be executed from the project root or from inside the `sh/` directory.

---

## 📋 Script Reference

### 1. `sh/start.sh` — Start All Services
Starts both the **FastAPI backend** (:8000) and **Next.js web application** (:3000) in the background, waits for health checks to pass, and prints the live URLs and demo credentials.

```bash
# Standard start
./sh/start.sh

# Optional: Start with Spring RAG microservice on port 8081
./sh/start.sh --with-spring-rag
```

- **API Logs**: `storage/logs/api.log`
- **Web Logs**: `storage/logs/web.log`
- **PID Files**: `storage/pids/`

---

### 2. `sh/stop.sh` — Stop All Services
Gracefully terminates backend, frontend, celery workers, and any lingering processes on ports 8000, 3000, and 8081.

```bash
./sh/stop.sh
```

---

### 3. `sh/restart.sh` — Restart All Services
Invokes `stop.sh`, waits for port sockets to clear, and starts fresh with `start.sh`.

```bash
./sh/restart.sh
```

---

### 4. `sh/restore.sh` — Restore & Re-Seed Database
Handles full database recovery and seeding:
1. **From Backup**: Pass an existing backup file to restore directly:
   ```bash
   ./sh/restore.sh storage/backups/opspilot_backup_20260917_023000.db.bak
   ```
2. **Fresh Re-Seed**: Running with no arguments archives current data to `storage/backups/`, wipes `opspilot.db`, and regenerates all UrbanThread catalog, inventory, users, workflows, tasks, and knowledge SOPs:
   ```bash
   ./sh/restore.sh
   ```

If services were running before `restore.sh` was invoked, they are automatically stopped during the restore and restarted upon completion.

---

### 5. `sh/status.sh` — System Health & Telemetry
Inspects running processes, open ports, health endpoints, database row counts, and log file sizes.

```bash
./sh/status.sh
```

---

## 🔑 Demo Login Credentials

| Role | Email | Password | Primary Functions |
|---|---|---|---|
| **Admin** | `admin@urbanthread.local` | `DemoPassword123!` | System configuration, Kill Switch, Full Admin |
| **Warehouse Staff** | `warehouse@acme.test` | `DemoPassword123!` | Pick & Pack Task Dispatcher (`/employee/tasks`) |
| **Finance Lead** | `finance@urbanthread.local` | `DemoPassword123!` | High-Risk Refund Approvals (> ₹2,000) |
| **Customer Support** | `support@urbanthread.local` | `DemoPassword123!` | Tickets & Customer Inquiries |
