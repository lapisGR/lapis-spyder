"""AI processing Celery tasks."""

import asyncio
from typing import Dict, List, Optional
import json

from celery import Task

from src.celery import app
from src.database.mongodb import MongoDBOperations, get_mongo_collection
from src.database.postgres import get_db_context
from src.ai.gemini import (
    structure_markdown, 
    generate_llms_txt_entry,
    extract_code_examples,
    generate_content_index
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


@app.task(bind=True, name="process_page_with_ai")
def process_page_with_ai(self: Task, page_id: str, website_id: str) -> Dict:
    """Process page content with AI enhancement."""
    logger.info(f"Processing page {page_id} with AI")
    
    try:
        # Get page data from MongoDB
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            markdown_doc = loop.run_until_complete(
                MongoDBOperations.get_markdown(page_id)
            )
            
            if not markdown_doc:
                logger.error(f"No markdown found for page {page_id}")
                return {
                    "page_id": page_id,
                    "status": "failed",
                    "error": "No markdown content found"
                }
            
            # Get page metadata from PostgreSQL
            with get_db_context() as db:
                page_data = db.execute(
                    "SELECT url, title FROM pages WHERE id = %s",
                    (page_id,)
                ).fetchone()
                
                if not page_data:
                    logger.error(f"Page {page_id} not found in database")
                    return {
                        "page_id": page_id,
                        "status": "failed",
                        "error": "Page not found"
                    }
                
                url = page_data[0]
                title = page_data[1]
            
            # Structure markdown with AI
            structured_result = loop.run_until_complete(
                structure_markdown(
                    markdown_doc.get("raw_markdown", ""),
                    url,
                    title
                )
            )
            
            # Extract code examples
            code_examples = loop.run_until_complete(
                extract_code_examples(
                    structured_result.get("structured_markdown", "")
                )
            )
            
            # Update MongoDB with structured content
            loop.run_until_complete(
                MongoDBOperations.insert_markdown(
                    page_id=page_id,
                    website_id=website_id,
                    url=url,
                    raw_markdown=markdown_doc.get("raw_markdown", ""),
                    structured_markdown=structured_result.get("structured_markdown", ""),
                    metadata={
                        **markdown_doc.get("metadata", {}),
                        "ai_processed": True,
                        "summary": structured_result.get("summary", ""),
                        "key_topics": structured_result.get("key_topics", []),
                        "page_type": structured_result.get("page_type", "other"),
                        "main_concepts": structured_result.get("main_concepts", []),
                        "code_languages": structured_result.get("code_languages", []),
                        "quality_score": structured_result.get("quality_score", 0.5),
                        "code_examples": code_examples
                    },
                    prompt_used="structure_markdown"
                )
            )
            
            logger.info(f"Successfully processed page {page_id} with AI")
            
            return {
                "page_id": page_id,
                "status": "completed",
                "summary": structured_result.get("summary", ""),
                "key_topics": structured_result.get("key_topics", []),
                "page_type": structured_result.get("page_type", "other"),
                "quality_score": structured_result.get("quality_score", 0.5)
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to process page {page_id} with AI: {e}")
        return {
            "page_id": page_id,
            "status": "failed",
            "error": str(e)
        }


@app.task(bind=True, name="generate_website_index")
def generate_website_index_task(self: Task, website_id: str) -> Dict:
    """Generate llms.txt style index for a website."""
    logger.info(f"Generating index for website {website_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get all processed pages for the website
            collection = get_mongo_collection("markdown_documents")
            pages = list(collection.find(
                {"website_id": website_id, "metadata.ai_processed": True}
            ).limit(100))
            
            if not pages:
                logger.warning(f"No processed pages found for website {website_id}")
                return {
                    "website_id": website_id,
                    "status": "failed",
                    "error": "No processed pages found"
                }
            
            # Generate llms.txt entries for each page
            llms_entries = []
            for page in pages:
                page_data = {
                    "url": page.get("url", ""),
                    "title": page.get("metadata", {}).get("title", ""),
                    "summary": page.get("metadata", {}).get("summary", ""),
                    "key_topics": page.get("metadata", {}).get("key_topics", []),
                    "page_type": page.get("metadata", {}).get("page_type", "other"),
                    "path": page.get("url", "").replace("https://", "").replace("http://", "")
                }
                
                entry = loop.run_until_complete(
                    generate_llms_txt_entry(page_data)
                )
                llms_entries.append(entry)
            
            # Generate overall index
            page_summaries = [
                {
                    "title": p.get("metadata", {}).get("title", "Untitled"),
                    "url": p.get("url", ""),
                    "summary": p.get("metadata", {}).get("summary", "")
                }
                for p in pages
            ]
            
            index_content = loop.run_until_complete(
                generate_content_index(page_summaries)
            )
            
            # Combine into final llms.txt format
            llms_txt_content = f"""# Website Documentation Index

Generated with Lapis Spider - AI-Enhanced Web Documentation

## Overview

{index_content}

## Pages

{"".join(f"\n{entry}\n" for entry in llms_entries)}

---
Generated on: {asyncio.get_event_loop().time()}
Total Pages: {len(pages)}
"""
            
            # Store in MongoDB
            collection = get_mongo_collection("website_indexes")
            collection.update_one(
                {"website_id": website_id},
                {
                    "$set": {
                        "website_id": website_id,
                        "index_content": llms_txt_content,
                        "page_tree": {
                            "total_pages": len(pages),
                            "pages": [
                                {
                                    "id": str(p.get("_id", "")),
                                    "url": p.get("url", ""),
                                    "title": p.get("metadata", {}).get("title", ""),
                                    "type": p.get("metadata", {}).get("page_type", "other")
                                }
                                for p in pages
                            ]
                        },
                        "generated_at": asyncio.get_event_loop().time(),
                        "version": 1
                    }
                },
                upsert=True
            )
            
            logger.info(f"Successfully generated index for website {website_id}")
            
            return {
                "website_id": website_id,
                "status": "completed",
                "total_pages": len(pages),
                "index_size": len(llms_txt_content)
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to generate index for website {website_id}: {e}")
        return {
            "website_id": website_id,
            "status": "failed",
            "error": str(e)
        }


@app.task(bind=True, name="batch_process_pages")
def batch_process_pages_task(self: Task, website_id: str, page_ids: List[str]) -> Dict:
    """Batch process multiple pages with AI."""
    logger.info(f"Batch processing {len(page_ids)} pages for website {website_id}")
    
    results = {
        "website_id": website_id,
        "total": len(page_ids),
        "processed": 0,
        "failed": 0,
        "page_results": []
    }
    
    for page_id in page_ids:
        try:
            result = process_page_with_ai(page_id, website_id)
            if result["status"] == "completed":
                results["processed"] += 1
            else:
                results["failed"] += 1
            results["page_results"].append(result)
        except Exception as e:
            logger.error(f"Failed to process page {page_id}: {e}")
            results["failed"] += 1
            results["page_results"].append({
                "page_id": page_id,
                "status": "failed",
                "error": str(e)
            })
    
    # Generate index after batch processing
    if results["processed"] > 0:
        generate_website_index_task.delay(website_id)
    
    return results