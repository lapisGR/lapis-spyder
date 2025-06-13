#!/usr/bin/env python3
"""
Test MongoDB connection specifically
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.database.mongodb import check_mongodb_connection_sync, get_sync_mongodb
    from src.config import settings
    
    print("🔍 Testing MongoDB Connection...")
    print(f"MongoDB URI: {settings.mongodb_connection_url}")
    print(f"MongoDB DB: {settings.mongodb_db}")
    print("=" * 50)
    
    # Test connection
    try:
        result = check_mongodb_connection_sync()
        print(f"✅ MongoDB sync connection: {'SUCCESS' if result else 'FAILED'}")
    except Exception as e:
        print(f"❌ MongoDB sync connection error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test client directly
    try:
        db = get_sync_mongodb()
        db.client.admin.command("ping")
        print("✅ Direct client ping: SUCCESS")
    except Exception as e:
        print(f"❌ Direct client ping error: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()