"""Crawler Celery tasks."""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from celery import Task
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.celery import app
from src.database.postgres import get_db_context
from src.database.mongodb import MongoDBOperations
from src.crawler.spider_wrapper import SpiderConfig, crawl_website as spider_crawl
from src.crawler.processor import extract_content, html_to_markdown
from src.crawler.markdown import process_markdown
from src.utils.logging import get_logger
from src.utils.hashing import hash_content

logger = get_logger(__name__)


@app.task(bind=True, name="crawl_website")
def crawl_website_task(self: Task, crawl_job_id: str, website_id: str, 
                      website_url: str, config: Dict) -> Dict:
    """Crawl a website and store results."""
    logger.info(f"Starting crawl job {crawl_job_id} for website {website_id}")
    
    try:
        # Update job status
        _update_crawl_job(crawl_job_id, "running")
        
        # Create spider config
        spider_config = SpiderConfig(
            url=website_url,
            max_pages=config.get("max_pages", 100),
            max_depth=config.get("max_depth", 3),
            concurrent_requests=config.get("concurrent_requests", 10),
            respect_robots_txt=config.get("respect_robots_txt", True),
            user_agent=config.get("user_agent", "Lapis-Spider/1.0"),
            crawl_delay=config.get("crawl_delay", 0.5),
            allowed_domains=config.get("allowed_domains", []),
            blacklist_patterns=config.get("blacklist_patterns", []),
            whitelist_patterns=config.get("whitelist_patterns", [])
        )
        
        # Run crawler in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            crawl_results = loop.run_until_complete(
                spider_crawl(
                    website_url,
                    max_pages=spider_config.max_pages,
                    max_depth=spider_config.max_depth,
                    concurrent_requests=spider_config.concurrent_requests,
                    respect_robots_txt=spider_config.respect_robots_txt,
                    user_agent=spider_config.user_agent,
                    crawl_delay=spider_config.crawl_delay,
                    allowed_domains=spider_config.allowed_domains,
                    blacklist_patterns=spider_config.blacklist_patterns,
                    whitelist_patterns=spider_config.whitelist_patterns
                )
            )
        finally:
            loop.close()
        
        # Process results
        processed_pages = []
        failed_pages = []
        
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
                
                if page_data:
                    processed_pages.append(page_data)
                else:
                    failed_pages.append({
                        "url": result.url,
                        "error": result.error or "Processing failed"
                    })
                    
            except Exception as e:
                logger.error(f"Failed to process page {result.url}: {e}")
                failed_pages.append({
                    "url": result.url,
                    "error": str(e)
                })
        
        # Update job with results
        job_stats = {
            "total_pages": crawl_results.get("total_pages", 0),
            "successful_pages": len(processed_pages),
            "failed_pages": len(failed_pages),
            "total_size_bytes": crawl_results.get("total_size_bytes", 0),
            "duration_seconds": crawl_results.get("duration_seconds", 0)
        }
        
        _update_crawl_job(
            crawl_job_id, 
            "completed",
            pages_crawled=len(processed_pages),
            statistics=job_stats
        )
        
        logger.info(f"Crawl job {crawl_job_id} completed: {len(processed_pages)} pages processed")
        
        # Trigger AI processing for crawled pages
        if processed_pages:
            from src.ai.tasks import batch_process_pages_task
            page_ids = [p["page_id"] for p in processed_pages]
            batch_process_pages_task.delay(website_id, page_ids)
            logger.info(f"Queued AI processing for {len(page_ids)} pages")
        
        return {
            "crawl_job_id": crawl_job_id,
            "website_id": website_id,
            "status": "completed",
            "statistics": job_stats,
            "processed_pages": len(processed_pages),
            "failed_pages": failed_pages
        }
        
    except Exception as e:
        logger.error(f"Crawl job {crawl_job_id} failed: {e}")
        _update_crawl_job(
            crawl_job_id,
            "failed",
            error_message=str(e)
        )
        raise


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


