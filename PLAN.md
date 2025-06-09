# Lapis-LLMT Spider: Web Crawler System Plan

## Overview
A production-grade web crawling system that:
- Accepts authenticated crawl requests via REST API
- Stores raw HTML and converts to structured markdown
- Monitors websites for changes every 24 hours
- Uses Gemini AI to clean and structure content
- Generates llms.txt style documentation indexes

## Core Technologies

### Backend Stack
- **Language**: Python 3.12
- **Web Framework**: FastAPI (async, modern, JWT support)
- **Task Queue**: Celery + Redis (distributed crawling)
- **Scheduler**: Celery Beat (cron jobs)
- **Database**: PostgreSQL (relational data) + MongoDB (document storage)
- **Cache**: Redis (job queuing, rate limiting)

### Crawling & Processing
- **Spider-rs**: Rust-based crawler (already submoduled)
- **Python Bindings**: PyO3 or subprocess for spider integration
- **BeautifulSoup4**: HTML parsing
- **Markdownify**: HTML to Markdown conversion
- **Google Generative AI**: Gemini API for content structuring

### Storage & Search
- **PostgreSQL**: 
  - Crawl jobs metadata
  - User authentication
  - Website monitoring configs
  - Change tracking
- **MongoDB**: 
  - Raw HTML storage
  - Processed markdown documents
  - Version history
- **MinIO/S3**: Large file storage (optional)

### Authentication & Security
- **JWT**: PyJWT for token generation/validation
- **Bcrypt**: Password hashing
- **Rate Limiting**: Redis-based rate limiter
- **API Keys**: For service-to-service auth

### Monitoring & Observability
- **Logging**: Structured logging with loguru
- **Metrics**: Prometheus + Grafana
- **Alerts**: Email/Slack notifications for failures

## Database Schema Design

### PostgreSQL Tables

```sql
-- Users for authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Websites to monitor
CREATE TABLE websites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    url VARCHAR(2048) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    crawl_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, url)
);

-- Crawl jobs
CREATE TABLE crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    website_id UUID REFERENCES websites(id),
    status VARCHAR(50) NOT NULL, -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    pages_crawled INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Page tracking for change detection
CREATE TABLE pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    website_id UUID REFERENCES websites(id),
    url VARCHAR(2048) NOT NULL,
    url_path VARCHAR(2048) NOT NULL,
    content_hash VARCHAR(64), -- SHA256 of content
    last_modified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(website_id, url)
);

-- Change history
CREATE TABLE page_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID REFERENCES pages(id),
    crawl_job_id UUID REFERENCES crawl_jobs(id),
    change_type VARCHAR(50), -- created, updated, deleted
    old_hash VARCHAR(64),
    new_hash VARCHAR(64),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crawl schedules
CREATE TABLE crawl_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    website_id UUID REFERENCES websites(id),
    cron_expression VARCHAR(255) DEFAULT '0 2 * * *', -- Daily at 2 AM
    is_active BOOLEAN DEFAULT true,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### MongoDB Collections

```javascript
// Raw HTML storage
{
  _id: ObjectId,
  crawl_job_id: UUID,
  page_id: UUID,
  url: String,
  raw_html: String,
  headers: Object,
  status_code: Number,
  crawled_at: Date,
  content_type: String,
  size_bytes: Number
}

// Processed markdown documents
{
  _id: ObjectId,
  page_id: UUID,
  website_id: UUID,
  url: String,
  raw_markdown: String,
  structured_markdown: String, // After Gemini processing
  metadata: {
    title: String,
    description: String,
    headings: Array,
    links: Array,
    images: Array
  },
  gemini_prompt_used: String,
  processed_at: Date,
  version: Number
}

// Website documentation index (llms.txt style)
{
  _id: ObjectId,
  website_id: UUID,
  index_content: String, // The full llms.txt content
  page_tree: Object, // Hierarchical structure
  generated_at: Date,
  version: Number
}
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Get JWT token
- `POST /auth/refresh` - Refresh token

### Crawling
- `POST /crawl/start` - Start crawl job (JWT required)
- `GET /crawl/status/{job_id}` - Check job status
- `GET /crawl/history` - List crawl jobs

### Content
- `GET /content/{website_id}/pages` - List pages
- `GET /content/{website_id}/page/{page_id}` - Get page content
- `GET /content/{website_id}/llms.txt` - Get structured index
- `GET /content/{website_id}/changes` - Get change history

