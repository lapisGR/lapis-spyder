# Running Lapis LLMT Spider on macOS (Local Development)

This guide will help you run the Lapis LLMT Spider web crawler locally on your Mac.

## Quick Start (Recommended)

### 1. One-Command Setup
```bash
# Navigate to project directory
cd /Users/saisur/Desktop/lapis/lapisResearch/lapis-llmt_spyder

# Run the setup script (installs everything)
./setup-macos.sh
```

This script will:
- Install Homebrew (if needed)
- Install Python 3.12, PostgreSQL, MongoDB, Redis, Node.js
- Create virtual environment and install dependencies
- Set up databases and create admin user
- Install frontend dependencies

### 2. Start All Services
```bash
./start-local-mac.sh
```

### 3. Access the Application
- **API Backend**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs  
- **Frontend**: http://localhost:3000
- **Login**: admin@example.com / Admin123!

## Manual Setup (Alternative)

If you prefer to set up manually or the script doesn't work:

### 1. Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Required Software
```bash
# Core dependencies
brew install python@3.12 postgresql@15 redis node

# MongoDB
brew tap mongodb/brew
brew install mongodb-community

# Start services
brew services start postgresql@15
brew services start mongodb-community  
brew services start redis
```

### 3. Project Setup
```bash
# Navigate to project
cd /Users/saisur/Desktop/lapis/lapisResearch/lapis-llmt_spyder

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 4. Environment Configuration
```bash
# Copy example env file
cp .env.example .env

# Edit with your settings
nano .env
```

Update these key variables in `.env`:
```env
# API Keys (get your own)
GEMINI_API_KEY=your-gemini-api-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here

# MongoDB Atlas (get from mongodb.com/atlas)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/lapis_spider?retryWrites=true&w=majority

# Local PostgreSQL (default brew installation)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=lapis_spider
POSTGRES_USER=$(whoami)
POSTGRES_PASSWORD=

# Local Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

**Getting API Keys:**
- **Gemini API**: Go to https://makersuite.google.com/app/apikey
- **OpenRouter API**: Go to https://openrouter.ai/keys
- **MongoDB Atlas**: Go to https://mongodb.com/atlas and create a free cluster

### 5. Set Up Databases

#### PostgreSQL Setup
```bash
# Create database and user
createdb lapis_spider

# Run database setup
python scripts/setup_db.py

# Or manually with psql
psql -d lapis_spider < scripts/init_db.sql
```

#### MongoDB Setup
```bash
# MongoDB should connect automatically to your Atlas instance
# To test connection:
python -c "from src.database.mongodb import check_mongodb_connection_sync; print('MongoDB connected:', check_mongodb_connection_sync())"
```

## Running the Application

### Terminal 1: Start FastAPI Backend
```bash
# Activate virtual environment
source venv/bin/activate

# Run the API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# Or use the Python command
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

### Terminal 2: Start Celery Worker
```bash
# Activate virtual environment
source venv/bin/activate

# Start Celery worker
celery -A src.celery worker --loglevel=info
```

### Terminal 3: Start Celery Beat (Optional - for scheduled tasks)
```bash
# Activate virtual environment
source venv/bin/activate

# Start Celery beat
celery -A src.celery beat --loglevel=info
```

### Terminal 4: Start Frontend (Next.js)
```bash
# Navigate to frontend directory
cd lapis-frontend

# Install dependencies (first time only)
npm install

# Run development server
npm run dev
```

## Quick Start Commands

### Create Admin User
```bash
python -c "
from src.auth.models import create_user
from src.database.postgres import get_db
from sqlalchemy.orm import Session

