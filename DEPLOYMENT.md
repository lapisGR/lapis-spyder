# Lapis Spider Deployment Guide

This guide covers the deployment of the Lapis Spider system to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Monitoring Setup](#monitoring-setup)
6. [Security Considerations](#security-considerations)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04 LTS or later (recommended)
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ depending on crawl volume
- **Python**: 3.11 or later
- **Rust**: Latest stable (for Spider-rs)
- **Docker**: 20.10+ (optional but recommended)
- **Docker Compose**: 2.0+ (optional but recommended)

### Required Services

- PostgreSQL 15+
- MongoDB 6.0+
- Redis 7.0+
- SMTP server (for email notifications)
- Google Gemini API key

## Environment Setup

### 1. Create Production Environment File

```bash
cp .env.example .env.production
```

Edit `.env.production` with production values:

```env
# Application Settings
APP_NAME="Lapis Spider"
APP_ENV=production
APP_DEBUG=false
APP_URL=https://your-domain.com

# Security
JWT_SECRET_KEY=<generate-strong-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=86400

# Database
DATABASE_URL=postgresql://lapis_user:password@localhost:5432/lapis_spider
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=lapis_spider
REDIS_URL=redis://localhost:6379/0

# API Keys
GOOGLE_API_KEY=<your-gemini-api-key>

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=<app-password>
SMTP_FROM_EMAIL=noreply@your-domain.com
SMTP_TLS=true

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Storage
STORAGE_RETENTION_DAYS=90

# Performance
CRAWL_TIMEOUT_SECONDS=300
MAX_CONCURRENT_CRAWLS=5
```

### 2. Generate Secure Secrets

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate database passwords
openssl rand -base64 32
```

## Database Setup

### 1. PostgreSQL Setup

```bash
# Create database and user
sudo -u postgres psql <<EOF
CREATE USER lapis_user WITH PASSWORD 'secure_password';
CREATE DATABASE lapis_spider OWNER lapis_user;
GRANT ALL PRIVILEGES ON DATABASE lapis_spider TO lapis_user;
EOF

# Initialize schema
python -m src.database.setup
```

### 2. MongoDB Setup

```bash
# Create MongoDB user
mongosh admin <<EOF
db.createUser({
  user: "lapis_user",
  pwd: "secure_password",
  roles: [
    { role: "readWrite", db: "lapis_spider" }
  ]
})
EOF
```

### 3. Redis Setup

```bash
# Configure Redis for production
sudo nano /etc/redis/redis.conf

# Add these settings:
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 4. Apply Database Optimizations

```bash
# Run optimization script
psql -U lapis_user -d lapis_spider -f scripts/optimize_db.sql
```

## Application Deployment

### Option 1: Docker Deployment (Recommended)

#### 1. Build Production Image

```bash
docker build -f docker/Dockerfile -t lapis-spider:latest .
```

#### 2. Deploy with Docker Compose

```bash
# Use production compose file
docker-compose -f docker-compose.yml up -d

# Check logs
docker-compose logs -f api
```

#### 3. Scale Workers

```bash
# Scale Celery workers
docker-compose up -d --scale worker=3
```

### Option 2: Manual Deployment

#### 1. Install Dependencies

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql-client libpq-dev redis-tools

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### 2. Build Spider-rs

```bash
cd spider
cargo build --release
cd ..
```

#### 3. Configure Systemd Services

Create `/etc/systemd/system/lapis-spider.service`:

```ini
[Unit]
Description=Lapis Spider API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=lapis
Group=lapis
WorkingDirectory=/opt/lapis-spider
Environment="PATH=/opt/lapis-spider/venv/bin"
ExecStart=/opt/lapis-spider/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    src.main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/lapis-spider-worker.service`:

```ini
[Unit]
Description=Lapis Spider Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=lapis
Group=lapis
WorkingDirectory=/opt/lapis-spider
Environment="PATH=/opt/lapis-spider/venv/bin"
ExecStart=/opt/lapis-spider/venv/bin/celery \
    -A src.celery worker \
    --loglevel=info \
    --concurrency=4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/lapis-spider-beat.service`:

```ini
[Unit]
Description=Lapis Spider Celery Beat
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=lapis
Group=lapis
WorkingDirectory=/opt/lapis-spider
Environment="PATH=/opt/lapis-spider/venv/bin"
ExecStart=/opt/lapis-spider/venv/bin/celery \
    -A src.celery beat \
    --loglevel=info \
    --scheduler celery.beat.PersistentScheduler
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 4. Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable lapis-spider lapis-spider-worker lapis-spider-beat
sudo systemctl start lapis-spider lapis-spider-worker lapis-spider-beat

# Check status
sudo systemctl status lapis-spider
```

### Nginx Configuration

Create `/etc/nginx/sites-available/lapis-spider`:

```nginx
upstream lapis_spider {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;
    
    location / {
        proxy_pass http://lapis_spider;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /ws {
        proxy_pass http://lapis_spider;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/lapis-spider /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Monitoring Setup

### 1. Application Monitoring

#### Prometheus Metrics

Add to your application:

```python
# src/monitoring.py
from prometheus_client import Counter, Histogram, generate_latest

crawl_counter = Counter('crawls_total', 'Total number of crawls')
crawl_duration = Histogram('crawl_duration_seconds', 'Crawl duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Grafana Dashboard

Import the provided dashboard configuration from `monitoring/grafana-dashboard.json`.

### 2. Log Aggregation

Configure centralized logging:

```yaml
# docker-compose.yml addition
  fluentd:
    image: fluent/fluentd:v1.16-debian
    volumes:
      - ./fluent.conf:/fluentd/etc/fluent.conf
      - /var/log/lapis-spider:/var/log/lapis-spider
    ports:
      - "24224:24224"
```

### 3. Health Checks

Set up monitoring for the `/health` endpoint:

```bash
# Example with curl
curl -f https://your-domain.com/health || alert_ops_team
```

## Security Considerations

### 1. API Security

- Always use HTTPS in production
- Rotate JWT secrets regularly
- Implement IP whitelisting for admin endpoints
- Use API rate limiting
- Enable CORS only for trusted domains

### 2. Database Security

- Use strong, unique passwords
- Enable SSL/TLS for database connections
- Restrict database access by IP
- Regular security updates
- Implement database backups

### 3. Infrastructure Security

- Keep all software updated
- Use firewall rules (ufw/iptables)
- Implement fail2ban for SSH
- Regular security audits
- Monitor for suspicious activity

### 4. Secrets Management

Consider using:
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets
- Environment-specific encryption

## Backup Strategy

### 1. Database Backups

```bash
# PostgreSQL backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U lapis_user lapis_spider | gzip > "$BACKUP_DIR/lapis_spider_$DATE.sql.gz"

# MongoDB backup
mongodump --uri="mongodb://localhost:27017/lapis_spider" \
    --archive="$BACKUP_DIR/mongodb_$DATE.gz" --gzip
```

### 2. Automated Backups

Add to crontab:

```cron
# Daily backups at 2 AM
0 2 * * * /opt/lapis-spider/scripts/backup.sh

# Weekly full backup
0 3 * * 0 /opt/lapis-spider/scripts/full-backup.sh
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL
sudo systemctl status postgresql
psql -U lapis_user -d lapis_spider -c "SELECT 1"

# Check MongoDB
mongosh lapis_spider --eval "db.runCommand({ping: 1})"

# Check Redis
redis-cli ping
```

#### 2. Celery Worker Issues

```bash
# Check worker status
celery -A src.celery inspect active

# Check queue length
celery -A src.celery inspect reserved

# Purge queue if needed
celery -A src.celery purge
```

#### 3. Performance Issues

```bash
# Check system resources
htop
iostat -x 1

# PostgreSQL slow queries
psql -U lapis_user -d lapis_spider -c "
SELECT query, calls, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

#### 4. Spider Crawling Issues

```bash
# Test Spider directly
./spider/target/release/spider_cli https://example.com --max-pages 1

# Check Spider logs
tail -f /var/log/lapis-spider/spider.log
```

### Debug Mode

For troubleshooting, temporarily enable debug mode:

```bash
# Set in environment
export APP_DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services
sudo systemctl restart lapis-spider
```

## Performance Tuning

### 1. PostgreSQL Tuning

```sql
-- Update postgresql.conf
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 2. Redis Tuning

```conf
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
tcp-backlog 511
timeout 300
tcp-keepalive 300
```

### 3. Application Tuning

```python
# Gunicorn workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000
keepalive = 5
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use HAProxy or AWS ALB
2. **Multiple API Servers**: Deploy behind load balancer
3. **Celery Workers**: Scale based on queue depth
4. **Database Replication**: Set up read replicas

### Vertical Scaling

1. **API Server**: Increase CPU/RAM as needed
2. **Database**: Monitor and upgrade when >80% capacity
3. **Redis**: Add memory for larger cache
4. **Workers**: More CPU cores = more concurrent tasks

## Maintenance

### Regular Tasks

1. **Daily**
   - Check health endpoints
   - Monitor error logs
   - Review metrics

2. **Weekly**
   - Database vacuum/analyze
   - Security updates check
   - Backup verification

3. **Monthly**
   - Performance review
   - Capacity planning
   - Security audit

### Update Process

```bash
# 1. Backup everything
./scripts/full-backup.sh

# 2. Update code
git pull origin main

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python -m src.database.migrate

# 5. Restart services (with zero downtime)
sudo systemctl reload lapis-spider
sudo systemctl restart lapis-spider-worker
sudo systemctl restart lapis-spider-beat
```

## Support

For issues or questions:

1. Check logs: `/var/log/lapis-spider/`
2. Review monitoring dashboards
3. Consult this documentation
4. Contact the development team

## Appendix

### A. Environment Variables Reference

See `.env.example` for complete list of environment variables.

### B. API Endpoints Reference

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- Full API documentation at `/docs` (if enabled)

### C. Database Schema

See `scripts/init_db.sql` for complete schema.

### D. Monitoring Queries

Useful queries for monitoring:

```sql
-- Active crawls
SELECT COUNT(*) FROM crawl_jobs WHERE status = 'running';

-- Daily crawl volume
SELECT DATE(created_at), COUNT(*) 
FROM crawl_jobs 
GROUP BY DATE(created_at) 
ORDER BY DATE(created_at) DESC 
LIMIT 7;

-- Storage usage
SELECT 
    pg_size_pretty(pg_database_size('lapis_spider')) as db_size,
    pg_size_pretty(pg_total_relation_size('pages')) as pages_size,
    pg_size_pretty(pg_total_relation_size('crawl_jobs')) as jobs_size;
```