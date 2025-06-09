"""Content retrieval and processing API endpoints."""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.database.postgres import get_db
from src.database.mongodb import get_mongo_collection
from src.ai.tasks import process_page_with_ai, batch_process_pages_task
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models
class PageSummary(BaseModel):
    """Page summary information."""
    
    id: str
    url: str
    title: str
    content_hash: str
    last_modified: Optional[datetime]
    ai_processed: bool = False
    summary: Optional[str]
    page_type: Optional[str]
    
    class Config:
        from_attributes = True


class PageContent(BaseModel):
    """Full page content."""
    
    id: str
    url: str
    title: str
    raw_markdown: str
    structured_markdown: Optional[str]
    metadata: dict
    ai_processed: bool
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProcessingRequest(BaseModel):
    """Request to process pages with AI."""
    
    page_ids: List[str] = Field(..., min_items=1, max_items=100)


class ProcessingStatus(BaseModel):
    """Processing job status."""
    
    job_id: str
    status: str
    total_pages: int
    processed_pages: int
    failed_pages: int


# API Endpoints
@router.get("/{website_id}/pages", response_model=List[PageSummary])
async def list_website_pages(
    website_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    ai_processed_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all pages for a website."""
    # Verify website belongs to user
    website = db.execute(
        """
        SELECT id FROM websites 
        WHERE id = %s AND user_id = %s
        """,
        (website_id, str(current_user.id))
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Get pages from PostgreSQL
    query = """
        SELECT id, url, title, content_hash, last_modified
        FROM pages
        WHERE website_id = %s
        ORDER BY url
        LIMIT %s OFFSET %s
    """
    
    pages = db.execute(query, (website_id, limit, offset)).fetchall()
    
    # Get AI processing status from MongoDB
    collection = get_mongo_collection("markdown_documents")
    page_summaries = []
    
    for page in pages:
        page_id = str(page[0])
        
        # Check if processed
        mongo_doc = collection.find_one({"page_id": page_id})
        ai_processed = False
        summary = None
        page_type = None
        
        if mongo_doc and mongo_doc.get("metadata", {}).get("ai_processed"):
            ai_processed = True
            summary = mongo_doc["metadata"].get("summary")
            page_type = mongo_doc["metadata"].get("page_type")
        
        if not ai_processed_only or ai_processed:
            page_summaries.append(PageSummary(
                id=page_id,
                url=page[1],
                title=page[2] or "Untitled",
                content_hash=page[3],
                last_modified=page[4],
                ai_processed=ai_processed,
                summary=summary,
                page_type=page_type
            ))
    
    return page_summaries


@router.get("/{website_id}/page/{page_id}", response_model=PageContent)
async def get_page_content(
    website_id: str,
    page_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full content for a specific page."""
    # Verify page belongs to user's website
    page = db.execute(
        """
        SELECT p.id, p.url, p.title
        FROM pages p
        JOIN websites w ON p.website_id = w.id
        WHERE p.id = %s AND p.website_id = %s AND w.user_id = %s
        """,
        (page_id, website_id, str(current_user.id))
    ).fetchone()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Get content from MongoDB
    collection = get_mongo_collection("markdown_documents")
    mongo_doc = collection.find_one({"page_id": page_id})
    
    if not mongo_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page content not found"
        )
    
    return PageContent(
        id=page_id,
        url=page[1],
        title=page[2] or "Untitled",
        raw_markdown=mongo_doc.get("raw_markdown", ""),
        structured_markdown=mongo_doc.get("structured_markdown"),
        metadata=mongo_doc.get("metadata", {}),
        ai_processed=mongo_doc.get("metadata", {}).get("ai_processed", False),
        processed_at=mongo_doc.get("processed_at")
    )


