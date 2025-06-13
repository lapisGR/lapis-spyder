#!/usr/bin/env python3
"""
Quick test script to verify database connections
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_postgresql():
    """Test PostgreSQL connection"""
    try:
        from src.database.postgres import check_db_connection
        result = check_db_connection()
        print(f"✅ PostgreSQL connection: {'SUCCESS' if result else 'FAILED'}")
        return result
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")
        return False

def test_mongodb():
    """Test MongoDB connection"""
    try:
        from src.database.mongodb import check_mongodb_connection_sync
        result = check_mongodb_connection_sync()
        print(f"✅ MongoDB connection: {'SUCCESS' if result else 'FAILED'}")
        return result
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    try:
        from src.database.redis import check_redis_connection
        result = check_redis_connection()
        print(f"✅ Redis connection: {'SUCCESS' if result else 'FAILED'}")
        return result
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def main():
    print("🔍 Testing Database Connections...")
    print("=" * 40)
    
    pg_ok = test_postgresql()
    mongo_ok = test_mongodb()
    redis_ok = test_redis()
    
    print("=" * 40)
    if pg_ok and mongo_ok and redis_ok:
        print("🎉 All database connections successful!")
    else:
        print("⚠️  Some connections failed. Check configuration.")
        
    # Show current config
    print("\n📋 Current Configuration:")
    try:
        from src.config import settings
        print(f"PostgreSQL: {settings.postgres_user}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
        print(f"MongoDB: {settings.mongodb_connection_url}")
        print(f"Redis: {settings.redis_connection_url}")
    except Exception as e:
        print(f"Config error: {e}")

if __name__ == "__main__":
    main()