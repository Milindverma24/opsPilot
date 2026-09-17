#!/usr/bin/env bash
# ==============================================================================
# OpsPilot — Service Stop Script
# Stops FastAPI Backend (:8000), Next.js Frontend (:3000), and related daemons
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

echo -e "${BOLD}${CYAN}==================================================================${RESET}"
echo -e "${BOLD}${CYAN}               OpsPilot — Stopping System Services                ${RESET}"
echo -e "${BOLD}${CYAN}==================================================================${RESET}"

stop_pid() {
    local name="$1"
    local pid_file="$2"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file" 2>/dev/null || echo "")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}[-] Stopping $name (PID: $pid)...${RESET}"
            kill -15 "$pid" 2>/dev/null || true
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${RED}[!] Force killing $name (PID: $pid)...${RESET}"
                kill -9 "$pid" 2>/dev/null || true
            fi
            echo -e "    ${GREEN}✔ $name stopped${RESET}"
        fi
        rm -f "$pid_file"
    fi
}

stop_port() {
    local name="$1"
    local port="$2"
    local pids
    pids=$(lsof -i :"$port" -sTCP:LISTEN -t 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}[-] Cleaning up process(es) on port $port ($name)...${RESET}"
        for p in $pids; do
            echo -e "    Killing PID $p on port $port..."
            kill -15 "$p" 2>/dev/null || true
            sleep 0.5
            if kill -0 "$p" 2>/dev/null; then
                kill -9 "$p" 2>/dev/null || true
            fi
        done
        echo -e "    ${GREEN}✔ Port $port freed${RESET}"
    fi
}

# 1. Stop via PID files
stop_pid "FastAPI Backend" "storage/pids/api.pid"
stop_pid "Next.js Frontend" "storage/pids/web.pid"
stop_pid "Spring RAG" "storage/pids/spring-rag.pid"

# 2. Stop any remaining processes bound to ports 8000, 3000, 8081
stop_port "FastAPI Backend (:8000)" 8000
stop_port "Next.js Frontend (:3000)" 3000
stop_port "Spring RAG (:8081)" 8081

# 3. Stop Celery workers if running
CELERY_PIDS=$(pgrep -f "celery -A apps.api.app.core.celery_app" 2>/dev/null || true)
if [ -n "$CELERY_PIDS" ]; then
    echo -e "${YELLOW}[-] Stopping Celery worker processes...${RESET}"
    for cp in $CELERY_PIDS; do
        kill -15 "$cp" 2>/dev/null || true
    done
    echo -e "    ${GREEN}✔ Celery workers stopped${RESET}"
fi

echo ""
echo -e "${BOLD}${GREEN}✔ All OpsPilot services successfully stopped.${RESET}"
echo -e "${BOLD}${CYAN}==================================================================${RESET}"
