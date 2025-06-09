"""Scheduler Celery tasks."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

from celery import Task

from src.celery import app
from src.database.postgres import get_db_context
from src.database.mongodb import get_mongo_collection, MongoDBOperations
from src.database.redis import get_redis
from src.crawler.tasks import crawl_website_task
from src.utils.logging import get_logger
from src.utils.diff import detect_changes
from src.notifications import send_notification

logger = get_logger(__name__)


@app.task(bind=True, name="check_scheduled_crawls")
def check_scheduled_crawls(self: Task) -> Dict:
    """Check for scheduled crawls that are due to run."""
    logger.info("Checking for scheduled crawls")
    
    executed = 0
    errors = 0
    
    try:
        with get_db_context() as db:
            # Find schedules that are due
            schedules = db.execute(
                """
                SELECT cs.id, cs.website_id, cs.cron_expression, w.url, w.crawl_config
                FROM crawl_schedules cs
                JOIN websites w ON cs.website_id = w.id
                WHERE cs.is_active = true 
                AND (cs.next_run IS NULL OR cs.next_run <= CURRENT_TIMESTAMP)
                """
            ).fetchall()
            
            logger.info(f"Found {len(schedules)} scheduled crawls to execute")
            
            for schedule in schedules:
                schedule_id = str(schedule[0])
                website_id = str(schedule[1])
                cron_expression = schedule[2]
                website_url = schedule[3]
                crawl_config = schedule[4] or {}
                
                try:
                    # Create new crawl job
                    import uuid
                    crawl_job_id = str(uuid.uuid4())
                    
                    db.execute(
                        """
                        INSERT INTO crawl_jobs (id, website_id, status)
                        VALUES (%s, %s, 'pending')
                        """,
                        (crawl_job_id, website_id)
                    )
                    
                    # Queue crawl task
                    crawl_website_task.delay(
                        crawl_job_id,
                        website_id,
                        website_url,
                        crawl_config
                    )
                    
                    # Update schedule
                    next_run = calculate_next_run(cron_expression)
                    db.execute(
                        """
                        UPDATE crawl_schedules 
                        SET last_run = CURRENT_TIMESTAMP, next_run = %s
                        WHERE id = %s
                        """,
                        (next_run, schedule_id)
                    )
                    
                    executed += 1
                    logger.info(f"Scheduled crawl queued for website {website_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to execute scheduled crawl for {website_id}: {e}")
                    errors += 1
            
            db.commit()
    
    except Exception as e:
        logger.error(f"Error checking scheduled crawls: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
    
    return {
        "status": "completed",
        "executed": executed,
        "errors": errors
    }


@app.task(bind=True, name="cleanup_old_data")
def cleanup_old_data(self: Task) -> Dict:
    """Clean up old crawl data based on retention policies."""
    logger.info("Starting old data cleanup")
    
    try:
        from src.config import settings
        retention_days = settings.storage_retention_days
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Clean up old crawl jobs
        with get_db_context() as db:
            # Get old crawl jobs
            old_jobs = db.execute(
                """
                SELECT id FROM crawl_jobs 
                WHERE created_at < %s 
                AND status IN ('completed', 'failed', 'cancelled')
                """,
                (cutoff_date,)
            ).fetchall()
            
            job_ids = [str(job[0]) for job in old_jobs]
            
            if job_ids:
                # Delete from MongoDB
                collection = get_mongo_collection("raw_html")
                html_result = collection.delete_many({
                    "crawl_job_id": {"$in": job_ids}
                })
                
                # Delete old crawl jobs
                placeholders = ','.join(['%s'] * len(job_ids))
                db.execute(
                    f"DELETE FROM crawl_jobs WHERE id IN ({placeholders})",
                    job_ids
                )
                
                db.commit()
                
                logger.info(
                    f"Cleaned up {len(job_ids)} old crawl jobs and "
                    f"{html_result.deleted_count} HTML documents"
                )
        
        # Clean up orphaned MongoDB documents
        collection = get_mongo_collection("markdown_documents")
        
        # Find documents without corresponding pages
        with get_db_context() as db:
            valid_page_ids = db.execute(
                "SELECT id::text FROM pages"
            ).fetchall()
            valid_page_ids = [p[0] for p in valid_page_ids]
        
        # Delete orphaned documents
        orphan_result = collection.delete_many({
            "page_id": {"$nin": valid_page_ids}
        })
        
        if orphan_result.deleted_count > 0:
            logger.info(f"Cleaned up {orphan_result.deleted_count} orphaned markdown documents")
        
        return {
            "status": "completed",
            "crawl_jobs_deleted": len(job_ids) if 'job_ids' in locals() else 0,
            "html_documents_deleted": html_result.deleted_count if 'html_result' in locals() else 0,
            "orphaned_documents_deleted": orphan_result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.task(bind=True, name="monitor_website_changes")
def monitor_website_changes(self: Task, website_id: str) -> Dict:
    """Monitor a website for content changes."""
    logger.info(f"Monitoring website {website_id} for changes")
    
    changes_detected = []
    
    try:
        with get_db_context() as db:
            # Get recent crawl job
            recent_job = db.execute(
                """
                SELECT id FROM crawl_jobs 
                WHERE website_id = %s AND status = 'completed'
                ORDER BY completed_at DESC 
                LIMIT 1
                """,
                (website_id,)
            ).fetchone()
            
            if not recent_job:
                logger.warning(f"No completed crawl jobs for website {website_id}")
                return {
                    "status": "no_data",
                    "website_id": website_id,
                    "changes": []
                }
            
            crawl_job_id = str(recent_job[0])
            
            # Get pages from this crawl
            pages = db.execute(
                """
                SELECT id, url, content_hash 
                FROM pages 
                WHERE website_id = %s
                """,
                (website_id,)
            ).fetchall()
            
            # Check each page for changes
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                for page in pages:
                    page_id = str(page[0])
                    url = page[1]
                    old_hash = page[2]
                    
                    # Get current content from MongoDB
                    current_doc = loop.run_until_complete(
                        MongoDBOperations.get_html(page_id)
                    )
                    
                    if current_doc:
                        from src.utils.hashing import hash_content
                        new_hash = hash_content(current_doc.get("raw_html", ""))
                        
                        if old_hash != new_hash:
                            # Content changed
                            change_data = {
                                "page_id": page_id,
                                "url": url,
                                "old_hash": old_hash,
                                "new_hash": new_hash,
                                "change_type": "modified"
                            }
                            
                            # Record change
                            db.execute(
                                """
                                INSERT INTO page_changes 
                                (page_id, crawl_job_id, change_type, old_hash, new_hash)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (page_id, crawl_job_id, "updated", old_hash, new_hash)
                            )
                            
                            changes_detected.append(change_data)
                            logger.info(f"Change detected for page {url}")
                
                db.commit()
                
            finally:
                loop.close()
        
        # Send notifications if changes detected
        if changes_detected:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(
                    send_notification(
                        "website_changes",
                        {
                            "website_id": website_id,
                            "changes_count": len(changes_detected),
                            "changes": changes_detected[:10]  # Limit to 10
                        }
                    )
                )
            finally:
                loop.close()
        
        return {
            "status": "completed",
            "website_id": website_id,
            "changes_detected": len(changes_detected),
            "changes": changes_detected
        }
        
    except Exception as e:
        logger.error(f"Error monitoring website {website_id}: {e}")
        return {
            "status": "error",
            "website_id": website_id,
            "error": str(e)
        }


