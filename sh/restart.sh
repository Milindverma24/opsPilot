#!/usr/bin/env bash
# ==============================================================================
# OpsPilot — Service Restart Script
# Gracefully stops all services, waits for socket teardown, and starts anew
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

BOLD="\033[1m"
CYAN="\033[0;36m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}==================================================================${RESET}"
echo -e "${BOLD}${CYAN}              OpsPilot — Restarting System Services               ${RESET}"
echo -e "${BOLD}${CYAN}==================================================================${RESET}"

"$SCRIPT_DIR/stop.sh"

echo ""
echo -e "${CYAN}Waiting 2 seconds before restart...${RESET}"
sleep 2

"$SCRIPT_DIR/start.sh" "$@"
