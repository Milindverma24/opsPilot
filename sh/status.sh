#!/usr/bin/env bash
# ==============================================================================
# OpsPilot — Service Status & Health Inspector
# Inspects running processes, ports, API health, and database metrics
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}==================================================================${RESET}"
echo -e "${BOLD}${CYAN}               OpsPilot — System Health & Status                  ${RESET}"
echo -e "${BOLD}${CYAN}==================================================================${RESET}"

# 1. Check FastAPI Backend (:8000)
echo -e "${BOLD}FastAPI Backend (Port 8000):${RESET}"
API_PID=$(lsof -i :8000 -sTCP:LISTEN -t 2>/dev/null | head -n 1 || echo "")
if [ -n "$API_PID" ]; then
    HEALTH_RESP=$(curl -s http://localhost:8000/health 2>/dev/null || echo "UNRESPONSIVE")
    echo -e "  • Status:     ${GREEN}● ONLINE${RESET} (PID: $API_PID)"
    echo -e "  • Health:     ${GREEN}$HEALTH_RESP${RESET}"
    echo -e "  • Swagger UI: ${CYAN}http://localhost:8000/docs${RESET}"
else
    echo -e "  • Status:     ${RED}○ OFFLINE${RESET}"
fi

echo ""

# 2. Check Next.js Frontend (:3000)
echo -e "${BOLD}Next.js Frontend (Port 3000):${RESET}"
WEB_PID=$(lsof -i :3000 -sTCP:LISTEN -t 2>/dev/null | head -n 1 || echo "")
if [ -n "$WEB_PID" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    echo -e "  • Status:     ${GREEN}● ONLINE${RESET} (PID: $WEB_PID)"
    echo -e "  • HTTP Code:  ${GREEN}$HTTP_CODE OK${RESET}"
    echo -e "  • Dashboard:  ${CYAN}http://localhost:3000${RESET}"
else
    echo -e "  • Status:     ${RED}○ OFFLINE${RESET}"
fi

echo ""

# 3. Check Database
echo -e "${BOLD}Local Database (opspilot.db):${RESET}"
if [ -f "opspilot.db" ]; then
    DB_SIZE=$(du -h opspilot.db | awk '{print $1}')
    echo -e "  • File Size:  $DB_SIZE"
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python -c "
from apps.api.app.core.database import SessionLocal
from apps.api.app.models import User, Product, Order, Task, Agent
try:
    db = SessionLocal()
    print(f'  • Metrics:    {db.query(User).count()} users | {db.query(Product).count()} products | {db.query(Order).count()} orders | {db.query(Agent).count()} agents')
    db.close()
except Exception as e:
    print(f'  • Metrics:    (Unable to read metrics: {e})')
" 2>/dev/null || echo "  • Metrics:    Unable to query"
    fi
else
    echo -e "  • Status:     ${YELLOW}opspilot.db not found (run ./sh/restore.sh to seed)${RESET}"
fi

echo ""

# 4. Logs summary
echo -e "${BOLD}Log Files:${RESET}"
for logf in "storage/logs/api.log" "storage/logs/web.log"; do
    if [ -f "$logf" ]; then
        L_SIZE=$(du -h "$logf" | awk '{print $1}')
        echo -e "  • $logf (${L_SIZE})"
    fi
done

echo -e "${BOLD}${CYAN}==================================================================${RESET}"
