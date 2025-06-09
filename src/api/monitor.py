"""Website monitoring API endpoints."""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from src.auth.dependencies import get_current_user
from src.auth.models import User  
from src.database.postgres import get_db
from src.scheduler.tasks import monitor_website_changes
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models
class MonitoringConfig(BaseModel):
    """Website monitoring configuration."""
    
    check_frequency: str = Field(default="daily", pattern="^(hourly|daily|weekly)$")
    notify_on_changes: bool = True
    notification_channels: List[str] = Field(default_factory=lambda: ["in_app"])
    change_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    
    @validator("notification_channels")
    def validate_channels(cls, v):
        """Validate notification channels."""
        valid_channels = {"email", "slack", "in_app"}
        for channel in v:
            if channel not in valid_channels:
                raise ValueError(f"Invalid channel: {channel}")
        return v


class MonitoringRequest(BaseModel):
    """Request to monitor a website."""
    
    website_id: str
    config: MonitoringConfig = Field(default_factory=MonitoringConfig)


class MonitoredWebsite(BaseModel):
    """Monitored website information."""
    
    id: str
    website_id: str
    website_url: str
    website_name: str
    is_active: bool
    last_check: Optional[datetime]
    next_check: Optional[datetime]
    config: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChangeDetectionResult(BaseModel):
    """Change detection result."""
    
    page_id: str
    url: str
    change_type: str
    old_hash: str
    new_hash: str
    detected_at: datetime
    significance: Optional[float]


