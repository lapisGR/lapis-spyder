"""Crawling API endpoints."""

import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, HttpUrl, validator

from src.auth.dependencies import get_current_user, require_auth
from src.auth.models import User
from src.database.postgres import get_db
from src.crawler.tasks import crawl_website_task
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models
class CrawlConfig(BaseModel):
    """Crawl configuration parameters."""
    
    max_pages: int = Field(default=100, ge=1, le=10000)
    max_depth: int = Field(default=3, ge=1, le=10)
    concurrent_requests: int = Field(default=10, ge=1, le=50)
    respect_robots_txt: bool = True
    user_agent: Optional[str] = None
    crawl_delay: float = Field(default=0.5, ge=0, le=10)
    allowed_domains: List[str] = Field(default_factory=list)
    blacklist_patterns: List[str] = Field(default_factory=list)
    whitelist_patterns: List[str] = Field(default_factory=list)
    
    @validator("crawl_delay")
    def validate_crawl_delay(cls, v):
        """Ensure crawl delay is reasonable."""
        return max(0.1, min(v, 10.0))


class CrawlRequest(BaseModel):
    """Request to start a crawl job."""
    
    url: HttpUrl
    name: Optional[str] = None
    config: CrawlConfig = Field(default_factory=CrawlConfig)


class CrawlJobResponse(BaseModel):
    """Crawl job response."""
    
    id: str
    website_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    pages_crawled: int
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CrawlHistoryItem(BaseModel):
    """Crawl history item."""
    
    id: str
    website_url: str
    website_name: str
    status: str
    pages_crawled: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    created_at: datetime


# API Endpoints
@router.post("/start", response_model=CrawlJobResponse)
async def start_crawl(
    request: CrawlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new crawl job."""
    logger.info(f"User {current_user.email} starting crawl for {request.url}")
    
    try:
        # Parse URL
        url_str = str(request.url)
        domain = request.url.host
        
        # Check if website exists
        website = db.execute(
            """
            SELECT id, name FROM websites 
            WHERE user_id = %s AND url = %s
            """,
            (str(current_user.id), url_str)
        ).fetchone()
        
        if website:
            website_id = str(website[0])
            website_name = website[1]
        else:
            # Create new website
            result = db.execute(
                """
                INSERT INTO websites (user_id, url, domain, name, crawl_config)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                RETURNING id
                """,
                (
                    str(current_user.id),
                    url_str,
                    domain,
                    request.name or domain,
                    request.config.dict()
                )
            )
            website_id = str(result.fetchone()[0])
            website_name = request.name or domain
            db.commit()
        
        # Create crawl job
        crawl_job_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO crawl_jobs (id, website_id, status)
            VALUES (%s, %s, 'pending')
            """,
            (crawl_job_id, website_id)
        )
        db.commit()
        
        # Queue crawl task
        task = crawl_website_task.apply_async(
            args=[crawl_job_id, website_id, url_str, request.config.dict()],
            task_id=crawl_job_id
        )
        
        logger.info(f"Crawl job {crawl_job_id} queued for {url_str}")
        
        # Get created job
        job = db.execute(
            """
            SELECT id, website_id, status, started_at, completed_at, 
                   pages_crawled, error_message, created_at
            FROM crawl_jobs
            WHERE id = %s
            """,
            (crawl_job_id,)
        ).fetchone()
        
        return CrawlJobResponse(
            id=str(job[0]),
            website_id=str(job[1]),
            status=job[2],
            started_at=job[3],
            completed_at=job[4],
            pages_crawled=job[5],
            error_message=job[6],
            created_at=job[7]
        )
        
    except Exception as e:
        logger.error(f"Failed to start crawl: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start crawl: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get crawl job status."""
    # Verify job belongs to user
    job = db.execute(
        """
        SELECT cj.id, cj.website_id, cj.status, cj.started_at, cj.completed_at,
               cj.pages_crawled, cj.error_message, cj.created_at
        FROM crawl_jobs cj
        JOIN websites w ON cj.website_id = w.id
        WHERE cj.id = %s AND w.user_id = %s
        """,
        (job_id, str(current_user.id))
    ).fetchone()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl job not found"
        )
    
    return CrawlJobResponse(
        id=str(job[0]),
        website_id=str(job[1]),
        status=job[2],
        started_at=job[3],
        completed_at=job[4],
        pages_crawled=job[5],
        error_message=job[6],
        created_at=job[7]
    )


@router.get("/history", response_model=List[CrawlHistoryItem])
async def get_crawl_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's crawl job history."""
    query = """
        SELECT cj.id, w.url, w.name, cj.status, cj.pages_crawled,
               cj.started_at, cj.completed_at, cj.created_at
        FROM crawl_jobs cj
        JOIN websites w ON cj.website_id = w.id
        WHERE w.user_id = %s
    """
    params = [str(current_user.id)]
    
    if status:
        query += " AND cj.status = %s"
        params.append(status)
    
    query += " ORDER BY cj.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    jobs = db.execute(query, params).fetchall()
    
    history = []
    for job in jobs:
        duration = None
        if job[5] and job[6]:  # started_at and completed_at
            duration = (job[6] - job[5]).total_seconds()
        
        history.append(CrawlHistoryItem(
            id=str(job[0]),
            website_url=job[1],
            website_name=job[2],
            status=job[3],
            pages_crawled=job[4],
            started_at=job[5],
            completed_at=job[6],
            duration_seconds=duration,
            created_at=job[7]
        ))
    
    return history


@router.post("/cancel/{job_id}")
async def cancel_crawl(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running crawl job."""
    # Verify job belongs to user and is cancellable
    job = db.execute(
        """
        SELECT cj.status
        FROM crawl_jobs cj
        JOIN websites w ON cj.website_id = w.id
        WHERE cj.id = %s AND w.user_id = %s
        """,
        (job_id, str(current_user.id))
    ).fetchone()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl job not found"
        )
    
    if job[0] not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in {job[0]} status"
        )
    
    # Update job status
    db.execute(
        """
        UPDATE crawl_jobs 
        SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (job_id,)
    )
    db.commit()
    
    # Try to revoke Celery task
    from celery.result import AsyncResult
    task = AsyncResult(job_id)
    task.revoke(terminate=True)
    
    logger.info(f"User {current_user.email} cancelled crawl job {job_id}")
    
    return {"message": "Crawl job cancelled"}


@router.get("/statistics")
async def get_crawl_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's crawling statistics."""
    stats = db.execute(
        """
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN cj.status = 'completed' THEN 1 END) as completed_jobs,
            COUNT(CASE WHEN cj.status = 'failed' THEN 1 END) as failed_jobs,
            COUNT(CASE WHEN cj.status = 'running' THEN 1 END) as running_jobs,
            COUNT(DISTINCT w.id) as total_websites,
            SUM(cj.pages_crawled) as total_pages_crawled
        FROM crawl_jobs cj
        JOIN websites w ON cj.website_id = w.id
        WHERE w.user_id = %s
        """,
        (str(current_user.id),)
    ).fetchone()
    
    return {
        "total_jobs": stats[0] or 0,
        "completed_jobs": stats[1] or 0,
        "failed_jobs": stats[2] or 0,
        "running_jobs": stats[3] or 0,
        "total_websites": stats[4] or 0,
        "total_pages_crawled": stats[5] or 0
    }