### Monitoring
- `POST /monitor/website` - Add website to monitor
- `GET /monitor/websites` - List monitored websites
- `PUT /monitor/website/{id}` - Update monitoring config
- `DELETE /monitor/website/{id}` - Remove from monitoring

## Directory Structure

```
lapis-llmt_spyder/
├── spider/                    # Spider-rs submodule
├── src/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry
│   ├── config.py             # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgres.py       # PostgreSQL models & queries
│   │   ├── mongodb.py        # MongoDB operations
│   │   └── redis.py          # Redis cache layer
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py            # JWT handling
│   │   ├── models.py         # Auth models
│   │   └── dependencies.py   # FastAPI dependencies
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── spider_wrapper.py # Spider-rs integration
│   │   ├── processor.py      # HTML processing
│   │   ├── markdown.py       # Markdown conversion
│   │   └── tasks.py          # Celery tasks
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── gemini.py         # Gemini API client
│   │   └── prompts.py        # Content structuring prompts
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py           # Auth endpoints
│   │   ├── crawl.py          # Crawl endpoints
│   │   ├── content.py        # Content endpoints
│   │   └── monitor.py        # Monitoring endpoints
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── tasks.py          # Scheduled tasks
│   │   └── beat.py           # Celery beat config
│   └── utils/
│       ├── __init__.py
│       ├── hashing.py        # Content hashing
│       ├── diff.py           # Change detection
│       └── llms_generator.py # Generate llms.txt
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_crawler.py
│   └── test_ai.py
├── scripts/
│   ├── setup_db.py           # Database initialization
│   └── migrate.py            # Database migrations
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example
├── requirements.txt
├── setup.py
├── README.md
└── .env.example
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- Set up project structure
- Configure PostgreSQL and MongoDB
- Implement basic FastAPI app
- Set up Redis and Celery
- Create database models

### Phase 2: Authentication & API (Week 2)
- Implement JWT authentication
- Create user registration/login
- Build rate limiting
- Add API key generation

### Phase 3: Spider Integration (Week 3)
- Integrate spider-rs with Python
- Create crawling tasks
- Implement HTML storage
- Add basic markdown conversion

### Phase 4: Content Processing (Week 4)
- Integrate Gemini API
- Create content structuring prompts
- Build markdown processor
- Generate llms.txt indexes

### Phase 5: Monitoring & Scheduling (Week 5)
- Implement change detection
- Set up Celery Beat schedules
- Create monitoring endpoints
- Add notification system

### Phase 6: Production Ready (Week 6)
- Add comprehensive tests
- Docker containerization
- Documentation
- Performance optimization
- Security hardening

## Configuration Example

```env
# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/lapis_spider
MONGODB_URL=mongodb://localhost:27017/lapis_spider

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Gemini AI
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-1.5-flash

# Crawler
MAX_PAGES_PER_CRAWL=1000
CRAWL_TIMEOUT_SECONDS=3600
USER_AGENT=Lapis-Spider/1.0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Security Considerations

1. **Authentication**: JWT with refresh tokens
2. **Rate Limiting**: Per-user API limits
3. **Input Validation**: Pydantic models for all inputs
4. **SQL Injection**: Use parameterized queries
5. **XSS Prevention**: Sanitize stored content
6. **Secrets Management**: Environment variables
7. **HTTPS Only**: Enforce TLS in production
8. **CORS**: Whitelist allowed origins

## Performance Optimization

1. **Async Processing**: Use FastAPI's async capabilities
2. **Connection Pooling**: For both databases
3. **Caching**: Redis for frequently accessed data
4. **Batch Processing**: Group similar operations
5. **Indexing**: Proper database indexes
6. **CDN**: For serving static content
7. **Compression**: Gzip responses

## Monitoring & Alerts

1. **Health Checks**: `/health` endpoint
2. **Metrics**: Prometheus exporters
3. **Logging**: Structured JSON logs
4. **Error Tracking**: Sentry integration
5. **Uptime Monitoring**: External service
6. **Database Monitoring**: Query performance
7. **Queue Monitoring**: Celery task metrics

## Next Steps

1. Review and approve this plan
2. Set up development environment
3. Initialize project structure
4. Begin Phase 1 implementation
5. Create detailed API documentation
6. Set up CI/CD pipeline