db: Session = next(get_db())
user = create_user(db, 'admin@example.com', 'Admin123!')
print(f'Created user: {user.email}')
"
```

### Test API Health
```bash
curl http://localhost:8080/health
```

### Login and Get Token
```bash
# Login
TOKEN=$(curl -X POST "http://localhost:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

### Create and Crawl a Website
```bash
# Create website
WEBSITE_ID=$(curl -X POST "http://localhost:8080/api/websites" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Example Site","url":"https://example.com","description":"Test crawl"}' \
  | jq -r '.id')

echo "Website ID: $WEBSITE_ID"

# Start crawl
curl -X POST "http://localhost:8080/api/crawl" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"website_id\":\"$WEBSITE_ID\",\"max_pages\":10}"
```

## Useful Development Commands

### Database Management
```bash
# Check PostgreSQL
psql -d lapis_spider -c "SELECT * FROM websites;"

# Check MongoDB
python -c "
from src.database.mongodb import get_sync_mongodb
db = get_sync_mongodb()
print('Collections:', db.list_collection_names())
print('Markdown docs:', db.markdown_documents.count_documents({}))
"

# Reset databases (WARNING: Deletes all data!)
python scripts/setup_db.py --reset
```

### Celery Management
```bash
# Monitor Celery tasks
celery -A src.celery flower

# Purge all tasks
celery -A src.celery purge -f

# Inspect active tasks
celery -A src.celery inspect active
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_crawler.py

# Run with coverage
pytest --cov=src tests/

# Test markdown storage
python test_markdown_storage.py
```

### Monitoring Logs
```bash
# API logs (if running with uvicorn)
# Logs appear in the terminal where uvicorn is running

# Celery logs
# Logs appear in the terminal where celery worker is running

# Combined logs (if configured)
tail -f logs/app.log
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>
```

### PostgreSQL Connection Issues
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@15

# Check connection
psql -U $(whoami) -d lapis_spider -c "SELECT 1;"
```

### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Restart Redis
brew services restart redis
```

### MongoDB Connection Issues
```bash
# For local MongoDB
brew services restart mongodb-community

# For MongoDB Atlas, check:
# 1. Your IP is whitelisted
# 2. Connection string is correct in .env
```

### Celery Not Processing Tasks
```bash
# Check Celery is connected to Redis
celery -A src.celery inspect ping

# Check for errors
celery -A src.celery inspect stats
```

## VS Code Setup (Recommended)

### Install Extensions
- Python
- Pylance
- Black Formatter
- GitLens
- Thunder Client (for API testing)

### VS Code Settings (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true
}
```

### Launch Configuration (.vscode/launch.json)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8080"
      ],
      "jinja": true,
      "justMyCode": true
    },
    {
      "name": "Celery Worker",
      "type": "python",
      "request": "launch",
      "module": "celery",
      "args": [
        "-A",
        "src.celery",
        "worker",
        "--loglevel=info"
      ],
      "justMyCode": true
    }
  ]
}
```

## Stopping Services

### Stop All Services
```bash
# Stop backend (Ctrl+C in terminal)

# Stop Celery
pkill -f "celery worker"
pkill -f "celery beat"

# Stop database services (optional)
brew services stop postgresql@15
brew services stop mongodb-community
brew services stop redis
```

### Deactivate Virtual Environment
```bash
deactivate
```

## Performance Tips

1. **Use MongoDB Atlas** instead of local MongoDB for better performance
2. **Limit concurrent requests** in crawler config to avoid overwhelming sites
3. **Use Redis for caching** to speed up repeated operations
4. **Run Flower** to monitor Celery task performance

## Next Steps

1. Access the API documentation: http://localhost:8080/docs
2. Access the frontend: http://localhost:3000
3. Monitor tasks with Flower: http://localhost:5555
4. Read the main README.md for detailed feature documentation

## Common Issues

### "Module not found" Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Slow Crawling
- Reduce `concurrent_requests` in crawl config
- Check your internet connection
- Monitor Celery worker for errors

### Memory Issues
- Limit `max_pages` in crawl requests
- Restart Celery workers periodically
- Monitor system resources with Activity Monitor

---

For production deployment, see DEPLOYMENT.md