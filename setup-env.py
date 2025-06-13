#!/usr/bin/env python3
"""
Environment Setup Script for Lapis LLMT Spider
Helps configure environment variables for Railway and Vercel deployment
"""

import os
import secrets
import json
import base64
from pathlib import Path
from typing import Dict, Any

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def generate_jwt_secret(length: int = 64) -> str:
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(length)

def generate_password(length: int = 32) -> str:
    """Generate a secure password"""
    return secrets.token_urlsafe(length)

def get_existing_env() -> Dict[str, str]:
    """Read existing .env file if it exists"""
    env_vars = {}
    env_file = Path('.env')
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def create_railway_env() -> Dict[str, str]:
    """Create Railway production environment variables"""
    existing = get_existing_env()
    
    print(f"\n{BLUE}🚂 Setting up Railway Environment Variables{NC}")
    print(f"{YELLOW}Note: Some values will be auto-provided by Railway{NC}\n")
    
    env_vars = {
        # API Configuration
        "API_HOST": "0.0.0.0",
        "API_PORT": "$PORT",  # Railway provides this
        "ENVIRONMENT": "production",
        
        # Database URLs (Railway provides these)
        "DATABASE_URL": "${{Postgres.DATABASE_URL}}",
        "REDIS_URL": "${{Redis.REDIS_URL}}",
        
        # Security
        "JWT_SECRET": generate_jwt_secret(),
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_DELTA": "30",
        
        # Celery (uses Railway Redis)
        "CELERY_BROKER_URL": "${{Redis.REDIS_URL}}",
        "CELERY_RESULT_BACKEND": "${{Redis.REDIS_URL}}",
        
        # Monitoring
        "PROMETHEUS_ENABLED": "true",
        "LOG_LEVEL": "INFO",
    }
    
    # MongoDB Atlas
    print(f"{YELLOW}MongoDB Atlas Configuration:{NC}")
    print("1. Go to https://mongodb.com/atlas")
    print("2. Create a free cluster")
    print("3. Get your connection string")
    mongodb_uri = input(f"\n{GREEN}Enter MongoDB Atlas URI{NC} (or press Enter to set later): ").strip()
    if mongodb_uri:
        env_vars["MONGODB_URI"] = mongodb_uri
    else:
        env_vars["MONGODB_URI"] = "mongodb+srv://username:password@cluster.mongodb.net/lapis?retryWrites=true&w=majority"
    
    # Google Gemini API
    print(f"\n{YELLOW}Google Gemini API Configuration:{NC}")
    print("1. Go to https://makersuite.google.com/app/apikey")
    print("2. Create an API key")
    
    # Check if we have existing Gemini key
    if existing.get('GEMINI_API_KEY') and existing['GEMINI_API_KEY'] != 'your-gemini-api-key':
        use_existing = input(f"\n{GREEN}Found existing Gemini API key. Use it? (y/n){NC}: ").lower()
        if use_existing == 'y':
            env_vars["GOOGLE_API_KEY"] = existing['GEMINI_API_KEY']
        else:
            gemini_key = input(f"{GREEN}Enter new Gemini API key{NC}: ").strip()
            env_vars["GOOGLE_API_KEY"] = gemini_key
    else:
        gemini_key = input(f"\n{GREEN}Enter Gemini API key{NC} (or press Enter to set later): ").strip()
        env_vars["GOOGLE_API_KEY"] = gemini_key or "your-gemini-api-key"
    
    # CORS Configuration
    print(f"\n{YELLOW}Frontend Configuration:{NC}")
    frontend_url = input(f"{GREEN}Enter your Vercel frontend URL{NC} (e.g., https://myapp.vercel.app): ").strip()
    if not frontend_url:
        frontend_url = "https://your-app.vercel.app"
    
    cors_origins = [frontend_url]
    if frontend_url != "http://localhost:3000":
        cors_origins.append("http://localhost:3000")  # For local development
    
    env_vars["CORS_ORIGINS"] = json.dumps(cors_origins)
    
    # Optional: Sentry
    print(f"\n{YELLOW}Optional: Error Monitoring{NC}")
    sentry_dsn = input(f"{GREEN}Enter Sentry DSN{NC} (or press Enter to skip): ").strip()
    if sentry_dsn:
        env_vars["SENTRY_DSN"] = sentry_dsn
    
    return env_vars

def create_vercel_env(backend_url: str = None) -> Dict[str, str]:
    """Create Vercel frontend environment variables"""
    print(f"\n{BLUE}▲ Setting up Vercel Environment Variables{NC}")
    
    if not backend_url:
        backend_url = input(f"{GREEN}Enter your Railway backend URL{NC} (e.g., https://myapp.railway.app): ").strip()
        if not backend_url:
            backend_url = "https://your-backend.railway.app"
    
    env_vars = {
        "NEXT_PUBLIC_API_URL": backend_url,
    }
    
    # Optional: Analytics
    print(f"\n{YELLOW}Optional: Analytics{NC}")
    ga_id = input(f"{GREEN}Enter Google Analytics ID{NC} (or press Enter to skip): ").strip()
    if ga_id:
        env_vars["NEXT_PUBLIC_GA_ID"] = ga_id
    
    return env_vars

