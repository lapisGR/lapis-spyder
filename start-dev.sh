#!/bin/bash

# Simple development starter script
# Run this after setting up your environment

echo "🚀 Starting Lapis LLMT Spider Development Environment"
echo "===================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   ./setup-macos.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"
echo ""
echo "🔧 Services to start (open each in a separate terminal):"
echo ""
echo "1️⃣  API Backend:"
echo "   source venv/bin/activate && uvicorn src.main:app --reload --host 0.0.0.0 --port 8080"
echo ""
echo "2️⃣  Celery Worker:"
echo "   source venv/bin/activate && celery -A src.celery worker --loglevel=info"
echo ""
echo "3️⃣  Celery Beat (optional):"
echo "   source venv/bin/activate && celery -A src.celery beat --loglevel=info"
echo ""
echo "4️⃣  Flower (Celery monitoring - optional):"
echo "   source venv/bin/activate && celery -A src.celery flower --port=5555"
echo ""
echo "5️⃣  Frontend (in new terminal):"
echo "   cd lapis-frontend && npm run dev"
echo ""
echo "🌐 Access URLs:"
echo "   • Frontend: http://localhost:3000"
echo "   • API: http://localhost:8080"
echo "   • API Docs: http://localhost:8080/docs"
echo "   • Flower: http://localhost:5555"
echo ""
echo "🔑 Default Login:"
echo "   • Email: admin@example.com"
echo "   • Password: Admin123!"
echo ""
echo "📝 Current environment activated. You can now run individual services."