async def process_crawled_page(crawl_job_id: str, website_id: str, url: str,
                              html: str, status_code: int, headers: Dict,
                              error: Optional[str] = None) -> Optional[Dict]:
    """Process a single crawled page."""
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
        page_id = await _store_page_data(
            crawl_job_id=crawl_job_id,
            website_id=website_id,
            url=url,
            content_hash=content_hash,
            title=extracted.get("title", ""),
            meta_description=extracted.get("description", "")
        )
        
        # Store HTML in MongoDB
        await MongoDBOperations.insert_html(
            crawl_job_id=crawl_job_id,
            page_id=page_id,
            url=url,
            html=html,
            headers=headers,
            status_code=status_code
        )
        
        # Store markdown in MongoDB
        await MongoDBOperations.insert_markdown(
            page_id=page_id,
            website_id=website_id,
            url=url,
            raw_markdown=markdown_content,
            metadata=markdown_doc.metadata
        )
        
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
        logger.error(f"Failed to process page {url}: {e}")
        return None


def _store_page_data_sync(crawl_job_id: str, website_id: str, url: str,
                         content_hash: str, title: str, meta_description: str) -> str:
    """Store page data in PostgreSQL (synchronous version)."""
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


async def _store_page_data(crawl_job_id: str, website_id: str, url: str,
                          content_hash: str, title: str, meta_description: str) -> str:
    """Store page data in PostgreSQL."""
    with get_db_context() as db:
        # Check if page exists
        existing_page = db.execute(
            text("SELECT id FROM pages WHERE website_id = :website_id AND url = :url"),
            {"website_id": website_id, "url": url}
        ).fetchone()
        
        if existing_page:
            # Update existing page
            page_id = str(existing_page[0])
            db.execute(
                text("""
                UPDATE pages 
                SET content_hash = :content_hash, title = :title, meta_description = :meta_description,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :page_id
                """),
                {"content_hash": content_hash, "title": title, "meta_description": meta_description, "page_id": page_id}
            )
        else:
            # Insert new page
            result = db.execute(
                text("""
                INSERT INTO pages (website_id, url, url_path, content_hash, 
                                 title, meta_description)
                VALUES (:website_id, :url, :url_path, :content_hash, :title, :meta_description)
                RETURNING id
                """),
                {"website_id": website_id, "url": url, "url_path": url, 
                 "content_hash": content_hash, "title": title, "meta_description": meta_description}
            )
            page_id = str(result.fetchone()[0])
        
        return page_id


def _update_crawl_job(crawl_job_id: str, status: str, pages_crawled: int = None,
                     error_message: str = None, statistics: Dict = None):
    """Update crawl job status in database."""
    with get_db_context() as db:
        update_fields = ["status = :status"]
        params = {"status": status, "crawl_job_id": crawl_job_id}
        
        if status == "running":
            update_fields.append("started_at = CURRENT_TIMESTAMP")
        elif status in ["completed", "failed"]:
            update_fields.append("completed_at = CURRENT_TIMESTAMP")
        
        if pages_crawled is not None:
            update_fields.append("pages_crawled = :pages_crawled")
            params["pages_crawled"] = pages_crawled
        
        if error_message:
            update_fields.append("error_message = :error_message")
            params["error_message"] = error_message
        
        if statistics:
            update_fields.append("statistics = CAST(:statistics AS jsonb)")
            # Properly serialize dictionary to JSON string
            params["statistics"] = json.dumps(statistics) if isinstance(statistics, dict) else statistics
        
        query = f"UPDATE crawl_jobs SET {', '.join(update_fields)} WHERE id = :crawl_job_id"
        db.execute(text(query), params)


@app.task(name="process_page_content")
def process_page_content(page_id: str, website_id: str):
    """Process page content with AI (Phase 4 placeholder)."""
    logger.info(f"Processing content for page {page_id}")
    
    # This will be implemented in Phase 4
    return {
        "page_id": page_id,
        "status": "pending",
        "message": "AI processing not yet implemented"
    }