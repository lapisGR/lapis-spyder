# Port Configuration Guide

This guide explains how to configure all services to run on different ports.

## Default Ports

| Service | Default Port | Environment Variable |
|---------|--------------|---------------------|
| Frontend (Next.js) | 3000 | `FRONTEND_PORT` |
| Backend API | 8000 | `APP_PORT` |
| PostgreSQL | 5432 | `POSTGRES_PORT` |
| MongoDB | 27017 | `MONGODB_PORT` |
| Redis | 6379 | `REDIS_PORT` |
| Celery Flower | 5555 | `FLOWER_PORT` |
| Prometheus | 9090 | `PROMETHEUS_PORT` |

## Changing Ports

### 1. Environment Variables Method

Copy the example environment files and modify the ports:

```bash
# Copy environment files
cp .env.example .env
cp lapis-frontend/.env.local.example lapis-frontend/.env.local
```

Edit `.env` file:
```bash
# Change API port to 8080
APP_PORT=8080

# Change database ports
POSTGRES_PORT=5433
MONGODB_PORT=27018
REDIS_PORT=6380

# Update Redis URLs with new port
REDIS_URL=redis://localhost:6380/0
CELERY_BROKER_URL=redis://localhost:6380/1
CELERY_RESULT_BACKEND=redis://localhost:6380/2

# Change monitoring port
PROMETHEUS_PORT=9091
FLOWER_PORT=5556

# Update CORS origins for new API port
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

Edit `lapis-frontend/.env.local` file:
```bash
# Point frontend to new API port
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### 2. Command Line Method

#### Frontend
```bash
cd lapis-frontend

# Run on port 3001
PORT=3001 npm run dev

# Or use the convenience script
PORT=3001 npm run dev:port
```

#### Backend (with uvicorn)
```bash
# Run API on port 8080
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

#### Using Docker Compose
```bash
# Set environment variables and run
APP_PORT=8080 FRONTEND_PORT=3001 POSTGRES_PORT=5433 docker-compose up
```

## Complete Example Configurations

### Example 1: Development on Alternative Ports

If you need to avoid conflicts with other services:

**Backend (.env):**
```bash
APP_PORT=8080
POSTGRES_PORT=5433
MONGODB_PORT=27018
REDIS_PORT=6380
REDIS_URL=redis://localhost:6380/0
CELERY_BROKER_URL=redis://localhost:6380/1
CELERY_RESULT_BACKEND=redis://localhost:6380/2
FLOWER_PORT=5556
PROMETHEUS_PORT=9091
CORS_ORIGINS=http://localhost:3001,http://localhost:8080
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

**Start commands:**
```bash
# Start backend services
docker-compose up postgres mongodb redis -d

# Start backend API
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

# Start frontend
cd lapis-frontend
PORT=3001 npm run dev
```

### Example 2: Production with Custom Ports

**Backend (.env):**
```bash
APP_ENV=production
APP_PORT=3001
POSTGRES_PORT=5432
MONGODB_PORT=27017
REDIS_PORT=6379
FRONTEND_URL=http://localhost:4000
FRONTEND_PORT=4000
CORS_ORIGINS=http://localhost:4000,http://localhost:3001
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:3001
```

### Example 3: Docker Compose with Custom Ports

Create a `docker-compose.override.yml` file:
```yaml
services:
  app:
    ports:
      - "8080:8080"
    command: uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
    environment:
      - APP_PORT=8080

  frontend:
    ports:
      - "3001:3001"
    environment:
      - NEXT_PUBLIC_API_URL=http://app:8080
      - PORT=3001

  postgres:
    ports:
      - "5433:5432"

  mongodb:
    ports:
      - "27018:27017"

  redis:
    ports:
      - "6380:6379"

  flower:
    ports:
      - "5556:5555"
```

Then run:
```bash
APP_PORT=8080 FRONTEND_PORT=3001 POSTGRES_PORT=5433 MONGODB_PORT=27018 REDIS_PORT=6380 FLOWER_PORT=5556 docker-compose up
```

## Testing Port Configuration

### 1. Check if ports are available
```bash
# Check if port is free (should return nothing if free)
lsof -i :8080  # Check if port 8080 is in use
netstat -tlnp | grep :8080  # Alternative check
```

### 2. Test service connectivity
```bash
# Test API health
curl http://localhost:8080/health

# Test frontend
curl http://localhost:3001

# Test database connections
psql -h localhost -p 5433 -U lapis -d lapis_spider
mongo localhost:27018
redis-cli -p 6380 ping
```

## Common Port Conflicts

### Typical port conflicts and solutions:

| Default Port | Common Conflict | Alternative Port |
|-------------|----------------|-----------------|
| 3000 | React dev server | 3001, 3002 |
| 8000 | Django, other APIs | 8080, 8888 |
| 5432 | PostgreSQL | 5433, 5434 |
| 27017 | MongoDB | 27018, 27019 |
| 6379 | Redis | 6380, 6381 |

## Troubleshooting

### Frontend can't connect to API
1. Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
2. Verify API is running on correct port
3. Check CORS settings in backend configuration

### Docker services can't communicate
1. Ensure all services are on the same Docker network
2. Use service names (not localhost) in Docker environment
3. Check that internal and external ports match in docker-compose

### Database connection errors
1. Verify database is running on configured port
2. Check connection strings include correct port
3. Ensure firewall allows connections on the port

## Scripts for Port Management

Create a `start.sh` script for easy port switching:

```bash
#!/bin/bash

# Set custom ports
export APP_PORT=${APP_PORT:-8080}
export FRONTEND_PORT=${FRONTEND_PORT:-3001}
export POSTGRES_PORT=${POSTGRES_PORT:-5433}

echo "Starting services on custom ports..."
echo "API: $APP_PORT"
echo "Frontend: $FRONTEND_PORT"
echo "Database: $POSTGRES_PORT"

# Start services
docker-compose up -d postgres mongodb redis
sleep 5

# Start API
uvicorn src.main:app --host 0.0.0.0 --port $APP_PORT --reload &

# Start frontend
cd lapis-frontend
PORT=$FRONTEND_PORT npm run dev
```

Make it executable:
```bash
chmod +x start.sh
```

Use it:
```bash
# Use default custom ports
./start.sh

# Use specific ports
APP_PORT=9000 FRONTEND_PORT=4000 ./start.sh
```