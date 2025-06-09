# Phase 5: Monitoring & Scheduling

## Overview
Implement website change detection, automated scheduling with Celery Beat, monitoring endpoints, and notification systems for the complete crawling lifecycle.

## Duration: Week 5

## Prerequisites
- Phase 1-4 completed successfully
- Crawling and processing pipelines operational
- Content quality metrics established
- All APIs functional

## Checklist

### Day 1-2: Change Detection System
- [ ] Content Hashing Implementation
  - [ ] Create content hashing utilities:
    - [ ] SHA-256 for full content
    - [ ] Perceptual hashing for similarity
    - [ ] Structural hashing for layout
  - [ ] Implement hash storage strategy
  - [ ] Add hash comparison logic
  - [ ] Handle minor vs major changes
  - [ ] Create change thresholds
  - [ ] Implement diff generation

- [ ] Change Tracking Database
  - [ ] Update page_changes table schema
  - [ ] Create change detection algorithm:
    ```python
    def detect_changes(old_content, new_content):
        # 1. Compare content hashes
        # 2. Calculate similarity score
        # 3. Identify changed sections
        # 4. Classify change type
        # 5. Generate change summary
    ```
  - [ ] Store change history
  - [ ] Track change frequency
  - [ ] Implement change analytics
  - [ ] Create change reports

### Day 2-3: Celery Beat Scheduling
- [ ] Schedule Configuration
  - [ ] Create schedule management system
  - [ ] Implement cron expression parser
  - [ ] Add schedule validation
  - [ ] Create default schedules:
    - [ ] Daily at 2 AM
    - [ ] Weekly on Sundays
    - [ ] Monthly on 1st
    - [ ] Custom expressions
  - [ ] Handle timezone conversions
  - [ ] Implement schedule persistence

- [ ] Scheduled Tasks
  - [ ] Create monitoring tasks:
    ```python
    @celery.task
    def monitor_website_changes(website_id):
        # 1. Fetch website config
        # 2. Run incremental crawl
        # 3. Compare with previous
        # 4. Detect changes
        # 5. Send notifications
        # 6. Update next run time
    ```
  - [ ] Implement task chaining
  - [ ] Add task dependencies
  - [ ] Create task groups
  - [ ] Handle failed schedules
  - [ ] Implement retry policies

### Day 3-4: Monitoring Infrastructure
- [ ] Monitoring Endpoints
  - [ ] POST /monitor/website
    ```json
    {
      "url": "https://example.com",
      "schedule": "0 2 * * *",
      "notify_on": ["content_change", "error"],
      "change_threshold": 0.1
    }
    ```
  - [ ] GET /monitor/websites
    - [ ] List all monitored sites
    - [ ] Show last check time
    - [ ] Display change statistics
  - [ ] PUT /monitor/website/{id}
    - [ ] Update schedule
    - [ ] Change notification settings
    - [ ] Modify crawl config
  - [ ] DELETE /monitor/website/{id}
  - [ ] GET /monitor/website/{id}/history
    - [ ] Show change timeline
    - [ ] Display crawl history
    - [ ] Include performance metrics

- [ ] Monitoring Dashboard API
  - [ ] Create dashboard data endpoints:
    - [ ] GET /monitor/stats/overview
    - [ ] GET /monitor/stats/changes
    - [ ] GET /monitor/stats/errors
    - [ ] GET /monitor/stats/performance
  - [ ] Implement real-time updates
  - [ ] Add WebSocket support
  - [ ] Create metric aggregations

### Day 4-5: Notification System
- [ ] Notification Framework
  - [ ] Create notification service:
    ```python
    class NotificationService:
        def send_email(user, subject, content)
        def send_slack(webhook, message)
        def send_webhook(url, payload)
        def send_in_app(user_id, notification)
    ```
  - [ ] Implement notification templates
  - [ ] Add notification queuing
  - [ ] Create retry mechanism
  - [ ] Handle delivery failures

- [ ] Notification Types
  - [ ] Content Changes
    - [ ] Major content updates
    - [ ] New pages discovered
    - [ ] Pages removed
    - [ ] Structure changes
  - [ ] System Events
    - [ ] Crawl completed
    - [ ] Crawl failed
    - [ ] Rate limit reached
    - [ ] Storage limit warning
  - [ ] Performance Alerts
    - [ ] Slow response times
    - [ ] High error rates
    - [ ] Resource usage alerts

### Day 5: Integration & Testing
- [ ] System Integration
  - [ ] Connect all monitoring components
  - [ ] Test end-to-end workflows
  - [ ] Verify notification delivery
  - [ ] Validate change detection
  - [ ] Check schedule execution
  - [ ] Monitor resource usage

