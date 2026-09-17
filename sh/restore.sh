#!/usr/bin/env bash
# ==============================================================================
# OpsPilot — Database & Environment Restore Script
# Restores database from a backup file OR re-seeds fresh UrbanThread demo data
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

mkdir -p storage/backups

echo -e "${BOLD}${CYAN}==================================================================${RESET}"
echo -e "${BOLD}${CYAN}             OpsPilot — Database Restore & Seeder                 ${RESET}"
echo -e "${BOLD}${CYAN}==================================================================${RESET}"

if [ ! -f ".venv/bin/python" ]; then
    echo -e "${RED}[ERROR] Python virtual environment (.venv) not found at $PROJECT_ROOT/.venv${RESET}"
    exit 1
fi

# Detect if services were running
WAS_RUNNING=false
if lsof -i :8000 -sTCP:LISTEN -t >/dev/null 2>&1 || lsof -i :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    WAS_RUNNING=true
    echo -e "${YELLOW}[i] Running services detected. Stopping temporarily for database restore...${RESET}"
    "$SCRIPT_DIR/stop.sh"
    echo ""
fi

BACKUP_SOURCE="$1"

if [ -n "$BACKUP_SOURCE" ] && [ -f "$BACKUP_SOURCE" ]; then
    echo -e "${CYAN}[1/3] Restoring from provided backup file:${RESET} ${BOLD}$BACKUP_SOURCE${RESET}"
    if [ -f "opspilot.db" ]; then
        PRE_RESTORE_BACKUP="storage/backups/opspilot_pre_restore_$(date +%Y%m%d_%H%M%S).db.bak"
        cp "opspilot.db" "$PRE_RESTORE_BACKUP"
        echo -e "      Current database safely archived to: $PRE_RESTORE_BACKUP"
    fi
    cp "$BACKUP_SOURCE" "opspilot.db"
    echo -e "      ${GREEN}✔ Backup file restored to opspilot.db${RESET}"

    echo -e "${CYAN}[2/3] Running startup recovery watchdog...${RESET}"
    .venv/bin/python -c "
from apps.api.app.core.database import SessionLocal
from apps.api.app.services.recovery_manager import RecoveryManager
db = SessionLocal()
RecoveryManager.run_startup_recovery(db)
db.close()
"
    echo -e "      ${GREEN}✔ Recovery watchdog complete${RESET}"

else
    echo -e "${CYAN}[1/4] Backing up current database...${RESET}"
    if [ -f "opspilot.db" ]; then
        AUTO_BACKUP="storage/backups/opspilot_backup_$(date +%Y%m%d_%H%M%S).db.bak"
        cp "opspilot.db" "$AUTO_BACKUP"
        echo -e "      Archived existing database to: ${BOLD}$AUTO_BACKUP${RESET}"
        rm -f "opspilot.db"
    fi

    echo -e "${CYAN}[2/4] Seeding core platform, organizations, and e-commerce...${RESET}"
    .venv/bin/python scripts/seed.py

    echo -e "${CYAN}[3/4] Seeding UrbanThread demo workforce & warehouse tasks...${RESET}"
    .venv/bin/python scripts/seed_urbanthread_demo.py

    echo -e "${CYAN}[4/4] Running recovery watchdog for leases & task queues...${RESET}"
    .venv/bin/python -c "
from apps.api.app.core.database import SessionLocal
from apps.api.app.services.recovery_manager import RecoveryManager
db = SessionLocal()
RecoveryManager.run_startup_recovery(db)
db.close()
"
fi

# Print telemetry summary
echo ""
echo -e "${BOLD}${CYAN}Database Telemetry:${RESET}"
.venv/bin/python -c "
from apps.api.app.core.database import SessionLocal
from apps.api.app.models import User, Product, Order, Task, Agent
db = SessionLocal()
print(f'  • Active Users:     {db.query(User).count()}')
print(f'  • Catalog Products: {db.query(Product).count()}')
print(f'  • Seeded Orders:    {db.query(Order).count()}')
print(f'  • Warehouse Tasks:  {db.query(Task).count()}')
print(f'  • AI Employees:     {db.query(Agent).count()}')
db.close()
"

echo ""
echo -e "${BOLD}${GREEN}✔ Database restore & seeding completed successfully!${RESET}"

# Restart services if they were running before restore
if [ "$WAS_RUNNING" = true ]; then
    echo ""
    echo -e "${CYAN}Restarting previously running services...${RESET}"
    "$SCRIPT_DIR/start.sh"
fi
