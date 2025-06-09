-- Database optimization script for Lapis Spider

-- Create indexes for better query performance

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Websites table indexes
CREATE INDEX IF NOT EXISTS idx_websites_user_id ON websites(user_id);
CREATE INDEX IF NOT EXISTS idx_websites_created_at ON websites(created_at);
CREATE INDEX IF NOT EXISTS idx_websites_url ON websites(url);

-- Crawl jobs table indexes
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_website_id ON crawl_jobs(website_id);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_created_at ON crawl_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_website_status ON crawl_jobs(website_id, status);

-- Pages table indexes
CREATE INDEX IF NOT EXISTS idx_pages_website_id ON pages(website_id);
CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url);
CREATE INDEX IF NOT EXISTS idx_pages_content_hash ON pages(content_hash);
CREATE INDEX IF NOT EXISTS idx_pages_created_at ON pages(created_at);
CREATE INDEX IF NOT EXISTS idx_pages_website_url ON pages(website_id, url);

-- API keys table indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- Crawl schedules table indexes
CREATE INDEX IF NOT EXISTS idx_crawl_schedules_website_id ON crawl_schedules(website_id);
CREATE INDEX IF NOT EXISTS idx_crawl_schedules_is_active ON crawl_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_crawl_schedules_next_run ON crawl_schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_crawl_schedules_active_next ON crawl_schedules(is_active, next_run);

-- Page changes table indexes
CREATE INDEX IF NOT EXISTS idx_page_changes_page_id ON page_changes(page_id);
CREATE INDEX IF NOT EXISTS idx_page_changes_crawl_job_id ON page_changes(crawl_job_id);
CREATE INDEX IF NOT EXISTS idx_page_changes_detected_at ON page_changes(detected_at);
CREATE INDEX IF NOT EXISTS idx_page_changes_change_type ON page_changes(change_type);

-- Notifications table indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read);

-- Audit logs table indexes (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);
    END IF;
END $$;

-- Create partial indexes for common queries
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_pending ON crawl_jobs(website_id) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_running ON crawl_jobs(website_id) WHERE status = 'running';
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id) WHERE is_read = false;

-- Create composite indexes for complex queries
CREATE INDEX IF NOT EXISTS idx_pages_website_created ON pages(website_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_website_created ON crawl_jobs(website_id, created_at DESC);

-- Analyze tables to update statistics
ANALYZE users;
ANALYZE websites;
ANALYZE crawl_jobs;
ANALYZE pages;
ANALYZE api_keys;
ANALYZE crawl_schedules;
ANALYZE page_changes;
ANALYZE notifications;

-- Configure autovacuum for optimal performance
ALTER TABLE crawl_jobs SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE pages SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE page_changes SET (autovacuum_vacuum_scale_factor = 0.1);

-- Add table partitioning for large tables (future enhancement)
-- This would partition crawl_jobs and pages by month for better performance
-- Example (not executed, for reference):
-- CREATE TABLE crawl_jobs_2024_01 PARTITION OF crawl_jobs 
-- FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Create materialized view for dashboard statistics (example)
-- CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_stats AS
-- SELECT 
--     COUNT(DISTINCT u.id) as total_users,
--     COUNT(DISTINCT w.id) as total_websites,
--     COUNT(cj.id) as total_crawls,
--     COUNT(p.id) as total_pages
-- FROM users u
-- LEFT JOIN websites w ON u.id = w.user_id
-- LEFT JOIN crawl_jobs cj ON w.id = cj.website_id
-- LEFT JOIN pages p ON w.id = p.website_id;

-- Create function for cleaning old data
CREATE OR REPLACE FUNCTION cleanup_old_data(retention_days INTEGER DEFAULT 90)
RETURNS TABLE(
    deleted_jobs INTEGER,
    deleted_changes INTEGER,
    deleted_notifications INTEGER
) AS $$
DECLARE
    cutoff_date TIMESTAMP;
    jobs_deleted INTEGER;
    changes_deleted INTEGER;
    notifications_deleted INTEGER;
BEGIN
    cutoff_date := CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    
    -- Delete old completed crawl jobs
    WITH deleted AS (
        DELETE FROM crawl_jobs 
        WHERE completed_at < cutoff_date 
        AND status IN ('completed', 'failed', 'cancelled')
        RETURNING id
    )
    SELECT COUNT(*) INTO jobs_deleted FROM deleted;
    
    -- Delete old page changes
    WITH deleted AS (
        DELETE FROM page_changes 
        WHERE detected_at < cutoff_date
        RETURNING id
    )
    SELECT COUNT(*) INTO changes_deleted FROM deleted;
    
    -- Delete old read notifications
    WITH deleted AS (
        DELETE FROM notifications 
        WHERE created_at < cutoff_date 
        AND is_read = true
        RETURNING id
    )
    SELECT COUNT(*) INTO notifications_deleted FROM deleted;
    
    RETURN QUERY SELECT jobs_deleted, changes_deleted, notifications_deleted;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION cleanup_old_data(INTEGER) TO lapis_user;