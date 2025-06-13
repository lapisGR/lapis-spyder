#!/usr/bin/env python3
"""
Generate secure environment variables for Lapis LLMT Spider deployment
"""

import os
import secrets
import json
from pathlib import Path
from datetime import datetime

def generate_jwt_secret(length: int = 64) -> str:
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(length)

def generate_password(length: int = 32) -> str:
    """Generate a secure password"""
    return secrets.token_urlsafe(length)

def generate_api_key(prefix: str = "lapis", length: int = 32) -> str:
    """Generate an API key with prefix"""
    return f"{prefix}_{secrets.token_urlsafe(length)}"

def main():
    print("🔐 Generating secure environment variables...")
    
    # Generate secure secrets
    jwt_secret = generate_jwt_secret()
    db_password = generate_password()
    redis_password = generate_password()
    admin_password = generate_password(24)
    
    # Create timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Railway environment variables
    railway_env = f"""# Railway Backend Environment Variables
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 
# IMPORTANT: Update the following after creating services:
# 1. MONGODB_URI - Get from MongoDB Atlas
# 2. GOOGLE_API_KEY - Get from Google Cloud Console
# 3. CORS_ORIGINS - Update with your Vercel URL

# API Configuration
API_HOST=0.0.0.0
API_PORT=$PORT
ENVIRONMENT=production
APP_NAME=lapis-spider

# Database URLs (Railway auto-provides these)
DATABASE_URL=${{{{Postgres.DATABASE_URL}}}}
REDIS_URL=${{{{Redis.REDIS_URL}}}}

# MongoDB Atlas (UPDATE THIS!)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/lapis?retryWrites=true&w=majority
MONGODB_DB=lapis_spider

# Security
JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Gemini (UPDATE THIS!)
GOOGLE_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=30

# CORS (UPDATE with your Vercel URL!)
CORS_ORIGINS=["https://your-app.vercel.app","http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true
TRUSTED_HOSTS=["your-app.railway.app"]

# Celery
CELERY_BROKER_URL=${{{{Redis.REDIS_URL}}}}
CELERY_RESULT_BACKEND=${{{{Redis.REDIS_URL}}}}
CELERY_TASK_TIME_LIMIT=3600
CELERY_TASK_SOFT_TIME_LIMIT=3300

# Crawler Settings
MAX_PAGES_PER_CRAWL=1000
CRAWL_TIMEOUT_SECONDS=3600
USER_AGENT=Lapis-Spider/1.0
CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RESPECT_ROBOTS_TXT=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Storage
STORAGE_RETENTION_DAYS=90
STORAGE_COMPRESSION=true

# Monitoring
SENTRY_DSN=
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# Email (Optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@lapis-spider.com
SMTP_TLS=true

# Slack (Optional)
SLACK_WEBHOOK_URL=

# Generated Credentials (for initial setup)
ADMIN_EMAIL=admin@lapis-spider.com
ADMIN_PASSWORD={admin_password}
"""

    # Vercel environment variables
    vercel_env = """# Vercel Frontend Environment Variables
# Generated: {timestamp}

# Backend API URL (UPDATE with your Railway URL!)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Optional: Analytics
NEXT_PUBLIC_GA_ID=
NEXT_PUBLIC_HOTJAR_ID=

# Optional: Error Tracking
NEXT_PUBLIC_SENTRY_DSN=
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Local development environment
    local_env = f"""# Local Development Environment Variables
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Use this for local development with your existing .env settings

# Copy your existing Google/OpenRouter API keys here
GOOGLE_API_KEY=your-existing-gemini-key
OPENROUTER_API_KEY=your-existing-openrouter-key

# MongoDB Atlas for local development
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/lapis_dev?retryWrites=true&w=majority

# Generated secure JWT secret for local testing
JWT_SECRET_KEY={generate_jwt_secret(48)}

# Admin credentials for local testing
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD={generate_password(16)}
"""

    # Save files
    with open('.env.railway', 'w') as f:
        f.write(railway_env)
    
    with open('.env.vercel', 'w') as f:
        f.write(vercel_env)
    
    with open('.env.local', 'w') as f:
        f.write(local_env)
    
    # Create a quick reference file
    quick_ref = f"""# 🚀 Lapis LLMT Spider - Environment Quick Reference

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 🔐 Generated Secrets

### JWT Secret (Railway)
```
{jwt_secret}
```

### Admin Credentials (for initial setup)
- Email: `admin@lapis-spider.com`
- Password: `{admin_password}`

## 📋 Required External Services