@router.get("/{website_id}/llms.txt")
async def get_llms_txt(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get llms.txt format index for the website."""
    # Verify website belongs to user
    website = db.execute(
        """
        SELECT id, domain FROM websites 
        WHERE id = %s AND user_id = %s
        """,
        (website_id, str(current_user.id))
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Get index from MongoDB
    collection = get_mongo_collection("website_indexes")
    index_doc = collection.find_one({"website_id": website_id})
    
    if not index_doc or not index_doc.get("index_content"):
        # Generate basic index if not available
        content = f"""# {website[1]} Documentation

This website has not been fully processed yet.
Please run AI processing to generate a comprehensive index.

## Available Pages

Visit /content/{website_id}/pages to see all crawled pages.
"""
        return Response(content=content, media_type="text/plain")
    
    return Response(
        content=index_doc["index_content"],
        media_type="text/plain",
        headers={
            "Content-Disposition": f'inline; filename="{website[1]}_llms.txt"'
        }
    )


@router.post("/{website_id}/process", response_model=ProcessingStatus)
async def process_pages_with_ai(
    website_id: str,
    request: ProcessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process pages with AI enhancement."""
    # Verify website belongs to user
    website = db.execute(
        """
        SELECT id FROM websites 
        WHERE id = %s AND user_id = %s
        """,
        (website_id, str(current_user.id))
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Verify all pages belong to the website
    placeholders = ','.join(['%s'] * len(request.page_ids))
    query = f"""
        SELECT COUNT(*) FROM pages 
        WHERE website_id = %s AND id IN ({placeholders})
    """
    
    count = db.execute(query, [website_id] + request.page_ids).fetchone()[0]
    
    if count != len(request.page_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some pages do not belong to this website"
        )
    
    # Queue batch processing task
    task = batch_process_pages_task.apply_async(
        args=[website_id, request.page_ids]
    )
    
    logger.info(f"Queued AI processing for {len(request.page_ids)} pages in website {website_id}")
    
    return ProcessingStatus(
        job_id=task.id,
        status="processing",
        total_pages=len(request.page_ids),
        processed_pages=0,
        failed_pages=0
    )


@router.get("/{website_id}/changes")
async def get_content_changes(
    website_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    since: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent content changes for a website."""
    # Verify website belongs to user
    website = db.execute(
        """
        SELECT id FROM websites 
        WHERE id = %s AND user_id = %s
        """,
        (website_id, str(current_user.id))
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Get changes
    query = """
        SELECT pc.id, pc.page_id, p.url, p.title, pc.change_type,
               pc.detected_at, pc.old_hash, pc.new_hash
        FROM page_changes pc
        JOIN pages p ON pc.page_id = p.id
        WHERE p.website_id = %s
    """
    params = [website_id]
    
    if since:
        query += " AND pc.detected_at > %s"
        params.append(since)
    
    query += " ORDER BY pc.detected_at DESC LIMIT %s"
    params.append(limit)
    
    changes = db.execute(query, params).fetchall()
    
    return {
        "website_id": website_id,
        "changes": [
            {
                "id": str(change[0]),
                "page_id": str(change[1]),
                "url": change[2],
                "title": change[3],
                "change_type": change[4],
                "detected_at": change[5],
                "old_hash": change[6],
                "new_hash": change[7]
            }
            for change in changes
        ]
    }


@router.get("/{website_id}/statistics")
async def get_website_statistics(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content statistics for a website."""
    # Verify website belongs to user
    website = db.execute(
        """
        SELECT id, domain, created_at FROM websites 
        WHERE id = %s AND user_id = %s
        """,
        (website_id, str(current_user.id))
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Get page statistics
    stats = db.execute(
        """
        SELECT 
            COUNT(*) as total_pages,
            COUNT(DISTINCT url_path) as unique_paths,
            MIN(created_at) as first_crawled,
            MAX(updated_at) as last_updated
        FROM pages
        WHERE website_id = %s
        """,
        (website_id,)
    ).fetchone()
    
    # Get AI processing statistics from MongoDB
    collection = get_mongo_collection("markdown_documents")
    ai_stats = collection.aggregate([
        {"$match": {"website_id": website_id}},
        {"$group": {
            "_id": None,
            "total_processed": {"$sum": 1},
            "ai_processed": {
                "$sum": {"$cond": [{"$eq": ["$metadata.ai_processed", True]}, 1, 0]}
            },
            "avg_quality_score": {"$avg": "$metadata.quality_score"}
        }}
    ])
    
    ai_stats_result = list(ai_stats)
    ai_data = ai_stats_result[0] if ai_stats_result else {}
    
    return {
        "website_id": website_id,
        "domain": website[1],
        "created_at": website[2],
        "statistics": {
            "total_pages": stats[0] or 0,
            "unique_paths": stats[1] or 0,
            "first_crawled": stats[2],
            "last_updated": stats[3],
            "ai_processed_pages": ai_data.get("ai_processed", 0),
            "average_quality_score": ai_data.get("avg_quality_score", 0.0)
        }
    }