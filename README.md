# Lapis-LLMT Spider

A production-grade web crawling system with AI-powered content processing that generates structured documentation similar to Vercel's llms.txt format.

## Features

- **Web Crawling**: High-performance crawling using Spider-rs
- **AI Processing**: Content structuring with Google Gemini
- **Authentication**: JWT-based API authentication with rate limiting
- **Monitoring**: Real-time change detection and notifications
- **Scheduling**: Automated crawl scheduling with Celery Beat
- **Storage**: PostgreSQL + MongoDB for optimal data storage
- **Documentation**: Generates llms.txt style documentation indexes

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Development](#development)
4. [Testing](#testing)
5. [API Documentation](#api-documentation)
6. [Architecture](#architecture)
7. [Deployment](#deployment)
8. [Port Configuration](#port-configuration)
9. [Configuration](#configuration)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- MongoDB 6.0+
- Redis 7.0+
- Rust (for building Spider-rs)
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lapis-llmt_spyder
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Initialize database**
   ```bash
   # Run database migrations
   python -m src.database.setup
   
   # Apply optimizations
   psql -U lapis_user -d lapis_spider -f scripts/optimize_db.sql
   ```

6. **Start development server**
   ```bash
   # Start API server
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   
   # In another terminal, start Celery worker
   celery -A src.celery worker --loglevel=info
   
   # In another terminal, start Celery beat scheduler
   celery -A src.celery beat --loglevel=info
   ```

The API will be available at http://localhost:8000

## Development

### Project Structure

```
lapis-llmt_spyder/
├── src/
│   ├── api/              # FastAPI route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── crawl.py      # Crawling endpoints
│   │   ├── content.py    # Content retrieval endpoints
│   │   └── monitor.py    # Monitoring endpoints
│   ├── auth/             # Authentication & authorization
│   │   ├── jwt.py        # JWT token handling
│   │   ├── middleware.py # Security middleware
│   │   └── models.py     # User models
│   ├── crawler/          # Web crawling logic
│   │   ├── spider_wrapper.py    # Spider-rs integration
│   │   ├── processor.py         # HTML processing
│   │   ├── markdown.py          # Markdown conversion
│   │   └── tasks.py             # Crawl Celery tasks
│   ├── ai/               # AI content processing
│   │   ├── gemini.py     # Google Gemini client
│   │   ├── prompts.py    # AI prompts
│   │   └── tasks.py      # AI processing tasks
│   ├── scheduler/        # Task scheduling
│   │   └── tasks.py      # Scheduled tasks
│   ├── database/         # Database connections & models
│   │   ├── postgres.py   # PostgreSQL setup
│   │   ├── mongodb.py    # MongoDB operations
│   │   └── redis.py      # Redis cache
│   ├── utils/            # Utility functions
│   │   ├── hashing.py    # Password & content hashing
│   │   ├── logging.py    # Logging configuration
│   │   ├── diff.py       # Change detection
│   │   ├── performance.py # Performance optimization
│   │   └── notifications.py # Notification system
│   ├── config.py         # Configuration management
│   ├── main.py           # FastAPI application
│   └── celery.py         # Celery configuration
├── spider/               # Spider-rs Rust crawler
├── lapis-frontend/       # Next.js frontend application
│   ├── src/
│   │   ├── app/          # Next.js app directory
│   │   ├── components/   # React components
│   │   ├── lib/          # API client & utilities
│   │   └── types/        # TypeScript type definitions
│   ├── public/           # Static assets
│   └── package.json      # Frontend dependencies
├── tests/                # Test suite
│   ├── test_auth.py      # Authentication tests
│   ├── test_crawler.py   # Crawler tests
│   ├── test_ai.py        # AI integration tests
│   ├── test_api.py       # API endpoint tests
│   └── test_utils.py     # Utility tests
├── scripts/              # Utility scripts
│   ├── init_db.sql       # Database schema
│   ├── optimize_db.sql   # Database optimizations
│   └── setup_db.py       # Database setup script
├── docker/               # Docker configurations
├── stages/               # Implementation phase guides
└── DEPLOYMENT.md         # Production deployment guide
```

### Available Commands

```bash
# Development
make dev           # Start full development environment
make serve         # Start API server only
make worker        # Start Celery worker
make beat          # Start Celery beat scheduler

# Testing
make test          # Run all tests with coverage
make test-fast     # Run fast tests only
./run_tests.sh     # Run comprehensive test suite

# Database
make init-db       # Initialize database
make migrate       # Run database migrations
make db-shell      # Open database shell

# Code Quality
make lint          # Run code linting (ruff)
make format        # Format code (black/isort)
make typecheck     # Run type checking (mypy)

# Docker
make docker-up     # Start all services
make docker-down   # Stop all services
make docker-logs   # View service logs

# Cleanup
make clean         # Clean up generated files
```

## Testing

### Running Tests

```bash
# Quick test run
./run_tests.sh

# Manual test commands
pytest tests/ -v                    # Run all tests
pytest tests/ -v --cov=src         # With coverage
pytest tests/test_auth.py -v       # Specific test file
pytest -k "test_login" -v          # Tests matching pattern
pytest -m "not slow" -v            # Exclude slow tests
```

### Test Coverage

After running tests with coverage:
- Terminal report shows missing lines
- HTML report available at `htmlcov/index.html`
- Coverage goals: >80% overall, >90% for critical paths

See [README_TESTING.md](./README_TESTING.md) for detailed testing guide.

## API Documentation

### Authentication Endpoints

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePassword123!
```

### Crawling Endpoints

```http
POST /crawl/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "website_id": "123e4567-e89b-12d3-a456-426614174000",
  "config": {
    "max_pages": 100,
    "max_depth": 3
  }
}
```

```http
GET /crawl/status/{job_id}
Authorization: Bearer <token>
```

### Content Endpoints

```http
GET /content/{website_id}/pages?limit=50&offset=0
Authorization: Bearer <token>
```

```http
GET /content/{website_id}/llms.txt
Authorization: Bearer <token>
```

### Monitoring Endpoints

```http
POST /monitor/website
Authorization: Bearer <token>
Content-Type: application/json

{
  "website_id": "123e4567-e89b-12d3-a456-426614174000",
  "config": {
    "check_frequency": "daily",
    "notify_on_changes": true,
    "notification_channels": ["email", "slack"]
  }
}
```

Full API documentation available at `/docs` when running in development mode.

## Architecture

### System Components

1. **API Layer** (FastAPI)
   - RESTful endpoints
   - JWT authentication
   - Request validation
   - Rate limiting

2. **Task Queue** (Celery + Redis)
   - Asynchronous crawling
   - Scheduled tasks
   - AI processing queue
   - Background jobs

3. **Crawler** (Spider-rs)
   - High-performance Rust crawler
   - Respects robots.txt
   - Concurrent requests
   - JavaScript rendering support

4. **AI Processing** (Google Gemini)
   - Content structuring
   - Summary generation
   - llms.txt formatting
   - Topic extraction

5. **Storage Layer**
   - PostgreSQL: Metadata, users, jobs
   - MongoDB: HTML content, markdown
   - Redis: Cache, sessions, rate limiting

6. **Monitoring & Notifications**
   - Change detection
   - Email notifications
   - Slack integration
   - In-app notifications

### Data Flow

```
User Request → API → Task Queue → Crawler → HTML Storage
                                     ↓
                              AI Processing
                                     ↓
                           Structured Content
                                     ↓
                              llms.txt Output
```

## Configuration

### Environment Variables

```env
# Application
APP_NAME="Lapis Spider"
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=86400

# Database
DATABASE_URL=postgresql://lapis_user:password@localhost:5432/lapis_spider
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=lapis_spider
REDIS_URL=redis://localhost:6379/0

# AI Processing
GOOGLE_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_REQUESTS_PER_MINUTE=10

# Crawler Settings
USER_AGENT=Lapis-Spider/1.0
MAX_PAGES_PER_CRAWL=1000
MAX_CRAWL_DEPTH=5
CRAWL_TIMEOUT_SECONDS=300
RESPECT_ROBOTS_TXT=true

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@your-domain.com
SMTP_TLS=true

# Slack Integration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Storage
STORAGE_RETENTION_DAYS=90

# Performance
MAX_CONCURRENT_CRAWLS=5
CELERY_WORKER_CONCURRENCY=4
```

See `.env.example` for complete configuration options.

## Deployment

### Production Deployment Options

1. **Docker Deployment** (Recommended)
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

2. **Manual Deployment**
   - See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions
   - Includes systemd service files
   - Nginx configuration
   - SSL setup

## Port Configuration

All services can run on configurable ports. Use the provided tools to easily change ports:

### Quick Port Changes

```bash
# Reset to default ports (API:8000, Frontend:3000)
./change-ports default

# Use alternative ports (API:8080, Frontend:3001) 
./change-ports alt

# Development ports (API:8888, Frontend:3002)
./change-ports dev

# Interactive custom port selection
./change-ports custom
```

### Manual Port Configuration

Edit `.env` and `lapis-frontend/.env.local` files:

```bash
# Backend (.env)
APP_PORT=8080
FRONTEND_PORT=3001
POSTGRES_PORT=5433
MONGODB_PORT=27018
REDIS_PORT=6380

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### Running with Custom Ports

```bash
# Backend
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

# Frontend  
cd lapis-frontend
PORT=3001 npm run dev

# Docker (reads from .env)
docker-compose up
```

See [PORT_CONFIGURATION.md](./PORT_CONFIGURATION.md) for detailed port management.

3. **Cloud Platforms**
   - AWS ECS/Fargate
   - Google Cloud Run
   - Kubernetes
   - Heroku

### Production Checklist

- [ ] Set `APP_ENV=production` and `APP_DEBUG=false`
- [ ] Generate strong JWT secret key
- [ ] Configure SSL certificates
- [ ] Set up database backups
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Set up log aggregation
- [ ] Configure rate limiting
- [ ] Enable security headers
- [ ] Set up health checks

## Phase Implementation

This project was implemented in 6 phases:

### Phase 1: Core Infrastructure ✓
- Database setup (PostgreSQL, MongoDB, Redis)
- Configuration management
- Logging system
- Basic project structure

### Phase 2: Authentication & API ✓
- JWT authentication
- User registration/login
- API rate limiting
- Security middleware

### Phase 3: Spider Integration ✓
- Spider-rs Python wrapper
- Crawl job management
- HTML storage in MongoDB
- Markdown conversion

### Phase 4: Content Processing ✓
- Google Gemini integration
- Content structuring
- llms.txt generation
- AI task queue

### Phase 5: Monitoring & Scheduling ✓
- Change detection
- Scheduled crawls
- Notification system
- Monitoring API

### Phase 6: Production Ready ✓
- Performance optimization
- Comprehensive tests
- Deployment documentation
- Database indexes

## Performance Optimization

### Implemented Optimizations

1. **Database**
   - Indexes on frequently queried fields
   - Connection pooling
   - Query optimization
   - Materialized views for statistics

2. **Caching**
   - Redis caching for API responses
   - Content deduplication
   - Session caching
   - Rate limit counters

3. **Async Processing**
   - Celery for background tasks
   - Async API endpoints
   - Concurrent crawling
   - Batch processing

4. **Resource Management**
   - Connection pooling
   - Memory limits
   - Request timeouts
   - Graceful shutdowns

## Monitoring

### Health Checks

```bash
# Check system health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "checks": {
    "postgres": true,
    "mongodb": true,
    "redis": true
  },
  "timestamp": 1234567890,
  "version": "0.1.0"
}
```

### Metrics

- Crawl success/failure rates
- Page processing times
- AI processing queue depth
- API response times
- Error rates by endpoint

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check services
   docker-compose ps
   
   # Check logs
   docker-compose logs postgres
   ```

2. **Crawler Not Working**
   ```bash
   # Test Spider directly
   cd spider
   cargo run -- https://example.com --max-pages 1
   ```

3. **AI Processing Failed**
   ```bash
   # Check API key
   echo $GOOGLE_API_KEY
   
   # Check Celery workers
   celery -A src.celery inspect active
   ```

4. **Tests Failing**
   ```bash
   # Run with verbose output
   pytest -vvs tests/test_failing.py
   
   # Check test database
   psql test_lapis_spider
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Run linting (`make lint`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

- Python: Black + isort + ruff
- TypeScript: Prettier + ESLint
- Rust: rustfmt + clippy

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: See `/docs` API endpoint
- **Issues**: Create GitHub issues for bugs/features
- **Testing**: See [README_TESTING.md](./README_TESTING.md)
- **Deployment**: See [DEPLOYMENT.md](./DEPLOYMENT.md)

## Acknowledgments

- Spider-rs for high-performance web crawling
- Google Gemini for AI content processing
- FastAPI for the excellent web framework
- The open-source community for inspiration# lapis-spyder