def save_env_files(railway_vars: Dict[str, str], vercel_vars: Dict[str, str]):
    """Save environment variables to files"""
    # Save Railway env
    railway_file = Path('.env.railway')
    with open(railway_file, 'w') as f:
        f.write("# Railway Environment Variables\n")
        f.write("# Copy these to your Railway dashboard\n\n")
        for key, value in railway_vars.items():
            f.write(f"{key}={value}\n")
    
    # Save Vercel env
    vercel_file = Path('.env.vercel')
    with open(vercel_file, 'w') as f:
        f.write("# Vercel Environment Variables\n")
        f.write("# Copy these to your Vercel dashboard\n\n")
        for key, value in vercel_vars.items():
            f.write(f"{key}={value}\n")
    
    # Create a Railway CLI env file
    railway_cli_file = Path('.env.railway.cli')
    with open(railway_cli_file, 'w') as f:
        f.write("# Railway CLI Environment Variables\n")
        f.write("# Use: railway run --envfile .env.railway.cli <command>\n\n")
        for key, value in railway_vars.items():
            # Skip Railway-specific variables for local testing
            if not value.startswith('${{'):
                f.write(f"{key}={value}\n")

def create_deployment_checklist():
    """Create a deployment checklist"""
    checklist = """
# 🚀 Deployment Checklist

## Railway Backend

1. [ ] Create Railway account at railway.app
2. [ ] Install Railway CLI: `brew install railway`
3. [ ] Create new Railway project
4. [ ] Add PostgreSQL database service
5. [ ] Add Redis database service
6. [ ] Deploy main application from GitHub
7. [ ] Copy environment variables from `.env.railway`
8. [ ] Deploy Celery worker service
9. [ ] Deploy Celery beat service
10. [ ] Test health endpoint: `https://your-app.railway.app/health`

## MongoDB Atlas

1. [ ] Create account at mongodb.com/atlas
2. [ ] Create free M0 cluster
3. [ ] Add your IP to whitelist (or allow all IPs for production)
4. [ ] Get connection string
5. [ ] Update MONGODB_URI in Railway

## Vercel Frontend

1. [ ] Create Vercel account at vercel.com
2. [ ] Install Vercel CLI: `npm i -g vercel`
3. [ ] Deploy frontend: `cd lapis-frontend && vercel --prod`
4. [ ] Copy environment variables from `.env.vercel`
5. [ ] Update CORS_ORIGINS in Railway with Vercel URL

## Post-Deployment

1. [ ] Initialize database: `railway run python scripts/setup_db.py`
2. [ ] Create admin user
3. [ ] Test login from frontend
4. [ ] Set up custom domains (optional)
5. [ ] Configure monitoring alerts (optional)

## Verification

- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] Authentication works (login/register)
- [ ] Can create and view crawl jobs
- [ ] Worker processes tasks
- [ ] Scheduled jobs run (check logs)
"""
    
    with open('DEPLOYMENT_CHECKLIST.md', 'w') as f:
        f.write(checklist)

def main():
    print(f"{GREEN}=== Lapis LLMT Spider Environment Setup ==={NC}")
    print(f"{YELLOW}This script helps you configure environment variables for deployment{NC}\n")
    
    # Check current directory
    if not Path('src').exists() or not Path('lapis-frontend').exists():
        print(f"{RED}Error: Please run this script from the project root directory{NC}")
        return
    
    # Setup type
    print("What would you like to set up?")
    print("1. Both Railway (backend) and Vercel (frontend)")
    print("2. Railway (backend) only")
    print("3. Vercel (frontend) only")
    
    choice = input(f"\n{GREEN}Enter choice (1-3){NC}: ").strip()
    
    railway_vars = {}
    vercel_vars = {}
    
    if choice in ['1', '2']:
        railway_vars = create_railway_env()
    
    if choice in ['1', '3']:
        # For option 1, we can suggest using the Railway URL
        backend_url = None
        if choice == '1' and railway_vars:
            backend_url = "https://your-app.railway.app"  # Placeholder
            print(f"\n{YELLOW}Note: Update NEXT_PUBLIC_API_URL with your actual Railway URL after deployment{NC}")
        
        vercel_vars = create_vercel_env(backend_url)
    
    # Save files
    if railway_vars or vercel_vars:
        save_env_files(railway_vars, vercel_vars)
        create_deployment_checklist()
        
        print(f"\n{GREEN}✅ Environment files created successfully!{NC}")
        print(f"\nFiles created:")
        if railway_vars:
            print(f"  - {BLUE}.env.railway{NC} - Copy to Railway dashboard")
            print(f"  - {BLUE}.env.railway.cli{NC} - For local testing with Railway CLI")
        if vercel_vars:
            print(f"  - {BLUE}.env.vercel{NC} - Copy to Vercel dashboard")
        print(f"  - {BLUE}DEPLOYMENT_CHECKLIST.md{NC} - Step-by-step deployment guide")
        
        print(f"\n{YELLOW}Next steps:{NC}")
        print("1. Review the generated environment files")
        print("2. Follow DEPLOYMENT_CHECKLIST.md")
        print("3. Deploy using: ./deploy.sh")
    
    # Security reminder
    print(f"\n{RED}⚠️  Security Reminder:{NC}")
    print("- Never commit .env files to Git")
    print("- Rotate JWT secrets regularly")
    print("- Use strong passwords for databases")
    print("- Keep API keys secure")

if __name__ == "__main__":
    main()