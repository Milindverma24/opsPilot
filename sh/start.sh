#!/usr/bin/env bash
# ==============================================================================
# OpsPilot — Service Start Script
# Starts FastAPI Backend (:8000) and Next.js Web Frontend (:3000)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

# Directories for runtime artifacts
mkdir -p storage/logs
mkdir -p storage/pids
mkdir -p storage/backups

API_LOG="storage/logs/api.log"
WEB_LOG="storage/logs/web.log"
SPRING_LOG="storage/logs/spring-rag.log"
API_PID_FILE="storage/pids/api.pid"
WEB_PID_FILE="storage/pids/web.pid"
SPRING_PID_FILE="storage/pids/spring-rag.pid"

echo -e "${BOLD}${CYAN}==================================================================${RESET}"
echo -e "${BOLD}${CYAN}              OpsPilot — Starting System Services                 ${RESET}"
echo -e "${BOLD}${CYAN}==================================================================${RESET}"

# 1. Environment & Prerequisites Check
if [ ! -f ".venv/bin/python" ]; then
    echo -e "${RED}[ERROR] Python virtual environment (.venv) not found at $PROJECT_ROOT/.venv${RESET}"
    echo "Please create the virtual environment first:"
    echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

if ! command -v npm &>/dev/null; then
    echo -e "${RED}[ERROR] npm command not found. Please install Node.js (v18+).${RESET}"
    exit 1
fi

# Ensure database exists; if not, initialize and seed
if [ ! -f "opspilot.db" ]; then
    echo -e "${YELLOW}[!] Database opspilot.db not detected. Initializing & seeding demo data...${RESET}"
    .venv/bin/python scripts/seed_urbanthread_demo.py
    .venv/bin/python scripts/seed_synthetic_documents.py
    .venv/bin/python scripts/seed_synthetic_website.py
fi

# 2. Check Port 8000 (FastAPI Backend)
if lsof -i :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    EXISTING_API_PID=$(lsof -i :8000 -sTCP:LISTEN -t | head -n 1)
    echo -e "${YELLOW}[i] Port 8000 is already active (PID: $EXISTING_API_PID). FastAPI backend appears to be running.${RESET}"
    echo "$EXISTING_API_PID" > "$API_PID_FILE"
else
    echo -e "${CYAN}[1/2] Starting FastAPI Backend (Port 8000)...${RESET}"
    python3 -c "
