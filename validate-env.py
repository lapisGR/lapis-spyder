#!/usr/bin/env python3
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
        print("\nChecking Railway environment...")
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
        print("\nChecking Vercel environment...")
        with open('.env.vercel', 'r') as f:
            content = f.read()
            
        if 'NEXT_PUBLIC_API_URL=https://your-backend' in content:
            print("❌ NEXT_PUBLIC_API_URL needs to be updated with your Railway URL")
        else:
            print("✅ Vercel variables configured!")

if __name__ == "__main__":
    validate_env()
