# Quick Start: Deploy Lapis LLMT Spider

## Prerequisites Checklist
- [ ] GitHub account with repository
- [ ] Railway account (railway.app)
- [ ] Vercel account (vercel.com)
- [ ] MongoDB Atlas account (mongodb.com/atlas)
- [ ] Google Cloud account for Gemini API

## Step 1: Install CLIs
```bash
# Install Railway CLI
brew install railway  # macOS
# OR: npm i -g @railway/cli

# Install Vercel CLI
npm i -g vercel
```

## Step 2: Get API Keys

### Google Gemini API
1. Go to https://makersuite.google.com
2. Create API key
3. Save for later

### MongoDB Atlas
1. Create free cluster at mongodb.com/atlas
2. Get connection string (format: mongodb+srv://...)
3. Add your IP to whitelist

## Step 3: Deploy Backend to Railway

### Option A: Using CLI (Recommended)
```bash
# Run the deployment script
./deploy.sh

# Choose option 2 (Backend only)
```

### Option B: Manual Steps
1. Go to railway.app
2. Create new project
3. Add services:
   - GitHub repo (select this repository)
   - PostgreSQL (Add Database → PostgreSQL)
   - Redis (Add Database → Redis)
4. Configure environment variables from `.env.railway.example`

## Step 4: Deploy Frontend to Vercel

### Option A: Using CLI
```bash
cd lapis-frontend
vercel --prod
```

### Option B: Import from GitHub
1. Go to vercel.com/new
2. Import GitHub repository
3. Set root directory: `lapis-frontend`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: Your Railway backend URL

## Step 5: Post-Deployment Setup

### Initialize Database
```bash
# Connect to Railway PostgreSQL
railway run python scripts/setup_db.py
```

### Create Admin User
```bash
railway run python -c "
from src.auth.models import create_user
from src.database.postgres import get_db
db = next(get_db())
create_user(db, 'admin@example.com', 'your-password')
"
```

### Update CORS
In Railway dashboard, update `CORS_ORIGINS` to include your Vercel URL.

## Step 6: Deploy Workers (Railway Dashboard)

1. In Railway project, add new service
2. Select same GitHub repo
3. Override start command:
   - Worker: `celery -A src.celery worker --loglevel=info`
   - Beat: `celery -A src.celery beat --loglevel=info`
4. Copy all environment variables from main service

## Verify Deployment

### Backend Health Check
```bash
curl https://your-backend.railway.app/health
```

### Frontend
Visit your Vercel URL and try logging in.

## Troubleshooting

### Common Issues
1. **CORS errors**: Update CORS_ORIGINS in Railway
2. **Database connection**: Check MongoDB Atlas whitelist
3. **Worker not running**: Ensure Celery services are deployed
4. **API timeout**: Scale up Railway resources

### Debug Commands
```bash
# View Railway logs
railway logs

# Check service status
railway status

# View Vercel logs
vercel logs
```

## Quick Reference

### Railway Dashboard
- View logs: Select service → Logs tab
- Environment vars: Select service → Variables tab
- Custom domain: Select service → Settings → Domains

### Vercel Dashboard
- View logs: Functions tab
- Environment vars: Settings → Environment Variables
- Custom domain: Settings → Domains

## Support
- Railway: https://discord.gg/railway
- Vercel: https://vercel.com/support
- MongoDB Atlas: https://mongodb.com/docs/atlas