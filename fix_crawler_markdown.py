#!/usr/bin/env python3
"""
Fix the crawler markdown storage issue.
This script addresses the async/sync mismatch and ensures markdown is properly stored.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def fix_mongodb_operations():
    """Add synchronous versions of MongoDB operations."""
    
    mongodb_sync_code = '''
    @staticmethod
    def insert_markdown_sync(page_id: str, website_id: str, url: str,
                           raw_markdown: str, structured_markdown: str = None,
                           metadata: dict = None, prompt_used: str = None):
        """Insert markdown document (synchronous version)."""
        collection = get_mongo_collection("markdown_documents", async_mode=False)
        
        # Check if document exists
        existing = collection.find_one({"page_id": page_id})
        version = 1 if not existing else existing.get("version", 0) + 1
        
        document = {
            "page_id": page_id,
            "website_id": website_id,
            "url": url,
            "raw_markdown": raw_markdown,
            "structured_markdown": structured_markdown,
            "metadata": metadata or {},
            "gemini_prompt_used": prompt_used,
            "processed_at": datetime.utcnow(),
            "version": version
        }
        
        if existing:
            result = collection.replace_one(
                {"page_id": page_id},
                document
            )
            return str(existing["_id"])
        else:
            result = collection.insert_one(document)
            return str(result.inserted_id)
    
    @staticmethod
    def insert_html_sync(crawl_job_id: str, page_id: str, url: str, 
                        html: str, headers: dict, status_code: int):
        """Insert raw HTML document (synchronous version)."""
        collection = get_mongo_collection("raw_html", async_mode=False)
        
        document = {
            "crawl_job_id": crawl_job_id,
            "page_id": page_id,
            "url": url,
            "raw_html": html,
            "headers": headers,
            "status_code": status_code,
            "crawled_at": datetime.utcnow(),
            "content_type": headers.get("content-type", "text/html"),
            "size_bytes": len(html.encode("utf-8"))
        }
        
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    def get_markdown_sync(page_id: str):
        """Get markdown document by page ID (synchronous version)."""
        collection = get_mongo_collection("markdown_documents", async_mode=False)
        return collection.find_one({"page_id": page_id})
    '''
    
    print("Add this code to src/database/mongodb.py after the MongoDBOperations class methods:")
    print(mongodb_sync_code)

def fix_crawler_tasks():
    """Fix the crawler tasks to use synchronous MongoDB operations."""
    
    tasks_fix = '''
def process_crawled_page_sync(crawl_job_id: str, website_id: str, url: str,
                             html: str, status_code: int, headers: Dict,
                             error: Optional[str] = None) -> Optional[Dict]:
    """Process a single crawled page (synchronous version)."""
    try:
        # Check if page should be processed
        if error or status_code >= 400 or not html:
            logger.warning(f"Skipping page {url}: status={status_code}, error={error}")
            return None
        
        # Extract content
        extracted = extract_content(html, url)
        
        # Convert to markdown
        markdown_content = html_to_markdown(html, url)
        
        # Process markdown
        markdown_doc = process_markdown(
            markdown_content,
            url=url,
            title=extracted.get("title", ""),
            metadata=extracted.get("metadata", {})
        )
        
        # Calculate content hash
        content_hash = hash_content(html)
        
        # Store in database
        page_id = _store_page_data_sync(
            crawl_job_id=crawl_job_id,
            website_id=website_id,
            url=url,
            content_hash=content_hash,
            title=extracted.get("title", ""),
            meta_description=extracted.get("description", "")
        )
        
        # Store HTML in MongoDB
        MongoDBOperations.insert_html_sync(
            crawl_job_id=crawl_job_id,
            page_id=page_id,
            url=url,
            html=html,
            headers=headers,
            status_code=status_code
        )
        
        # Store markdown in MongoDB with structured content
        MongoDBOperations.insert_markdown_sync(
            page_id=page_id,
            website_id=website_id,
            url=url,
            raw_markdown=markdown_content,
            structured_markdown=markdown_doc.content,  # Use the processed content
            metadata=markdown_doc.metadata
        )
        
        logger.info(f"Successfully stored markdown for page {url} (id: {page_id})")
        
        return {
            "page_id": page_id,
            "url": url,
            "title": extracted.get("title", ""),
            "content_hash": content_hash,
            "word_count": extracted.get("word_count", 0),
            "links_count": len(extracted.get("links", [])),
            "images_count": len(extracted.get("images", []))
        }
        
    except Exception as e:
        logger.error(f"Failed to process page {url}: {e}", exc_info=True)
        return None


def _store_page_data_sync(crawl_job_id: str, website_id: str, url: str,
                         content_hash: str, title: str, meta_description: str) -> str:
    """Store page data in PostgreSQL (synchronous version)."""
    from sqlalchemy import text
    
    with get_db_context() as db:
        # Check if page exists
        result = db.execute(
            text("SELECT id FROM pages WHERE website_id = :website_id AND url = :url"),
            {"website_id": website_id, "url": url}
        )
        existing_page = result.fetchone()
        
        if existing_page:
            # Update existing page
            page_id = str(existing_page[0])
            db.execute(
                text("""
                UPDATE pages 
                SET content_hash = :content_hash, title = :title, 
                    meta_description = :meta_description,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """),
                {
                    "content_hash": content_hash,
                    "title": title,
                    "meta_description": meta_description,
                    "id": page_id
                }
            )
            db.commit()
        else:
            # Insert new page
            result = db.execute(
                text("""
                INSERT INTO pages (website_id, url, url_path, content_hash, 
                                 title, meta_description)
                VALUES (:website_id, :url, :url_path, :content_hash, 
                        :title, :meta_description)
                RETURNING id
                """),
                {
                    "website_id": website_id,
                    "url": url,
                    "url_path": url,
                    "content_hash": content_hash,
                    "title": title,
                    "meta_description": meta_description
                }
            )
            db.commit()
            page_id = str(result.fetchone()[0])
        
        return page_id
    '''
    
    print("\n\nReplace the async process_crawled_page function in tasks.py with:")
    print(tasks_fix)
    
    print("\n\nThen update the crawl_website_task function to use the sync version:")
    print("""
# In crawl_website_task, replace this section:
# for result in crawl_results.get("results", []):
#     try:
#         # Process each page
#         page_data = loop.run_until_complete(
#             process_crawled_page(
#                 ...
#             )
#         )

# With this:
for result in crawl_results.get("results", []):
    try:
        # Process each page using synchronous version
        page_data = process_crawled_page_sync(
            crawl_job_id=crawl_job_id,
            website_id=website_id,
            url=result.url,
            html=result.content,
            status_code=result.status_code,
            headers=result.headers,
            error=result.error
        )
    """)

def main():
    print("=" * 80)
    print("Crawler Markdown Storage Fix")
    print("=" * 80)
    print("\nThe issue: async MongoDB operations are being called from sync Celery tasks")
    print("The fix: Create synchronous versions of the MongoDB operations\n")
    
    fix_mongodb_operations()
    print("\n" + "=" * 80 + "\n")
    fix_crawler_tasks()
    
    print("\n" + "=" * 80)
    print("\nAlso add this import to src/crawler/tasks.py:")
    print("from datetime import datetime")
    print("from sqlalchemy import text")
    
    print("\n\nAfter making these changes:")
    print("1. Restart the Celery worker")
    print("2. Run a new crawl to test")
    print("3. Check MongoDB to verify markdown is stored")

if __name__ == "__main__":
    main()