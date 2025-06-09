"""Crawler module for web scraping and content extraction."""

from .spider_wrapper import SpiderWrapper, SpiderConfig, CrawlResult, crawl_url, crawl_website
from .processor import HTMLProcessor, extract_content, html_to_markdown, html_to_text
from .markdown import MarkdownProcessor, MarkdownDocument, process_markdown, enhance_markdown
from .tasks import crawl_website_task, process_page_content

__all__ = [
    # Spider wrapper
    "SpiderWrapper",
    "SpiderConfig", 
    "CrawlResult",
    "crawl_url",
    "crawl_website",
    
    # HTML processor
    "HTMLProcessor",
    "extract_content",
    "html_to_markdown",
    "html_to_text",
    
    # Markdown processor
    "MarkdownProcessor",
    "MarkdownDocument",
    "process_markdown",
    "enhance_markdown",
    
    # Celery tasks
    "crawl_website_task",
    "process_page_content"
]