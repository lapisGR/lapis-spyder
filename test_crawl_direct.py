#!/usr/bin/env python3
"""
Test crawling functionality directly
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_crawl():
    """Test crawling functionality directly"""
    try:
        from src.crawler.tasks import crawl_website
        from src.config import settings
        
        print("🔍 Testing crawl functionality...")
        print(f"URL: https://docs.hud.so/quickstart")
        print("=" * 50)
        
        # Create a simple job config
        job_config = {
            "url": "https://docs.hud.so/quickstart",
            "max_pages": 5,
            "max_depth": 2,
            "user_id": "test-user",
            "website_id": "test-website"
        }
        
        # Test the crawl function directly
        print("🚀 Starting crawl...")
        result = crawl_website.delay(job_config)
        print(f"✅ Crawl task submitted: {result.id}")
        
        # Wait a bit for the task to process
        print("⏳ Waiting for crawl to process...")
        import time
        time.sleep(10)
        
        # Check result
        if result.ready():
            crawl_result = result.get()
            print(f"✅ Crawl completed: {crawl_result}")
        else:
            print("⏳ Crawl still in progress...")
            print(f"Task state: {result.state}")
            
    except Exception as e:
        print(f"❌ Crawl test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crawl())