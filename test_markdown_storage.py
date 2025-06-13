#!/usr/bin/env python3
"""
Test script to verify markdown content is being stored properly in MongoDB.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.mongodb import get_sync_mongodb, MongoDBOperations
from src.database.postgres import get_db_context
from sqlalchemy import text


def check_markdown_storage():
    """Check if markdown content is stored in MongoDB."""
    print("🔍 Checking markdown storage in MongoDB...\n")
    
    # Get MongoDB connection
    db = get_sync_mongodb()
    markdown_collection = db["markdown_documents"]
    html_collection = db["raw_html"]
    
    # Count documents
    markdown_count = markdown_collection.count_documents({})
    html_count = html_collection.count_documents({})
    
    print(f"📊 Document counts:")
    print(f"  - HTML documents: {html_count}")
    print(f"  - Markdown documents: {markdown_count}")
    
    if markdown_count == 0:
        print("\n❌ No markdown documents found in MongoDB!")
        print("This confirms the storage issue.")
        return False
    
    # Check a sample markdown document
    print("\n📄 Sample markdown document:")
    sample = markdown_collection.find_one()
    if sample:
        print(f"  - Page ID: {sample.get('page_id')}")
        print(f"  - URL: {sample.get('url')}")
        print(f"  - Has raw_markdown: {'raw_markdown' in sample and bool(sample['raw_markdown'])}")
        print(f"  - Raw markdown length: {len(sample.get('raw_markdown', ''))}")
        print(f"  - Has structured_markdown: {'structured_markdown' in sample and bool(sample['structured_markdown'])}")
        print(f"  - Processed at: {sample.get('processed_at')}")
        
        # Show first 200 chars of markdown
        if sample.get('raw_markdown'):
            print(f"\n📝 First 200 chars of markdown:")
            print(sample['raw_markdown'][:200] + "...")
    
    return markdown_count > 0


def check_recent_crawls():
    """Check recent crawl jobs and their pages."""
    print("\n\n🕷️ Checking recent crawl jobs...\n")
    
    with get_db_context() as db:
        # Get recent crawl jobs
        result = db.execute(
            text("""
            SELECT id, website_id, status, pages_crawled, created_at
            FROM crawl_jobs
            ORDER BY created_at DESC
            LIMIT 5
            """)
        )
        crawl_jobs = result.fetchall()
        
        if not crawl_jobs:
            print("❌ No crawl jobs found!")
            return
        
        print(f"Found {len(crawl_jobs)} recent crawl jobs:")
        
        for job in crawl_jobs:
            job_id, website_id, status, pages_crawled, created_at = job
            print(f"\n📋 Crawl Job: {job_id}")
            print(f"  - Status: {status}")
            print(f"  - Pages crawled: {pages_crawled}")
            print(f"  - Created: {created_at}")
            
            # Check pages for this crawl
            result = db.execute(
                text("""
                SELECT p.id, p.url, p.title
                FROM pages p
                WHERE p.website_id = :website_id
                LIMIT 3
                """),
                {"website_id": website_id}
            )
            pages = result.fetchall()
            
            if pages:
                print(f"  - Sample pages:")
                for page in pages:
                    page_id, url, title = page
                    print(f"    • {title or 'No title'} ({url})")
                    
                    # Check if markdown exists for this page
                    markdown_doc = MongoDBOperations.get_markdown_sync(str(page_id))
                    if markdown_doc:
                        print(f"      ✅ Has markdown (length: {len(markdown_doc.get('raw_markdown', ''))})")
                    else:
                        print(f"      ❌ No markdown found!")


def test_direct_storage():
    """Test storing markdown directly to verify the sync methods work."""
    print("\n\n🧪 Testing direct markdown storage...\n")
    
    test_page_id = "test-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    test_website_id = "test-website"
    test_url = "https://example.com/test"
    test_markdown = """# Test Page

This is a test markdown document to verify storage is working correctly.

## Section 1
Some test content here.

## Section 2  
More test content.
"""
    
    try:
        # Store test markdown
        result = MongoDBOperations.insert_markdown_sync(
            page_id=test_page_id,
            website_id=test_website_id,
            url=test_url,
            raw_markdown=test_markdown,
            structured_markdown=test_markdown,
            metadata={"test": True, "created_at": datetime.utcnow().isoformat()}
        )
        
        print(f"✅ Successfully stored test markdown with ID: {result}")
        
        # Retrieve it
        retrieved = MongoDBOperations.get_markdown_sync(test_page_id)
        if retrieved:
            print(f"✅ Successfully retrieved test markdown")
            print(f"  - Contains raw_markdown: {bool(retrieved.get('raw_markdown'))}")
            print(f"  - Markdown matches: {retrieved.get('raw_markdown') == test_markdown}")
        else:
            print("❌ Failed to retrieve test markdown")
            
        # Clean up
        db = get_sync_mongodb()
        db["markdown_documents"].delete_one({"page_id": test_page_id})
        print("🧹 Cleaned up test document")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("=" * 80)
    print("Markdown Storage Test")
    print("=" * 80)
    
    # Check current storage
    has_markdown = check_markdown_storage()
    
    # Check recent crawls
    check_recent_crawls()
    
    # Test direct storage
    test_direct_storage()
    
    print("\n" + "=" * 80)
    if has_markdown:
        print("✅ Markdown storage appears to be working!")
        print("\nNext steps:")
        print("1. If markdown is old, run a new crawl to test the fix")
        print("2. Check export_to_folder.py to ensure it reads markdown correctly")
    else:
        print("❌ Markdown storage issue confirmed!")
        print("\nThe fix has been applied. Next steps:")
        print("1. Restart Celery workers: docker-compose restart celery")
        print("2. Run a new crawl to test the fix")
        print("3. Run this script again to verify markdown is stored")


if __name__ == "__main__":
    main()