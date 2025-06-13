#\!/usr/bin/env python3
"""Re-process all existing pages with the fixed markdown converter."""

from datetime import datetime
from src.database.mongodb import get_mongo_collection
from src.database.postgres import SessionLocal
from src.crawler.processor import HTMLProcessor
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reprocess_all_pages():
    """Re-process all pages with fixed code block extraction."""
    db = SessionLocal()
    
    # Get HUD website
    website = db.execute(
        text("SELECT id, domain FROM websites WHERE domain = 'docs.hud.so'")
    ).fetchone()
    
    if not website:
        logger.error("HUD website not found")
        return
        
    website_id = str(website[0])
    domain = website[1]
    logger.info(f"Processing website: {domain} ({website_id})")
    
    # Get all pages for this website
    pages = db.execute(
        text("SELECT id, url FROM pages WHERE website_id = :website_id"),
        {"website_id": website_id}
    ).fetchall()
    
    logger.info(f"Found {len(pages)} pages to reprocess")
    
    # Get MongoDB collections
    html_collection = get_mongo_collection("html_content")
    markdown_collection = get_mongo_collection("markdown_documents")
    
    processor = HTMLProcessor()
    processed_count = 0
    code_blocks_total = 0
    
    for page in pages:
        page_id = str(page[0])
        url = page[1]
        
        # Get HTML content
        html_doc = html_collection.find_one({"page_id": page_id})
        if not html_doc or not html_doc.get("html"):
            logger.warning(f"No HTML content for page {url}")
            continue
        
        # Re-process with fixed processor
        try:
            html = html_doc["html"]
            markdown = processor.html_to_markdown(html, url)
            code_block_count = markdown.count("```") // 2
            code_blocks_total += code_block_count
            
            # Update MongoDB document
            result = markdown_collection.update_one(
                {"page_id": page_id},
                {
                    "$set": {
                        "raw_markdown": markdown,
                        "updated_at": datetime.utcnow(),
                        "processor_version": "2.0",
                        "metadata.code_blocks_count": code_block_count
                    }
                }
            )
            
            processed_count += 1
            
            # Log pages with code blocks
            if code_block_count > 0:
                logger.info(f"  {url}: {code_block_count} code blocks")
                
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
    
    logger.info(f"Completed\! Processed {processed_count} pages")
    logger.info(f"Total code blocks found: {code_blocks_total}")
    
    db.close()

if __name__ == "__main__":
    reprocess_all_pages()