### 1. MongoDB Atlas
- Sign up: https://mongodb.com/atlas
- Create free M0 cluster
- Get connection string
- Update MONGODB_URI in Railway

### 2. Google Gemini API
- Get API key: https://makersuite.google.com/app/apikey
- Update GOOGLE_API_KEY in Railway

### 3. Railway Services
- PostgreSQL: Auto-provisioned
- Redis: Auto-provisioned

## 🔧 Environment Files Created

1. **`.env.railway`** - Production backend variables
2. **`.env.vercel`** - Production frontend variables
3. **`.env.local`** - Local development reference

## 📝 Deployment Steps

### Backend (Railway)
```bash
# 1. Login to Railway
railway login

# 2. Create new project
railway new

# 3. Add services
railway add --database postgres
railway add --database redis

# 4. Deploy
railway up

# 5. Copy .env.railway contents to Railway dashboard
```

### Frontend (Vercel)
```bash
# 1. Navigate to frontend
cd lapis-frontend

# 2. Deploy
vercel --prod

# 3. Add environment variables from .env.vercel
```

## ⚠️ Important Updates Required

After deployment, update these values:

1. **Railway (.env.railway)**:
   - `MONGODB_URI` - Your MongoDB Atlas connection string
   - `GOOGLE_API_KEY` - Your Gemini API key
   - `CORS_ORIGINS` - Add your Vercel URL

2. **Vercel (.env.vercel)**:
   - `NEXT_PUBLIC_API_URL` - Your Railway backend URL

## 🔒 Security Notes

- All secrets are cryptographically generated
- Never commit .env files to Git
- Rotate secrets regularly
- Use environment-specific values

## 📞 Support Resources

- Railway Discord: https://discord.gg/railway
- Vercel Support: https://vercel.com/support
- MongoDB Atlas Docs: https://docs.atlas.mongodb.com
"""

    with open('ENV_QUICK_REFERENCE.md', 'w') as f:
        f.write(quick_ref)
    
    # Create deployment validation script
    validation_script = """#!/usr/bin/env python3
import os
import sys
from urllib.parse import urlparse

def validate_env():
    required_vars = {
        'Railway': [
            'API_HOST', 'API_PORT', 'JWT_SECRET', 'GOOGLE_API_KEY',
            'MONGODB_URI', 'CORS_ORIGINS'
        ],
        'Vercel': [
            'NEXT_PUBLIC_API_URL'
        ]
    }
    
    print("🔍 Validating environment variables...")
    
    # Check which env file exists
    if os.path.exists('.env.railway'):
        print("\\nChecking Railway environment...")
        with open('.env.railway', 'r') as f:
            content = f.read()
            
        missing = []
        for var in required_vars['Railway']:
            if var not in content or f"{var}=your-" in content or f"{var}=${{{{" in content:
                if var not in ['API_PORT', 'DATABASE_URL', 'REDIS_URL', 'CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND']:
                    missing.append(var)
        
        if missing:
            print(f"❌ Missing or placeholder values: {', '.join(missing)}")
        else:
            print("✅ All Railway variables configured!")
    
    if os.path.exists('.env.vercel'):
        print("\\nChecking Vercel environment...")
        with open('.env.vercel', 'r') as f:
            content = f.read()
            
        if 'NEXT_PUBLIC_API_URL=https://your-backend' in content:
            print("❌ NEXT_PUBLIC_API_URL needs to be updated with your Railway URL")
        else:
            print("✅ Vercel variables configured!")

if __name__ == "__main__":
    validate_env()
"""

    with open('validate-env.py', 'w') as f:
        f.write(validation_script)
    
    os.chmod('validate-env.py', 0o755)
    
    print("\n✅ Environment files generated successfully!\n")
    print("📁 Files created:")
    print("  - .env.railway (Production backend)")
    print("  - .env.vercel (Production frontend)")
    print("  - .env.local (Local development reference)")
    print("  - ENV_QUICK_REFERENCE.md (Important info & secrets)")
    print("  - validate-env.py (Validation script)")
    print("\n⚠️  IMPORTANT: Update the placeholder values:")
    print("  1. MONGODB_URI - Get from MongoDB Atlas")
    print("  2. GOOGLE_API_KEY - Get from Google Cloud")
    print("  3. CORS_ORIGINS - Add your Vercel URL")
    print("  4. NEXT_PUBLIC_API_URL - Add your Railway URL")
    print("\n📖 See ENV_QUICK_REFERENCE.md for all generated secrets and next steps")

if __name__ == "__main__":
    main()