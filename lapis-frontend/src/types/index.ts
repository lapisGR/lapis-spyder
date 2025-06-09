// Type definitions for Lapis Spider

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface Website {
  id: string;
  user_id: string;
  name: string;
  url: string;
  crawl_config?: Record<string, any>;
  created_at: string;
}

export interface Page {
  id: string;
  url: string;
  title: string;
  content_hash: string;
  last_modified?: string;
  ai_processed: boolean;
  summary?: string;
  page_type?: string;
}

export interface CrawlJob {
  id: string;
  website_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  pages_crawled?: number;
  error_message?: string;
  statistics?: {
    total_pages: number;
    successful_pages: number;
    failed_pages: number;
    duration_seconds: number;
  };
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}