- [ ] Testing Suite
  - [ ] Unit tests for change detection
  - [ ] Integration tests for scheduling
  - [ ] Test notification delivery
  - [ ] Simulate various change scenarios
  - [ ] Load test monitoring system
  - [ ] Test failure recovery

## Deliverables
1. Change detection system with diff generation
2. Celery Beat scheduling integration
3. Comprehensive monitoring API
4. Multi-channel notification system
5. Monitoring dashboard endpoints
6. Complete test coverage

## Validation Criteria
- [ ] Changes detected accurately (>95% accuracy)
- [ ] Schedules execute on time (±1 minute)
- [ ] Notifications delivered reliably
- [ ] Dashboard shows real-time data
- [ ] System handles 1000+ monitored sites
- [ ] Change history tracked correctly
- [ ] Resource usage remains stable

## Monitoring Architecture
```
┌─────────────────────┐
│   Celery Beat       │
│   (Scheduler)       │
└──────────┬──────────┘
           │ Triggers
┌──────────▼──────────┐     ┌─────────────────┐
│  Monitoring Tasks   │────▶│  Change Detection│
└─────────────────────┘     └──────────┬──────┘
                                       │
                            ┌──────────▼──────────┐
                            │  Notification Queue │
                            └──────────┬──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │    Email     │  │    Slack     │  │   Webhooks   │
            └──────────────┘  └──────────────┘  └──────────────┘
```

## Schedule Examples
```python
# Common schedules
SCHEDULES = {
    "hourly": "0 * * * *",
    "daily": "0 2 * * *",
    "weekly": "0 2 * * 0",
    "monthly": "0 2 1 * *",
    "business_hours": "0 9-17 * * 1-5",
    "twice_daily": "0 2,14 * * *",
    "every_6_hours": "0 */6 * * *"
}

# Celery Beat configuration
CELERYBEAT_SCHEDULE = {
    'monitor-all-websites': {
        'task': 'src.scheduler.tasks.monitor_all_websites',
        'schedule': crontab(minute=0, hour='*/6'),
    },
    'cleanup-old-data': {
        'task': 'src.scheduler.tasks.cleanup_old_data',
        'schedule': crontab(minute=0, hour=3),
    },
    'generate-daily-reports': {
        'task': 'src.scheduler.tasks.generate_reports',
        'schedule': crontab(minute=0, hour=8),
    }
}
```

## Notification Templates

### Email Template (Change Detected)
```html
<h2>Website Changes Detected</h2>
<p>We've detected changes on <strong>{{ website_name }}</strong></p>

<h3>Summary</h3>
<ul>
  <li>Pages changed: {{ changed_count }}</li>
  <li>New pages: {{ new_count }}</li>
  <li>Removed pages: {{ removed_count }}</li>
  <li>Change significance: {{ change_level }}</li>
</ul>

<h3>Top Changes</h3>
{{ change_details }}

<p><a href="{{ dashboard_url }}">View Full Report</a></p>
```

### Slack Message
```json
{
  "text": "Website changes detected",
  "attachments": [{
    "color": "warning",
    "fields": [
      {"title": "Website", "value": "example.com", "short": true},
      {"title": "Changes", "value": "15 pages", "short": true},
      {"title": "Significance", "value": "Major", "short": true},
      {"title": "Last Check", "value": "2 hours ago", "short": true}
    ],
    "actions": [
      {"type": "button", "text": "View Changes", "url": "..."}
    ]
  }]
}
```

## Common Issues & Solutions
1. **Missed schedules**: Check Celery Beat process health
2. **False positives**: Tune change detection thresholds
3. **Notification spam**: Implement digest notifications
4. **Time zone issues**: Always store in UTC
5. **Memory leaks**: Monitor worker memory usage

## Testing Commands
```bash
# Test change detection
pytest tests/test_monitoring.py -v

# Manually trigger monitoring
curl -X POST http://localhost:8000/monitor/website/ID/check \
  -H "Authorization: Bearer YOUR_TOKEN"

# View monitoring stats
curl -X GET http://localhost:8000/monitor/stats/overview \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test notification
curl -X POST http://localhost:8000/monitor/test-notification \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "email", "recipient": "test@example.com"}'

# Monitor Celery Beat
celery -A src.celery beat --loglevel=info

# Check scheduled tasks
celery -A src.celery inspect scheduled
```

## Next Phase Dependencies
Monitoring and scheduling must be stable before moving to production deployment in Phase 6.