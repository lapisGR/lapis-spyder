# Phase 3: Spider Integration

## Overview
Integrate the Spider-rs Rust crawler with Python, implement crawling tasks, HTML storage, and basic markdown conversion.

## Duration: Week 3

## Prerequisites
- Phase 1 & 2 completed successfully
- Authentication system operational
- Celery workers running
- Spider-rs submodule initialized

## Checklist

### Day 1-2: Spider-rs Integration
- [ ] Rust-Python Bridge Setup
  - [ ] Evaluate integration options:
    - [ ] PyO3 for direct Rust bindings
    - [ ] Subprocess with JSON communication
    - [ ] gRPC service approach
  - [ ] Install required dependencies
  - [ ] Create spider_wrapper.py module
  - [ ] Implement Spider configuration class
  - [ ] Handle Rust binary compilation/installation
  - [ ] Create error handling for Rust panics

- [ ] Spider Configuration
  - [ ] Create crawl configuration schema:
    - [ ] Max pages to crawl
    - [ ] Crawl depth limit
    - [ ] URL patterns to include/exclude
    - [ ] Request timeout
    - [ ] Concurrent requests limit
    - [ ] User agent string
    - [ ] Custom headers
    - [ ] Robots.txt respect
  - [ ] Implement configuration validation
  - [ ] Create per-website configurations
  - [ ] Add JavaScript rendering options

### Day 2-3: Crawling Task Implementation
- [ ] Celery Tasks
  - [ ] Create crawl_website task
  - [ ] Implement progress tracking
  - [ ] Add task status updates
  - [ ] Handle task cancellation
  - [ ] Implement retry logic for failures
  - [ ] Create task result storage
  - [ ] Add memory limit monitoring
  - [ ] Implement graceful shutdown

- [ ] Crawl Job Management
  - [ ] Create job lifecycle methods:
    - [ ] Initialize crawl job
    - [ ] Update job progress
    - [ ] Handle job completion
    - [ ] Process job failures
  - [ ] Implement job queueing system
  - [ ] Add priority queue support
  - [ ] Create job monitoring
  - [ ] Implement job timeout handling

### Day 3-4: HTML Storage System
- [ ] Raw HTML Storage
  - [ ] Design MongoDB document schema
  - [ ] Implement bulk insert for performance
  - [ ] Add compression for HTML storage
  - [ ] Create content deduplication
  - [ ] Implement storage cleanup policies
  - [ ] Add metadata extraction:
    - [ ] Page title
    - [ ] Meta description
    - [ ] Open Graph tags
    - [ ] Response headers
    - [ ] Content type
    - [ ] Page size
  - [ ] Create retrieval methods

- [ ] URL Management
  - [ ] Implement URL normalization
  - [ ] Create URL deduplication
  - [ ] Handle redirect chains
  - [ ] Track crawled vs pending URLs
  - [ ] Implement URL filtering rules
  - [ ] Create sitemap parser
  - [ ] Add robots.txt parser

### Day 4-5: Basic Markdown Conversion
- [ ] HTML to Markdown Converter
  - [ ] Install markdown conversion libraries
  - [ ] Create conversion pipeline:
    - [ ] Clean HTML (remove scripts/styles)
    - [ ] Extract main content
    - [ ] Convert to markdown
    - [ ] Preserve important formatting
  - [ ] Handle special elements:
    - [ ] Tables
    - [ ] Code blocks
    - [ ] Images with alt text
    - [ ] Links with titles
    - [ ] Nested lists
  - [ ] Implement fallback strategies

- [ ] Content Processing Pipeline
  - [ ] Create processing queue
  - [ ] Implement batch processing
  - [ ] Add content validation
  - [ ] Create quality metrics:
    - [ ] Content length
    - [ ] Link density
    - [ ] Image count
    - [ ] Heading structure
  - [ ] Store processed content
  - [ ] Handle processing failures

### Day 5: API Endpoints & Testing
- [ ] Crawl API Endpoints
  - [ ] POST /crawl/start
    ```json
    {
      "website_id": "uuid",
      "config": {
        "max_pages": 1000,
        "depth": 3,
        "include_patterns": ["*"],
        "exclude_patterns": ["/admin/*"]
      }
    }
    ```
  - [ ] GET /crawl/status/{job_id}
  - [ ] POST /crawl/stop/{job_id}
  - [ ] GET /crawl/history
  - [ ] GET /crawl/stats/{website_id}

- [ ] Testing Suite
  - [ ] Unit tests for spider wrapper
  - [ ] Integration tests with mock sites
  - [ ] Test crawl configuration validation
  - [ ] Test HTML storage and retrieval
  - [ ] Test markdown conversion quality
  - [ ] Performance benchmarks
  - [ ] Load testing for concurrent crawls

## Deliverables
1. Working Spider-rs integration
2. Celery-based crawling tasks
3. HTML storage in MongoDB
4. Basic markdown conversion
5. Crawl management API
6. Comprehensive test suite

## Validation Criteria
- [ ] Can start crawl via API
- [ ] Spider successfully crawls websites
- [ ] HTML stored correctly in MongoDB
- [ ] Progress tracked in real-time
- [ ] Markdown conversion produces clean output
- [ ] Rate limiting respected
- [ ] Robots.txt honored
- [ ] Memory usage stays within limits

## Performance Targets
- Crawl speed: 10+ pages/second
- Storage efficiency: <50% of raw HTML size
- Conversion speed: 100+ pages/second
- Memory usage: <1GB per crawl job
- Concurrent crawls: 10+ websites

## Common Issues & Solutions
1. **Spider crashes**: Implement process monitoring and restart
2. **Memory leaks**: Set worker max tasks per child
3. **Slow crawls**: Tune concurrent request limits
4. **Storage growth**: Implement retention policies
5. **Blocked requests**: Rotate user agents, add delays

## Configuration Examples
```python
# Crawl configuration
{
    "max_pages": 1000,
    "max_depth": 3,
    "concurrent_requests": 10,
    "request_timeout": 30,
    "respect_robots_txt": True,
    "user_agent": "Lapis-Spider/1.0",
    "include_patterns": ["https://example.com/*"],
    "exclude_patterns": [
        "*.pdf",
        "*.zip",
        "/admin/*",
        "/api/*"
    ],
    "headers": {
        "Accept-Language": "en-US,en;q=0.9"
    },
    "javascript": {
        "enabled": False,
        "wait_time": 2
    }
}
```

## Testing Commands
```bash
# Test spider wrapper
pytest tests/test_crawler.py -v

# Start a test crawl
curl -X POST http://localhost:8000/crawl/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "test-site-id",
    "config": {
      "max_pages": 10,
      "depth": 2
    }
  }'

# Check crawl status
curl -X GET http://localhost:8000/crawl/status/JOB_ID \
  -H "Authorization: Bearer YOUR_TOKEN"

# Monitor Celery tasks
celery -A src.celery flower

# Check MongoDB storage
mongosh lapis_spider --eval "db.raw_html.stats()"
```

## Integration Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI API   │────▶│  Celery Tasks   │────▶│  Spider-rs      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   PostgreSQL    │     │     MongoDB     │
                        │   (job status)  │     │   (HTML docs)   │
                        └─────────────────┘     └─────────────────┘
```

## Next Phase Dependencies
Crawling and basic markdown conversion must work before adding AI-powered content processing in Phase 4.