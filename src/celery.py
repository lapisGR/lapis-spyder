"""Celery configuration and initialization."""

import os
from celery import Celery, Task
from celery.schedules import crontab

from src.config import settings

# Set default Django settings module for Celery
os.environ.setdefault("LAPIS_SETTINGS_MODULE", "src.config")

# Create Celery app
app = Celery(
    "lapis_spider",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.crawler.tasks",
        "src.scheduler.tasks",
        "src.ai.tasks",
    ]
)

# Celery configuration
app.conf.update(
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "src.crawler.tasks.*": {"queue": "crawler"},
        "src.ai.tasks.*": {"queue": "ai"},
        "src.scheduler.tasks.*": {"queue": "scheduler"},
    },
    
    # Task time limits
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat schedule
    beat_schedule={
        # Check for scheduled crawls every 5 minutes
        "check-scheduled-crawls": {
            "task": "src.scheduler.tasks.check_scheduled_crawls",
            "schedule": crontab(minute="*/5"),
        },
        # Clean up old data daily at 3 AM
        "cleanup-old-data": {
            "task": "src.scheduler.tasks.cleanup_old_data",
            "schedule": crontab(hour=3, minute=0),
        },
        # Generate daily reports at 8 AM
        "generate-daily-reports": {
            "task": "src.scheduler.tasks.generate_daily_reports",
            "schedule": crontab(hour=8, minute=0),
        },
        # Monitor system health every minute
        "monitor-system-health": {
            "task": "src.scheduler.tasks.monitor_system_health",
            "schedule": 60.0,  # Every 60 seconds
        },
    },
    
    # Error handling
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


class BaseTask(Task):
    """Base task with automatic retries and error handling."""
    
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60  # 1 minute
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        print(f"Task {self.name}[{task_id}] retry {self.request.retries}/{self.max_retries}: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        print(f"Task {self.name}[{task_id}] failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        print(f"Task {self.name}[{task_id}] succeeded")
        super().on_success(retval, task_id, args, kwargs)


# Set default base task
app.Task = BaseTask


# Celery signals
from celery.signals import setup_logging, worker_ready, worker_shutdown


@setup_logging.connect
def setup_celery_logging(**kwargs):
    """Configure Celery logging."""
    from src.utils.logging import setup_logging as configure_logging
    configure_logging()


@worker_ready.connect
def worker_ready_handler(sender, **kwargs):
    """Called when worker is ready."""
    print(f"Worker {sender.hostname} is ready")


@worker_shutdown.connect
def worker_shutdown_handler(sender, **kwargs):
    """Called when worker is shutting down."""
    print(f"Worker {sender.hostname} is shutting down")


if __name__ == "__main__":
    app.start()