# Deploy Lapis LLMT Spider: Vercel (Frontend) + Railway (Backend)

## Prerequisites
- Vercel account
- Railway account
- GitHub repository with your code
- Google Cloud account (for Gemini API)

## Backend Deployment on Railway

### 1. Prepare Backend for Railway

Create `railway.json` in root directory:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker/Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

Create `Procfile` in root directory:
```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
worker: celery -A src.celery worker --loglevel=info
beat: celery -A src.celery beat --loglevel=info
```

### 2. Deploy Services on Railway

1. **Create New Project** in Railway dashboard

2. **Add PostgreSQL Service**:
   - Click "New Service" → "Database" → "PostgreSQL"
   - Railway will provide connection URL

3. **Add Redis Service**:
   - Click "New Service" → "Database" → "Redis"
   - Railway will provide connection URL

4. **Add MongoDB** (via MongoDB Atlas):
   - Create free cluster at mongodb.com/atlas
   - Get connection string
   - Add to Railway variables

5. **Deploy Backend**:
   - Click "New Service" → "GitHub Repo"
   - Select your repository
   - Set root directory if needed

### 3. Configure Environment Variables in Railway

Add these variables to your backend service:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=$PORT
ENVIRONMENT=production

# Database URLs (Railway provides these)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/lapis?retryWrites=true&w=majority

# Security
JWT_SECRET=your-very-long-random-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=30

# Google Gemini
GOOGLE_API_KEY=your-gemini-api-key

# CORS (add your Vercel frontend URL)
CORS_ORIGINS=["https://your-app.vercel.app"]

# Celery
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
```

### 4. Deploy Worker Services

For Celery worker and beat, create separate services:

1. **Celery Worker**:
   - New Service → GitHub Repo (same repo)
   - Override start command: `celery -A src.celery worker --loglevel=info`
   - Copy all env variables from main service

2. **Celery Beat**:
   - New Service → GitHub Repo (same repo)
   - Override start command: `celery -A src.celery beat --loglevel=info`
   - Copy all env variables from main service

## Frontend Deployment on Vercel

### 1. Prepare Frontend Configuration

Update `lapis-frontend/next.config.ts`:
```typescript
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://your-backend.railway.app',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
```

### 2. Deploy to Vercel

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy from Frontend Directory**:
   ```bash
   cd lapis-frontend
   vercel
   ```

3. **Configure Environment Variables** in Vercel Dashboard:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```

4. **Set Build & Output Settings**:
   - Framework Preset: Next.js
   - Root Directory: `lapis-frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

## Post-Deployment Setup

### 1. Initialize Database

SSH into Railway service or run locally with production DATABASE_URL:

```bash
# Run database migrations
python scripts/setup_db.py

# Initialize MongoDB collections
python -c "from src.database.mongodb import init_mongodb; init_mongodb()"
```

### 2. Create Admin User

```bash
# Via Railway CLI or local with prod env
python -c "
from src.auth.models import create_user
from src.database.postgres import get_db
db = next(get_db())
create_user(db, 'admin@example.com', 'securepassword')
"
```

### 3. Update CORS Settings

Ensure your Railway backend allows your Vercel frontend URL:
- Add `https://your-app.vercel.app` to CORS_ORIGINS

### 4. Configure Custom Domain (Optional)

**Vercel**:
- Settings → Domains → Add your domain

**Railway**:
- Service Settings → Domains → Add custom domain

## Monitoring & Logs

**Railway**:
- View logs in Railway dashboard
- Set up alerts for service health

**Vercel**:
- Functions tab for API route logs
- Analytics for performance metrics

## Troubleshooting

### Backend Issues
1. Check Railway logs for errors
2. Verify all environment variables are set
3. Ensure database connections are working
4. Check Celery workers are running

### Frontend Issues
1. Verify NEXT_PUBLIC_API_URL is correct
2. Check browser console for CORS errors
3. Ensure API routes are properly configured

### Common Fixes
- **CORS errors**: Add Vercel URL to backend CORS_ORIGINS
- **Database connection**: Check connection strings and network access
- **API timeouts**: Increase Railway service resources
- **Worker not processing**: Ensure Celery services are running

## Cost Optimization

**Railway**:
- Free tier: $5/month credit
- Scale down workers when not needed
- Use sleep feature for development

**Vercel**:
- Free tier suitable for most projects
- Monitor bandwidth usage

**MongoDB Atlas**:
- Free tier: 512MB storage
- Sufficient for small-medium sites

## Security Checklist

- [ ] Strong JWT_SECRET in production
- [ ] HTTPS enabled on both services
- [ ] Database credentials secure
- [ ] API rate limiting configured
- [ ] CORS properly restricted
- [ ] Environment variables not exposed