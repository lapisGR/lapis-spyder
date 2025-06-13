#!/bin/bash

# Lapis LLMT Spider - Stop Local Development Services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Lapis LLMT Spider Services${NC}"
echo "========================================="

# Kill Python processes
echo -e "${YELLOW}Stopping Python services...${NC}"

# Kill Uvicorn
if pgrep -f "uvicorn src.main:app" > /dev/null; then
    pkill -f "uvicorn src.main:app"
    echo -e "${GREEN}✅ Stopped FastAPI server${NC}"
else
    echo -e "${BLUE}ℹ️  FastAPI server not running${NC}"
fi

# Kill Celery Worker
if pgrep -f "celery.*worker" > /dev/null; then
    pkill -f "celery.*worker"
    echo -e "${GREEN}✅ Stopped Celery worker${NC}"
else
    echo -e "${BLUE}ℹ️  Celery worker not running${NC}"
fi

# Kill Celery Beat
if pgrep -f "celery.*beat" > /dev/null; then
    pkill -f "celery.*beat"
    echo -e "${GREEN}✅ Stopped Celery beat${NC}"
else
    echo -e "${BLUE}ℹ️  Celery beat not running${NC}"
fi

# Kill Flower
if pgrep -f "celery.*flower" > /dev/null; then
    pkill -f "celery.*flower"
    echo -e "${GREEN}✅ Stopped Flower${NC}"
else
    echo -e "${BLUE}ℹ️  Flower not running${NC}"
fi

# Kill Node.js dev server
echo -e "\n${YELLOW}Stopping frontend...${NC}"
if lsof -ti:3000 > /dev/null 2>&1; then
    kill $(lsof -ti:3000) 2>/dev/null
    echo -e "${GREEN}✅ Stopped Next.js frontend${NC}"
else
    echo -e "${BLUE}ℹ️  Frontend not running on port 3000${NC}"
fi

# Optional: Stop database services
echo -e "\n${YELLOW}Database services:${NC}"
echo -e "${BLUE}ℹ️  Database services (PostgreSQL, MongoDB, Redis) are still running${NC}"
echo -e "   To stop them, run:"
echo -e "   ${YELLOW}brew services stop postgresql@15${NC}"
echo -e "   ${YELLOW}brew services stop mongodb-community${NC}"
echo -e "   ${YELLOW}brew services stop redis${NC}"

echo -e "\n${GREEN}✅ All application services stopped!${NC}"
echo "========================================="

# Clean up any orphaned processes
echo -e "\n${YELLOW}Cleaning up orphaned processes...${NC}"

# Check for any remaining Python processes from our app
remaining=$(pgrep -f "src\.(main|celery)" | wc -l | tr -d ' ')
if [ "$remaining" -gt "0" ]; then
    echo -e "${YELLOW}Found $remaining orphaned processes. Cleaning up...${NC}"
    pkill -9 -f "src\.(main|celery)"
    echo -e "${GREEN}✅ Cleaned up orphaned processes${NC}"
fi

echo -e "\n${BLUE}To restart services, run:${NC}"
echo "  ./start-local-mac.sh"