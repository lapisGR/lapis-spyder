# Lapis Spider Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Start development environment"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean up generated files"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Start development environment
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Run tests
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -rf build/ dist/ *.egg-info/

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Database commands
init-db:
	python -c "from src.database import init_db; init_db()"

# Celery commands
celery-worker:
	celery -A src.celery worker --loglevel=info

celery-beat:
	celery -A src.celery beat --loglevel=info

celery-flower:
	celery -A src.celery flower

# Development server
serve:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Check system health
health:
	curl -s http://localhost:8000/health | python -m json.tool