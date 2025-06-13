# Markdown Storage Fix Summary

## Problem Identified
The markdown content wasn't being stored during crawls due to an async/sync mismatch in the Celery tasks. The `crawl_website_task` (synchronous) was trying to call async MongoDB operations, which don't work in a sync context.

## Root Cause
1. Celery tasks are synchronous by default
2. MongoDB operations were only available as async methods
3. The `process_crawled_page` function was async but called from a sync context
4. This caused the MongoDB insert operations to silently fail

## Solution Applied

### 1. Added Synchronous MongoDB Operations
Added to `src/database/mongodb.py`:
- `insert_markdown_sync()` - Synchronous version for storing markdown
- `insert_html_sync()` - Synchronous version for storing HTML
- `get_markdown_sync()` - Synchronous version for retrieving markdown

### 2. Created Synchronous Processing Function
Added to `src/crawler/tasks.py`:
- `process_crawled_page_sync()` - Synchronous version of page processor
- `_store_page_data_sync()` - Synchronous version using SQLAlchemy `text()`
- Updated to store both raw and structured markdown content

### 3. Fixed Celery Task
Modified `crawl_website_task` to:
- Use `process_crawled_page_sync()` instead of async version
- Remove unnecessary asyncio event loop usage for processing

## Key Changes

### Before (Broken)
```python
# Async call in sync context - doesn't work!
page_data = loop.run_until_complete(
    process_crawled_page(...)  # async function
)

# Missing structured_markdown parameter
await MongoDBOperations.insert_markdown(
    page_id=page_id,
    website_id=website_id,
    url=url,
    raw_markdown=markdown_content,
    metadata=markdown_doc.metadata
)
```

### After (Fixed)
```python
# Sync call in sync context - works!
page_data = process_crawled_page_sync(...)  # sync function

# Includes both raw and structured markdown
MongoDBOperations.insert_markdown_sync(
    page_id=page_id,
    website_id=website_id,
    url=url,
    raw_markdown=markdown_content,
    structured_markdown=markdown_doc.content,  # Added!
    metadata=markdown_doc.metadata
)
```

## Testing the Fix

### 1. Restart Services
```bash
# Restart Celery to load the changes
docker-compose restart celery celery-beat

# Or if running locally
# Kill existing celery workers and restart
```

### 2. Run Test Script
```bash
python test_markdown_storage.py
```

### 3. Perform New Crawl
```bash
# Get auth token
TOKEN=$(curl -X POST "http://localhost:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!"}' \
  | jq -r '.access_token')

# Create website
WEBSITE_ID=$(curl -X POST "http://localhost:8080/api/websites" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Site","url":"https://example.com","description":"Test"}' \
  | jq -r '.id')

# Start crawl
curl -X POST "http://localhost:8080/api/crawl" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"website_id\":\"$WEBSITE_ID\",\"max_pages\":5}"
```

### 4. Verify Storage
```bash
# Check MongoDB directly
python -c "
from src.database.mongodb import get_sync_mongodb
db = get_sync_mongodb()
count = db['markdown_documents'].count_documents({})
print(f'Markdown documents in MongoDB: {count}')
"
```

## Next Steps

1. **Test Export**: Run `export_to_folder.py` to verify markdown can be read
2. **AI Processing**: Ensure AI processing tasks can read the stored markdown
3. **Frontend**: Update frontend to display the markdown content

## Important Notes

- Always use `sqlalchemy.text()` for raw SQL queries in SQLAlchemy 2.0+
- Celery tasks should use synchronous database operations unless specifically designed as async
- The `structured_markdown` field contains the processed/formatted content
- The `raw_markdown` field contains the original conversion from HTML

## Monitoring

To monitor if markdown is being stored:
```python
# Quick check
from src.database.mongodb import MongoDBOperations
doc = MongoDBOperations.get_markdown_sync("your-page-id")
print(f"Has markdown: {bool(doc and doc.get('raw_markdown'))}")
```