@app.task(bind=True, name="generate_daily_reports")
def generate_daily_reports(self: Task) -> Dict:
    """Generate daily activity reports."""
    logger.info("Generating daily reports")
    
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        today = datetime.utcnow()
        
        with get_db_context() as db:
            # Get crawl statistics
            crawl_stats = db.execute(
                """
                SELECT 
                    COUNT(*) as total_crawls,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    SUM(pages_crawled) as total_pages
                FROM crawl_jobs
                WHERE created_at >= %s AND created_at < %s
                """,
                (yesterday, today)
            ).fetchone()
            
            # Get change statistics
            change_stats = db.execute(
                """
                SELECT 
                    COUNT(DISTINCT page_id) as pages_changed,
                    COUNT(*) as total_changes
                FROM page_changes
                WHERE detected_at >= %s AND detected_at < %s
                """,
                (yesterday, today)
            ).fetchone()
            
            # Get active users
            active_users = db.execute(
                """
                SELECT COUNT(DISTINCT w.user_id)
                FROM crawl_jobs cj
                JOIN websites w ON cj.website_id = w.id
                WHERE cj.created_at >= %s AND cj.created_at < %s
                """,
                (yesterday, today)
            ).fetchone()[0]
        
        report = {
            "date": yesterday.strftime("%Y-%m-%d"),
            "crawl_statistics": {
                "total_crawls": crawl_stats[0] or 0,
                "successful_crawls": crawl_stats[1] or 0,
                "failed_crawls": crawl_stats[2] or 0,
                "total_pages_crawled": crawl_stats[3] or 0
            },
            "change_statistics": {
                "pages_with_changes": change_stats[0] or 0,
                "total_changes": change_stats[1] or 0
            },
            "active_users": active_users or 0
        }
        
        # Send report notification
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                send_notification("daily_report", report)
            )
        finally:
            loop.close()
        
        logger.info(f"Daily report generated: {report}")
        
        return {
            "status": "completed",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.task(bind=True, name="monitor_system_health")
def monitor_system_health(self: Task) -> Dict:
    """Monitor system health and performance."""
    logger.info("Monitoring system health")
    
    try:
        health_data = {}
        
        # Check database connections
        with get_db_context() as db:
            postgres_ok = True
            
            # Get database size
            db_size = db.execute(
                """
                SELECT pg_database_size(current_database()) as size
                """
            ).fetchone()[0]
            
            health_data["postgres"] = {
                "status": "healthy",
                "database_size_mb": db_size / 1024 / 1024
            }
        
        # Check MongoDB
        try:
            collection = get_mongo_collection("raw_html")
            doc_count = collection.count_documents({})
            
            health_data["mongodb"] = {
                "status": "healthy",
                "document_count": doc_count
            }
        except Exception as e:
            health_data["mongodb"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check Redis
        try:
            redis = get_redis()
            info = redis.info()
            
            health_data["redis"] = {
                "status": "healthy",
                "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            health_data["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check Celery workers
        from src.celery import app as celery_app
        active_workers = celery_app.control.inspect().active()
        
        health_data["celery"] = {
            "status": "healthy" if active_workers else "unhealthy",
            "active_workers": len(active_workers) if active_workers else 0
        }
        
        # Overall health
        all_healthy = all(
            service.get("status") == "healthy" 
            for service in health_data.values()
        )
        
        logger.info(f"System health check: {'healthy' if all_healthy else 'unhealthy'}")
        
        # Send alert if unhealthy
        if not all_healthy:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(
                    send_notification("system_unhealthy", health_data)
                )
            finally:
                loop.close()
        
        return {
            "status": "completed",
            "overall_health": "healthy" if all_healthy else "unhealthy",
            "services": health_data
        }
        
    except Exception as e:
        logger.error(f"Error monitoring system health: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def calculate_next_run(cron_expression: str) -> datetime:
    """Calculate next run time from cron expression."""
    # Simple implementation - just add 24 hours
    # In production, use croniter or similar library
    return datetime.utcnow() + timedelta(days=1)