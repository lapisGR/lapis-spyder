# Phase 1: Core Infrastructure

## Overview
Set up the foundational infrastructure for the Lapis-LLMT Spider system including databases, message queues, and basic application structure.

## Duration: Week 1

## Prerequisites
- Python 3.12 installed
- Docker and Docker Compose installed
- PostgreSQL client tools
- MongoDB client tools
- Redis client tools

## Checklist

### Day 1-2: Project Setup
- [x] Initialize Python project structure
  - [x] Create src/ directory with __init__.py files
  - [x] Set up virtual environment with Python 3.12
  - [x] Create requirements.txt with initial dependencies
  - [x] Create setup.py for package installation
  - [x] Initialize git repository (if not already)
  - [x] Create .gitignore file
  - [x] Create .env.example file with all required variables

- [x] Set up configuration management
  - [x] Create config.py with environment variable loading
  - [x] Implement settings validation with Pydantic
  - [x] Create separate configs for dev/test/prod
  - [x] Add logging configuration

### Day 2-3: Database Setup
- [x] PostgreSQL Setup
  - [x] Create docker-compose.yml with PostgreSQL service
  - [x] Design and document database schema
  - [x] Create SQL migration scripts
  - [x] Implement database connection pooling
  - [x] Create initial tables:
    - [x] users table
    - [x] websites table
    - [x] crawl_jobs table
    - [x] pages table
    - [x] page_changes table
    - [x] crawl_schedules table
  - [x] Add proper indexes for performance
  - [x] Create database initialization script

- [x] MongoDB Setup
  - [x] Add MongoDB service to docker-compose.yml
  - [x] Configure MongoDB connection
  - [x] Create database and collections
  - [x] Design document schemas
  - [x] Implement connection management
  - [x] Create indexes for:
    - [x] raw_html collection
    - [x] markdown_documents collection
    - [x] website_indexes collection

### Day 3-4: Message Queue & Cache Setup
- [x] Redis Setup
  - [x] Add Redis service to docker-compose.yml
  - [x] Configure Redis connection
  - [x] Implement Redis client wrapper
  - [x] Set up connection pooling
  - [x] Create cache key naming conventions
  - [x] Implement basic cache operations

- [x] Celery Setup
  - [x] Install and configure Celery
  - [x] Create celery.py configuration file
  - [x] Set up Celery Beat for scheduling
  - [x] Configure task routing
  - [x] Create base task classes
  - [x] Implement task retry logic
  - [x] Set up result backend

### Day 4-5: Basic FastAPI Application
- [x] FastAPI Setup
  - [x] Create main.py with FastAPI app
  - [x] Configure CORS middleware
  - [x] Add request ID middleware
  - [x] Implement global exception handlers
  - [x] Set up API versioning
  - [x] Create health check endpoint

- [x] Database Integration
  - [x] Create database session management
  - [x] Implement dependency injection for DB
  - [x] Create base SQLAlchemy models
  - [x] Implement MongoDB client management
  - [x] Add database health checks

### Day 5: Development Tools
- [x] Testing Infrastructure
  - [x] Set up pytest configuration
  - [x] Create test database fixtures
  - [x] Implement test data factories
  - [x] Add test coverage configuration
  - [x] Create initial smoke tests

- [x] Development Utilities
  - [x] Create Makefile for common commands
  - [ ] Add pre-commit hooks
  - [x] Set up code formatting (black, isort)
  - [x] Configure linting (flake8, pylint)
  - [x] Create development docker-compose override

## Deliverables
1. Working project structure with all dependencies
2. Running PostgreSQL, MongoDB, and Redis instances
3. Basic FastAPI application with health checks
4. Celery worker and beat configuration
5. Development environment fully configured

## Validation Criteria
- [x] All services start successfully with docker-compose up
- [x] Health check endpoint returns 200 OK
- [x] Can connect to all databases
- [x] Celery worker processes test tasks
- [x] All initial tests pass
- [x] Code passes linting and formatting checks

## Common Issues & Solutions
1. **Port conflicts**: Check for existing services on default ports
2. **Permission issues**: Ensure docker volumes have correct permissions
3. **Connection timeouts**: Verify service dependencies in docker-compose
4. **Import errors**: Check PYTHONPATH and package structure

## Next Phase Dependencies
This phase must be completed before starting Phase 2 as all subsequent work depends on this infrastructure.

## Resources & References
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
- [Redis-py Documentation](https://redis-py.readthedocs.io/)

## Commands Cheatsheet
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Run database migrations
python scripts/setup_db.py

# Start Celery worker
celery -A src.celery worker --loglevel=info

# Start Celery beat
celery -A src.celery beat --loglevel=info

# Run tests
pytest tests/ -v

# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
```