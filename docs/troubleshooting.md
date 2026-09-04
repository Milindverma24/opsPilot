# Troubleshooting Guide — OpsPilot

This guide resolves common local setup, port conflict, and worker recovery issues.

---

## 1. Port Conflicts

### Port 8000 (FastAPI) Already In Use
```bash
lsof -i :8000
kill -9 <PID>
# Restart API
make run-api
```

### Port 3000 (Next.js) Already In Use
```bash
lsof -i :3000
kill -9 <PID>
# Restart Web App
make run-web
```

---

## 2. Worker Crash or Frozen Task

If a worker crashed mid-operation and a task appears stuck in `CLAIMED` status:
1. Open [http://localhost:3000/employee/tasks](http://localhost:3000/employee/tasks).
2. Click **"Recover Stale Leases"** in the top banner.
3. Or invoke the CLI watchdog:
```bash
.venv/bin/python -c "
from apps.api.app.core.database import SessionLocal
from apps.api.app.services.recovery_manager import RecoveryManager
db = SessionLocal()
RecoveryManager.run_startup_recovery(db)
db.close()
"
```
The watchdog will immediately identify tasks with expired leases and restore them to `CREATED` status without duplicate mutations.

---

## 3. Resetting Local Database

To wipe and reseed the local SQLite database from scratch:
```bash
make clean
make seed
```
This re-creates `opspilot.db` and populates all UrbanThread products, inventory, departments, and AI agents.
