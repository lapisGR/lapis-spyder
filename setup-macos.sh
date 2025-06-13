#!/bin/bash

# Lapis LLMT Spider - macOS Setup Script
# Installs dependencies and sets up the local development environment

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

echo -e "${BLUE}🚀 Setting up Lapis LLMT Spider for macOS${NC}"
echo "========================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for this session
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo -e "${GREEN}✅ Homebrew found${NC}"
fi

# Function to install Homebrew package if not installed
install_brew_package() {
    local package=$1
    local service_name=${2:-$package}
    
    if brew list "$package" &>/dev/null; then
        echo -e "${GREEN}✅ $package already installed${NC}"
    else
        echo -e "${YELLOW}📦 Installing $package...${NC}"
        brew install "$package"
    fi
    
    # Start service if it's a service
    if brew services list | grep -q "$service_name"; then
        if brew services list | grep -q "$service_name.*started"; then
            echo -e "${GREEN}✅ $service_name service is running${NC}"
        else
            echo -e "${YELLOW}🚀 Starting $service_name service...${NC}"
            brew services start "$service_name"
        fi
    fi
}

# Install required software
echo -e "\n${BLUE}Installing required software...${NC}"

install_brew_package "python@3.12" ""
install_brew_package "postgresql@15" "postgresql@15"
install_brew_package "redis" "redis"
install_brew_package "node" ""

# Install MongoDB Community Edition
if brew list mongodb-community &>/dev/null; then
    echo -e "${GREEN}✅ mongodb-community already installed${NC}"
else
    echo -e "${YELLOW}📦 Installing MongoDB Community...${NC}"
    brew tap mongodb/brew
    brew install mongodb-community
fi

# Start MongoDB
if brew services list | grep -q "mongodb-community.*started"; then
    echo -e "${GREEN}✅ MongoDB service is running${NC}"
else
    echo -e "${YELLOW}🚀 Starting MongoDB service...${NC}"
    brew services start mongodb-community
fi

# Set up Python virtual environment
echo -e "\n${BLUE}Setting up Python environment...${NC}"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3.12 -m venv venv
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Install project in development mode
echo -e "${YELLOW}Installing project in development mode...${NC}"
pip install -e .

# Set up environment file
echo -e "\n${BLUE}Setting up environment configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp .env.example .env
    
    # Update .env with proper local settings
    sed -i '' 's/APP_PORT=8000/APP_PORT=8080/' .env
    sed -i '' 's/FRONTEND_PORT=3000/FRONTEND_PORT=3000/' .env
    sed -i '' 's/POSTGRES_PORT=5432/POSTGRES_PORT=5432/' .env
    sed -i '' 's/REDIS_PORT=6379/REDIS_PORT=6379/' .env
    sed -i '' 's|REDIS_URL=redis://localhost:6379/0|REDIS_URL=redis://localhost:6379/0|' .env
    sed -i '' 's|CELERY_BROKER_URL=redis://localhost:6379/1|CELERY_BROKER_URL=redis://localhost:6379/1|' .env
    sed -i '' 's|CELERY_RESULT_BACKEND=redis://localhost:6379/2|CELERY_RESULT_BACKEND=redis://localhost:6379/2|' .env
    
    echo -e "${GREEN}✅ Created .env file with local settings${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Set up PostgreSQL database
echo -e "\n${BLUE}Setting up PostgreSQL database...${NC}"

# Create database user if not exists
if ! psql -t -c "SELECT 1 FROM pg_roles WHERE rolname='lapis'" | grep -q 1; then
    echo -e "${YELLOW}Creating database user 'lapis'...${NC}"
    createuser -s lapis
else
    echo -e "${GREEN}✅ Database user 'lapis' exists${NC}"
fi

# Create database if not exists
if ! psql -lqt | cut -d \| -f 1 | grep -qw lapis_spider; then
    echo -e "${YELLOW}Creating database 'lapis_spider'...${NC}"
    createdb -O lapis lapis_spider
else
    echo -e "${GREEN}✅ Database 'lapis_spider' exists${NC}"
fi

# Run database initialization
echo -e "${YELLOW}Setting up database schema...${NC}"
python scripts/setup_db.py

# Set up frontend
echo -e "\n${BLUE}Setting up frontend...${NC}"
cd lapis-frontend

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi

cd "$PROJECT_DIR"

# Create admin user
echo -e "\n${BLUE}Creating admin user...${NC}"
python -c "
import sys
sys.path.insert(0, '.')
from src.auth.models import create_user
from src.database.postgres import get_db
from sqlalchemy.orm import Session

try:
    db: Session = next(get_db())
    user = create_user(db, 'admin@example.com', 'Admin123!')
    print('✅ Created admin user: admin@example.com / Admin123!')
except Exception as e:
    if 'already exists' in str(e).lower():
        print('✅ Admin user already exists')
    else:
        print(f'❌ Error creating admin user: {e}')
"

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo "========================================="
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo -e "${YELLOW}1. Update .env file with your API keys:${NC}"
echo "   - GEMINI_API_KEY: Get from https://makersuite.google.com/app/apikey"
echo "   - OPENROUTER_API_KEY: Get from https://openrouter.ai/keys"
echo "   - MONGODB_URI: Your MongoDB Atlas connection string"
echo ""
echo -e "${YELLOW}2. Start the services:${NC}"
echo "   ./start-local-mac.sh"
echo ""
echo -e "${YELLOW}3. Access the application:${NC}"
echo "   - API Backend: http://localhost:8080"
echo "   - API Docs: http://localhost:8080/docs"
echo "   - Frontend: http://localhost:3000"
echo ""
echo -e "${YELLOW}4. Default login credentials:${NC}"
echo "   - Email: admin@example.com"
echo "   - Password: Admin123!"
echo ""
echo -e "${GREEN}Happy crawling! 🕷️${NC}"