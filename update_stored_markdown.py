#!/usr/bin/env python3
"""
Update stored markdown with properly extracted code blocks.
"""

from src.database.mongodb import get_mongo_collection
from src.crawler.processor import html_processor
from src.utils.logging import get_logger

logger = get_logger(__name__)


def update_markdown_with_code_blocks():
    # Get collections
    html_collection = get_mongo_collection('raw_html')
    markdown_collection = get_mongo_collection('markdown_documents')
    
    # Get all HTML documents
    html_docs = list(html_collection.find())
    logger.info(f"Found {len(html_docs)} HTML documents to process")
    
    updated = 0
    for doc in html_docs:
        page_id = doc['page_id']
        url = doc['url']
        raw_html = doc.get('raw_html', '')
        
        if not raw_html:
            continue
            
        logger.info(f"Processing {url}")
        
        try:
            # Convert with improved processor
            markdown = html_processor.html_to_markdown(raw_html, url)
            
            # Check if we have code blocks
            code_count = markdown.count('```')
            if code_count > 0:
                logger.info(f"  Found {code_count // 2} code blocks")
            
            # Update markdown
            result = markdown_collection.update_one(
                {'page_id': page_id},
                {'$set': {'raw_markdown': markdown, 'improved': True}},
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id:
                updated += 1
                
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
    
    logger.info(f"Updated {updated} documents")


if __name__ == "__main__":
    update_markdown_with_code_blocks()