# API Endpoints
@router.post("/website", response_model=MonitoredWebsite)
async def add_website_monitoring(
    request: MonitoringRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a website to monitoring."""
    # Verify website belongs to user
    website = db.execute(
        """
        SELECT id, url, name FROM websites 
        WHERE id = %s AND user_id = %s
        """,
        (request.website_id, str(current_user.id))
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Check if already monitoring
    existing = db.execute(
        """
        SELECT id FROM crawl_schedules 
        WHERE website_id = %s
        """,
        (request.website_id,)
    ).fetchone()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Website is already being monitored"
        )
    
    # Create monitoring schedule
    cron_expression = {
        "hourly": "0 * * * *",
        "daily": "0 2 * * *",
        "weekly": "0 2 * * 0"
    }.get(request.config.check_frequency, "0 2 * * *")
    
    # Calculate next run
    next_run = datetime.utcnow()
    if request.config.check_frequency == "hourly":
        next_run += timedelta(hours=1)
    elif request.config.check_frequency == "weekly":
        next_run += timedelta(days=7)
    else:
        next_run += timedelta(days=1)
    
    import uuid
    schedule_id = str(uuid.uuid4())
    
    db.execute(
        """
        INSERT INTO crawl_schedules (id, website_id, cron_expression, is_active, next_run)
        VALUES (%s, %s, %s, true, %s)
        """,
        (schedule_id, request.website_id, cron_expression, next_run)
    )
    
    # Store monitoring config
    db.execute(
        """
        UPDATE websites 
        SET crawl_config = crawl_config || %s::jsonb
        WHERE id = %s
        """,
        (
            {
                "monitoring": request.config.dict(),
                "auto_process_ai": True
            },
            request.website_id
        )
    )
    
    db.commit()
    
    logger.info(f"Added monitoring for website {request.website_id}")
    
    return MonitoredWebsite(
        id=schedule_id,
        website_id=str(website[0]),
        website_url=website[1],
        website_name=website[2],
        is_active=True,
        last_check=None,
        next_check=next_run,
        config=request.config.dict(),
        created_at=datetime.utcnow()
    )


@router.get("/websites", response_model=List[MonitoredWebsite])
async def list_monitored_websites(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all monitored websites for the user."""
    query = """
        SELECT cs.id, cs.website_id, w.url, w.name, cs.is_active,
               cs.last_run, cs.next_run, w.crawl_config, cs.created_at
        FROM crawl_schedules cs
        JOIN websites w ON cs.website_id = w.id
        WHERE w.user_id = %s
    """
    params = [str(current_user.id)]
    
    if is_active is not None:
        query += " AND cs.is_active = %s"
        params.append(is_active)
    
    query += " ORDER BY cs.created_at DESC"
    
    schedules = db.execute(query, params).fetchall()
    
    monitored = []
    for schedule in schedules:
        config = schedule[7] or {}
        monitoring_config = config.get("monitoring", {})
        
        monitored.append(MonitoredWebsite(
            id=str(schedule[0]),
            website_id=str(schedule[1]),
            website_url=schedule[2],
            website_name=schedule[3],
            is_active=schedule[4],
            last_check=schedule[5],
            next_check=schedule[6],
            config=monitoring_config,
            created_at=schedule[8]
        ))
    
    return monitored


@router.put("/website/{schedule_id}", response_model=MonitoredWebsite)
async def update_monitoring_config(
    schedule_id: str,
    config: MonitoringConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update monitoring configuration."""
    # Verify schedule belongs to user
    schedule = db.execute(
        """
        SELECT cs.id, cs.website_id, w.url, w.name, cs.is_active,
               cs.last_run, cs.next_run, cs.created_at
        FROM crawl_schedules cs
        JOIN websites w ON cs.website_id = w.id
        WHERE cs.id = %s AND w.user_id = %s
        """,
        (schedule_id, str(current_user.id))
    ).fetchone()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring schedule not found"
        )
    
    # Update cron expression
    cron_expression = {
        "hourly": "0 * * * *",
        "daily": "0 2 * * *", 
        "weekly": "0 2 * * 0"
    }.get(config.check_frequency, "0 2 * * *")
    
    db.execute(
        """
        UPDATE crawl_schedules 
        SET cron_expression = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (cron_expression, schedule_id)
    )
    
    # Update website config
    db.execute(
        """
        UPDATE websites 
        SET crawl_config = crawl_config || %s::jsonb
        WHERE id = %s
        """,
        (
            {"monitoring": config.dict()},
            str(schedule[1])
        )
    )
    
    db.commit()
    
    logger.info(f"Updated monitoring config for schedule {schedule_id}")
    
    return MonitoredWebsite(
        id=schedule_id,
        website_id=str(schedule[1]),
        website_url=schedule[2],
        website_name=schedule[3],
        is_active=schedule[4],
        last_check=schedule[5],
        next_check=schedule[6],
        config=config.dict(),
        created_at=schedule[7]
    )


@router.delete("/website/{schedule_id}")
async def remove_website_monitoring(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a website from monitoring."""
    # Verify schedule belongs to user
    schedule = db.execute(
        """
        SELECT cs.id FROM crawl_schedules cs
        JOIN websites w ON cs.website_id = w.id
        WHERE cs.id = %s AND w.user_id = %s
        """,
        (schedule_id, str(current_user.id))
    ).fetchone()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring schedule not found"
        )
    
    # Deactivate schedule (soft delete)
    db.execute(
        """
        UPDATE crawl_schedules 
        SET is_active = false, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (schedule_id,)
    )
    
    db.commit()
    
    logger.info(f"Removed monitoring for schedule {schedule_id}")
    
    return {"message": "Website monitoring removed"}


@router.post("/website/{schedule_id}/pause")
async def pause_monitoring(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause monitoring for a website."""
    # Verify schedule belongs to user
    schedule = db.execute(
        """
        SELECT cs.id, cs.is_active FROM crawl_schedules cs
        JOIN websites w ON cs.website_id = w.id
        WHERE cs.id = %s AND w.user_id = %s
        """,
        (schedule_id, str(current_user.id))
    ).fetchone()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring schedule not found"
        )
    
    if not schedule[1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Monitoring is already paused"
        )
    
    db.execute(
        """
        UPDATE crawl_schedules 
        SET is_active = false, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (schedule_id,)
    )
    
    db.commit()
    
    return {"message": "Monitoring paused"}


@router.post("/website/{schedule_id}/resume")
async def resume_monitoring(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume monitoring for a website."""
    # Verify schedule belongs to user
    schedule = db.execute(
        """
        SELECT cs.id, cs.is_active FROM crawl_schedules cs
        JOIN websites w ON cs.website_id = w.id
        WHERE cs.id = %s AND w.user_id = %s
        """,
        (schedule_id, str(current_user.id))
    ).fetchone()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring schedule not found"
        )
    
    if schedule[1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Monitoring is already active"
        )
    
    # Calculate next run time
    next_run = datetime.utcnow() + timedelta(hours=1)
    
    db.execute(
        """
        UPDATE crawl_schedules 
        SET is_active = true, next_run = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (next_run, schedule_id)
    )
    
    db.commit()
    
    return {"message": "Monitoring resumed"}


@router.post("/check/{website_id}")
async def check_website_now(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger a change check for a website."""
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
    
    # Queue monitoring task
    task = monitor_website_changes.apply_async(args=[website_id])
    
    logger.info(f"Manual change check triggered for website {website_id}")
    
    return {
        "message": "Change detection started",
        "task_id": task.id
    }


@router.get("/changes/{website_id}", response_model=List[ChangeDetectionResult])
async def get_recent_changes(
    website_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    since: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent changes detected for a website."""
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
        SELECT pc.page_id, p.url, pc.change_type, pc.old_hash, 
               pc.new_hash, pc.detected_at, pc.change_details
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
    
    results = []
    for change in changes:
        change_details = change[6] or {}
        
        results.append(ChangeDetectionResult(
            page_id=str(change[0]),
            url=change[1],
            change_type=change[2],
            old_hash=change[3],
            new_hash=change[4],
            detected_at=change[5],
            significance=change_details.get("significance")
        ))
    
    return results