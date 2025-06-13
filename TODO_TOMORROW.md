# TODO for Tomorrow

## High Priority

### 1. Fix Page Content Storage
- [ ] Debug why markdown content isn't being stored during crawl
- [ ] Ensure `process_crawled_page` in `src/crawler/tasks.py` properly stores markdown in MongoDB
- [ ] Test with a fresh crawl to verify markdown is saved

### 2. Complete Spider Markdown Integration
- [ ] Compile the Rust spider binary for better performance
- [ ] Update spider wrapper to use native markdown transformation
- [ ] Remove the need for Python html2text fallback

### 3. Fix Website Export
- [ ] Ensure all pages have actual content (not "Content not yet processed")
- [ ] Test export_to_folder.py with properly populated markdown content
- [ ] Verify llms.txt is included with full content

## Medium Priority

### 4. API Endpoint Testing
- [ ] Test all new markdown endpoints (/page/{id}.md, /all.md)
- [ ] Verify authentication works correctly across all endpoints
- [ ] Create Postman/Insomnia collection for API testing

### 5. Frontend Integration
- [ ] Update frontend to display AI-processed summaries
- [ ] Add UI for triggering AI processing on pages
- [ ] Show llms.txt preview in the frontend

### 6. Celery Task Improvements
- [ ] Add proper error handling and retry logic for failed tasks
- [ ] Implement progress tracking for long-running crawls
- [ ] Add task status webhooks/notifications

## Low Priority

### 7. Documentation
- [ ] Create API documentation with examples
- [ ] Add setup instructions for new developers
- [ ] Document the crawler configuration options

### 8. Performance Optimization
- [ ] Add caching for frequently accessed pages
- [ ] Optimize MongoDB queries for large datasets
- [ ] Implement pagination for content endpoints

### 9. Testing
- [ ] Write unit tests for OpenRouter client
- [ ] Add integration tests for crawl workflow
- [ ] Test with larger websites (100+ pages)

## Nice to Have

### 10. Features
- [ ] Add support for crawling JavaScript-heavy sites
- [ ] Implement incremental crawling (only new/changed pages)
- [ ] Add support for multiple AI models/providers
- [ ] Create scheduling system for periodic re-crawls
- [ ] Add content diff visualization

## Bugs to Fix

1. **MongoDB Connection**: Sometimes fails on startup - need reliable reconnection logic
2. **Token Expiration**: Frontend doesn't handle expired tokens gracefully
3. **Crawl Status**: Status updates aren't real-time in the API
4. **Memory Usage**: Large crawls may consume too much memory

## Quick Wins

- [ ] Add `crawl_website` management command for easy testing
- [ ] Create `reset_database` script for development
- [ ] Add health check endpoint for monitoring
- [ ] Improve error messages in API responses

## Notes

- Remember: FastAPI runs on port **8080**, not 8000
- Use `admin@example.com` / `Admin123!` for testing
- OpenRouter model: `google/gemini-2.5-flash-preview-05-20`
- Always use `sqlalchemy.text()` for raw SQL queries

## Command Reference

```bash
# Quick test crawl
curl -X POST "http://localhost:8080/api/crawl" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"website_id": "c5fd4070-e904-4906-a087-471a4e8af5c9", "max_pages": 10}'

# Process pages with AI
python test_ai.py

# Export to markdown
python export_to_folder.py

# Check Celery tasks
celery -A src.celery inspect active
```

## Success Criteria

By end of tomorrow:
1. ✅ Full crawl → markdown → AI processing → export workflow works end-to-end
2. ✅ All pages have actual markdown content (not placeholder text)
3. ✅ llms.txt contains authoritative, AI-generated documentation
4. ✅ Can export any website to a folder of markdown files