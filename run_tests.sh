#!/bin/bash

# Script to run all tests for Lapis Spider

echo "🧪 Running Lapis Spider Tests"
echo "============================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov pytest-mock

# Set test environment variables
export APP_ENV=test
export APP_DEBUG=true
export DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/test_lapis_spider
export MONGODB_URI=mongodb://localhost:27017
export MONGODB_DATABASE=test_lapis_spider
export REDIS_URL=redis://localhost:6379/1
export JWT_SECRET_KEY=test_secret_key_for_testing_only
export GOOGLE_API_KEY=test_api_key

# Create test database (if PostgreSQL is running)
echo -e "${YELLOW}Setting up test database...${NC}"
if command -v psql &> /dev/null; then
    sudo -u postgres psql <<EOF 2>/dev/null
DROP DATABASE IF EXISTS test_lapis_spider;
CREATE DATABASE test_lapis_spider;
EOF
fi

# Run tests with different options
echo -e "${GREEN}Running tests...${NC}"

# 1. Run all tests with coverage
echo -e "\n${YELLOW}1. Running all tests with coverage:${NC}"
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# 2. Run specific test modules
echo -e "\n${YELLOW}2. Running individual test modules:${NC}"

echo -e "${GREEN}Testing Authentication...${NC}"
pytest tests/test_auth.py -v

echo -e "${GREEN}Testing Crawler...${NC}"
pytest tests/test_crawler.py -v

echo -e "${GREEN}Testing AI Integration...${NC}"
pytest tests/test_ai.py -v

echo -e "${GREEN}Testing API Endpoints...${NC}"
pytest tests/test_api.py -v

echo -e "${GREEN}Testing Utilities...${NC}"
pytest tests/test_utils.py -v

# 3. Run only fast tests (exclude slow integration tests)
echo -e "\n${YELLOW}3. Running fast tests only:${NC}"
pytest tests/ -v -m "not slow"

# 4. Run with warnings
echo -e "\n${YELLOW}4. Running with warnings enabled:${NC}"
pytest tests/ --tb=short -W default

# Generate test report
echo -e "\n${YELLOW}Generating test report...${NC}"
echo "Test Summary" > test_report.txt
echo "============" >> test_report.txt
echo "Date: $(date)" >> test_report.txt
echo "" >> test_report.txt
pytest tests/ --tb=no -q >> test_report.txt 2>&1

# Check if all tests passed
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
else
    echo -e "\n${RED}❌ Some tests failed. Check the output above.${NC}"
fi

# Show coverage report location
echo -e "\n${YELLOW}📊 Coverage report generated at: htmlcov/index.html${NC}"

# Cleanup test database
if command -v psql &> /dev/null; then
    echo -e "\n${YELLOW}Cleaning up test database...${NC}"
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS test_lapis_spider;" 2>/dev/null
fi

echo -e "\n${GREEN}Testing complete!${NC}"