import subprocess
with open('$PROJECT_ROOT/$API_LOG', 'a') as log_f:
    proc = subprocess.Popen(
        ['$PROJECT_ROOT/.venv/bin/uvicorn', 'apps.api.app.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'],
        cwd='$PROJECT_ROOT',
        stdin=subprocess.DEVNULL,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    with open('$PROJECT_ROOT/$API_PID_FILE', 'w') as pid_f:
        pid_f.write(str(proc.pid))
"
    API_PID=$(cat "$API_PID_FILE" 2>/dev/null || echo "")
    echo -e "      Spawned process PID: ${BOLD}$API_PID${RESET} (Logs: $API_LOG)"
fi

# Wait for FastAPI health endpoint
echo -n "      Waiting for FastAPI to become healthy"
MAX_ATTEMPTS=25
ATTEMPT=0
API_READY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
        API_READY=true
        break
    fi
    echo -n "."
    sleep 0.8
    ATTEMPT=$((ATTEMPT + 1))
done
echo ""

if [ "$API_READY" = true ]; then
    echo -e "      ${GREEN}✔ FastAPI Backend is ready at http://localhost:8000${RESET}"
else
    echo -e "      ${RED}✖ Failed to verify FastAPI health within timeout. Check $API_LOG for details.${RESET}"
    tail -n 20 "$API_LOG"
    exit 1
fi

# 3. Check Port 3000 (Next.js Web App)
if lsof -i :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    EXISTING_WEB_PID=$(lsof -i :3000 -sTCP:LISTEN -t | head -n 1)
    echo -e "${YELLOW}[i] Port 3000 is already active (PID: $EXISTING_WEB_PID). Next.js web app appears to be running.${RESET}"
    echo "$EXISTING_WEB_PID" > "$WEB_PID_FILE"
else
    echo -e "${CYAN}[2/2] Starting Next.js Frontend (Port 3000)...${RESET}"
    python3 -c "
import subprocess
with open('$PROJECT_ROOT/$WEB_LOG', 'a') as log_f:
    proc = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd='$PROJECT_ROOT/apps/web',
        stdin=subprocess.DEVNULL,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    with open('$PROJECT_ROOT/$WEB_PID_FILE', 'w') as pid_f:
        pid_f.write(str(proc.pid))
"
    WEB_PID=$(cat "$WEB_PID_FILE" 2>/dev/null || echo "")
    echo -e "      Spawned process PID: ${BOLD}$WEB_PID${RESET} (Logs: $WEB_LOG)"
fi

# Wait for Web App
echo -n "      Waiting for Next.js Web App to respond"
ATTEMPT=0
WEB_READY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -I http://localhost:3000 >/dev/null 2>&1; then
        WEB_READY=true
        break
    fi
    echo -n "."
    sleep 0.8
    ATTEMPT=$((ATTEMPT + 1))
done
echo ""

if [ "$WEB_READY" = true ]; then
    echo -e "      ${GREEN}✔ Next.js Frontend is ready at http://localhost:3000${RESET}"
else
    echo -e "      ${YELLOW}[!] Next.js is compiling in background. It will be available shortly at http://localhost:3000${RESET}"
fi

# 4. Optional: Spring RAG microservice if requested via flag
if [[ "$*" == *"--with-spring-rag"* ]]; then
    if [ -f "apps/spring-rag/target/spring-rag-1.0.0.jar" ]; then
        if lsof -i :8081 -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${YELLOW}[i] Port 8081 is already active. Spring RAG appears to be running.${RESET}"
        else
            echo -e "${CYAN}[+] Starting Spring RAG Microservice (Port 8081)...${RESET}"
            nohup java -jar apps/spring-rag/target/spring-rag-1.0.0.jar > "$SPRING_LOG" 2>&1 &
            SPRING_PID=$!
            echo "$SPRING_PID" > "$SPRING_PID_FILE"
            echo -e "      Spawned Spring RAG PID: ${BOLD}$SPRING_PID${RESET} (Logs: $SPRING_LOG)"
        fi
    else
        echo -e "${YELLOW}[!] apps/spring-rag/target/spring-rag-1.0.0.jar not found. Skipping Spring RAG.${RESET}"
    fi
fi

echo ""
echo -e "${BOLD}${GREEN}==================================================================${RESET}"
echo -e "${BOLD}${GREEN}           🎉 OpsPilot Services Successfully Started!             ${RESET}"
echo -e "${BOLD}${GREEN}==================================================================${RESET}"
echo ""
echo -e "  ${BOLD}Web Dashboard:${RESET}             ${CYAN}http://localhost:3000${RESET}"
echo -e "  ${BOLD}Warehouse Dispatcher:${RESET}      ${CYAN}http://localhost:3000/employee/tasks${RESET}"
echo -e "  ${BOLD}AI Simulation Test Lab:${RESET}    ${CYAN}http://localhost:3000/ai/test-lab${RESET}"
echo -e "  ${BOLD}Tool Controls & Circuit:${RESET}   ${CYAN}http://localhost:3000/settings/tools${RESET}"
echo -e "  ${BOLD}FastAPI Swagger Docs:${RESET}      ${CYAN}http://localhost:8000/docs${RESET}"
echo -e "  ${BOLD}API Health Check:${RESET}          ${CYAN}http://localhost:8000/health${RESET}"
echo ""
echo -e "  ${BOLD}Demo Credentials:${RESET}"
echo -e "    • Admin:           ${GREEN}admin@urbanthread.local${RESET} / ${YELLOW}DemoPassword123!${RESET}"
echo -e "    • Warehouse Staff: ${GREEN}warehouse@acme.test${RESET}     / ${YELLOW}DemoPassword123!${RESET}"
echo -e "    • Finance Lead:    ${GREEN}finance@urbanthread.local${RESET} / ${YELLOW}DemoPassword123!${RESET}"
echo ""
echo -e "  ${BOLD}Management Commands:${RESET}"
echo -e "    • Stop:            ${CYAN}./sh/stop.sh${RESET}"
echo -e "    • Restart:         ${CYAN}./sh/restart.sh${RESET}"
echo -e "    • Restore DB:      ${CYAN}./sh/restore.sh${RESET}"
echo -e "    • Status:          ${CYAN}./sh/status.sh${RESET}"
echo -e "${BOLD}${GREEN}==================================================================${RESET}"
