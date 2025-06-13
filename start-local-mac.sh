#!/bin/bash

# Lapis LLMT Spider - Local Development Starter for macOS
# This script starts all services needed for local development

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo -e "${BLUE}🚀 Starting Lapis LLMT Spider Local Development${NC}"
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3.12 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
else
    echo -e "${GREEN}✅ Virtual environment found${NC}"
fi

# Function to check if service is running
check_service() {
    if brew services list | grep -q "$1.*started"; then
        echo -e "${GREEN}✅ $1 is running${NC}"
    else
        echo -e "${YELLOW}⚠️  $1 is not running. Starting...${NC}"
        brew services start $1
    fi
}

# Check required services
echo -e "\n${BLUE}Checking required services...${NC}"
check_service "postgresql@15"
check_service "mongodb-community"
check_service "redis"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}⚠️  .env file not found. Creating from example...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Please update .env with your API keys and database credentials${NC}"
    exit 1
fi

# Function to run command in new terminal tab
run_in_new_tab() {
    local name=$1
    local command=$2
    
    osascript <<EOF
    tell application "Terminal"
        tell application "System Events" to keystroke "t" using command down
        delay 0.5
        do script "cd $PROJECT_DIR && source venv/bin/activate && $command" in front window
        set custom title of front window to "$name"
    end tell
EOF
}

# Start services in new terminal tabs
echo -e "\n${BLUE}Starting services in new Terminal tabs...${NC}"

# Start FastAPI
echo -e "${YELLOW}Starting FastAPI backend...${NC}"
run_in_new_tab "Lapis API" "uvicorn src.main:app --reload --host 0.0.0.0 --port 8080"

# Wait a bit for API to start
sleep 3

# Start Celery Worker
echo -e "${YELLOW}Starting Celery worker...${NC}"
run_in_new_tab "Celery Worker" "celery -A src.celery worker --loglevel=info"

# Start Celery Beat
echo -e "${YELLOW}Starting Celery beat...${NC}"
run_in_new_tab "Celery Beat" "celery -A src.celery beat --loglevel=info"

# Start Flower (optional)
echo -e "${YELLOW}Starting Flower (Celery monitoring)...${NC}"
run_in_new_tab "Flower" "celery -A src.celery flower --port=5555"

# Start Frontend
echo -e "${YELLOW}Starting Next.js frontend...${NC}"
osascript <<EOF
tell application "Terminal"
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "cd $PROJECT_DIR/lapis-frontend && npm install && npm run dev" in front window
    set custom title of front window to "Lapis Frontend"
end tell
EOF

echo -e "\n${GREEN}✅ All services starting!${NC}"
echo "========================================="
echo -e "${BLUE}Service URLs:${NC}"
echo "  • API Backend: http://localhost:8080"
echo "  • API Docs: http://localhost:8080/docs"
echo "  • Frontend: http://localhost:3000"
echo "  • Flower (Celery): http://localhost:5555"
echo ""
echo -e "${BLUE}Default Login:${NC}"
echo "  • Email: admin@example.com"
echo "  • Password: Admin123!"
echo ""
echo -e "${YELLOW}Tips:${NC}"
echo "  • Check each Terminal tab for service logs"
echo "  • Use Ctrl+C to stop a service"
echo "  • Run 'brew services list' to check databases"
echo ""
echo -e "${GREEN}Happy crawling! 🕷️${NC}"

# Keep this terminal open for monitoring
echo -e "\n${BLUE}This terminal will monitor the services...${NC}"
echo "Press Ctrl+C to stop monitoring (services will continue running)"

# Simple monitoring loop
while true; do
    sleep 5
    # Check if API is responding
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        printf "\r${GREEN}[$(date '+%H:%M:%S')] API: ✅  ${NC}"
    else
        printf "\r${RED}[$(date '+%H:%M:%S')] API: ❌  ${NC}"
    fi
done