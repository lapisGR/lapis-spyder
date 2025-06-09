"""Tests for crawler functionality."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.crawler.spider_wrapper import SpiderConfig, CrawlResult, SpiderWrapper
from src.crawler.processor import HTMLProcessor, extract_content, html_to_markdown
from src.crawler.markdown import MarkdownDocument, process_markdown
from src.crawler.tasks import crawl_website_task, process_crawled_page


class TestSpiderWrapper:
    """Test SpiderWrapper class."""
    
    @pytest.fixture
    def spider_wrapper(self):
        """Create spider wrapper instance."""
        with patch('src.crawler.spider_wrapper.SpiderWrapper._find_spider_executable') as mock:
            mock.return_value = '/path/to/spider'
            return SpiderWrapper()
    
    def test_spider_config_to_args(self):
        """Test SpiderConfig to CLI arguments conversion."""
        config = SpiderConfig(
            url="https://example.com",
            max_pages=50,
            max_depth=2,
            respect_robots_txt=False,
            allowed_domains=["example.com", "test.com"]
        )
        
        args = config.to_spider_args()
        
        assert "https://example.com" in args
        assert "--max-pages" in args
        assert "50" in args
        assert "--max-depth" in args
        assert "2" in args
        assert "--no-respect-robots-txt" in args
        assert "--allowed-domain" in args
        assert "example.com" in args
        assert "test.com" in args
    
    @pytest.mark.asyncio
    async def test_crawl_url_success(self, spider_wrapper):
        """Test successful URL crawling."""
        mock_results = [
            CrawlResult(
                url="https://example.com",
                status_code=200,
                content="<html><body>Test</body></html>",
                headers={"content-type": "text/html"},
                error=None
            )
        ]
        
        with patch.object(spider_wrapper, '_run_spider_subprocess', return_value=mock_results):
            results = await spider_wrapper.crawl_url("https://example.com")
            
            assert len(results) == 1
            assert results[0].url == "https://example.com"
            assert results[0].status_code == 200
            assert results[0].error is None
    
    @pytest.mark.asyncio
    async def test_crawl_url_failure(self, spider_wrapper):
        """Test URL crawling failure."""
        with patch.object(spider_wrapper, '_run_spider_subprocess', side_effect=Exception("Crawl failed")):
            results = await spider_wrapper.crawl_url("https://example.com")
            
            assert len(results) == 1
            assert results[0].url == "https://example.com"
            assert results[0].status_code == 0
            assert "Crawl failed" in results[0].error


class TestHTMLProcessor:
    """Test HTML processing functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create HTML processor instance."""
        return HTMLProcessor()
    
    def test_extract_content_basic(self, processor):
        """Test basic content extraction."""
        html = """
        <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Main Title</h1>
            <p>This is a test paragraph.</p>
            <a href="https://example.com">Link</a>
            <img src="image.jpg" alt="Test image">
        </body>
        </html>
        """
        
        result = processor.extract_content(html, "https://test.com")
        
        assert result["title"] == "Test Page"
        assert result["description"] == "Test description"
        assert "This is a test paragraph" in result["text"]
        assert len(result["links"]) == 1
        assert result["links"][0]["href"] == "https://example.com"
        assert len(result["images"]) == 1
        assert result["images"][0]["src"] == "image.jpg"
    
    def test_html_to_markdown(self, processor):
        """Test HTML to Markdown conversion."""
        html = """
        <html>
        <body>
            <h1>Title</h1>
            <p>Paragraph with <strong>bold</strong> and <em>italic</em>.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <a href="https://example.com">Link</a>
        </body>
        </html>
        """
        
        markdown = processor.html_to_markdown(html, "https://test.com")
        
        assert "# Title" in markdown
        assert "**bold**" in markdown
        assert "*italic*" in markdown
        assert "* Item 1" in markdown
        assert "* Item 2" in markdown
        assert "[Link](https://example.com)" in markdown
    
    def test_extract_metadata(self, processor):
        """Test metadata extraction."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta property="og:image" content="og-image.jpg">
            <meta name="author" content="Test Author">
            <meta name="keywords" content="test, keywords">
        </head>
        </html>
        """
        
        metadata = processor.extract_metadata(html)
        
        assert metadata["og:title"] == "OG Title"
        assert metadata["og:description"] == "OG Description"
        assert metadata["og:image"] == "og-image.jpg"
        assert metadata["author"] == "Test Author"
        assert metadata["keywords"] == "test, keywords"


class TestMarkdownProcessing:
    """Test markdown processing functionality."""
    
    def test_process_markdown_basic(self):
        """Test basic markdown processing."""
        markdown = "# Title\n\nThis is a paragraph."
        
        doc = process_markdown(
            markdown,
            url="https://test.com",
            title="Test Page",
            metadata={"author": "Test"}
        )
        
        assert isinstance(doc, MarkdownDocument)
        assert doc.raw_markdown == markdown
        assert doc.metadata["url"] == "https://test.com"
        assert doc.metadata["title"] == "Test Page"
        assert doc.metadata["author"] == "Test"
        assert doc.metadata["word_count"] > 0
    
    def test_markdown_document_sections(self):
        """Test markdown section extraction."""
        markdown = """
# Main Title

## Section 1
Content 1

## Section 2
Content 2

### Subsection 2.1
Subcontent
        """
        
        doc = MarkdownDocument(
            raw_markdown=markdown,
            structured_markdown=None,
            metadata={}
        )
        
        sections = doc.get_sections()
        
        assert len(sections) == 4
        assert sections[0]["title"] == "Main Title"
        assert sections[1]["title"] == "Section 1"
        assert sections[2]["title"] == "Section 2"
        assert sections[3]["title"] == "Subsection 2.1"


class TestCrawlerTasks:
    """Test Celery crawler tasks."""
    
    @pytest.mark.asyncio
    async def test_process_crawled_page_success(self):
        """Test successful page processing."""
        html = "<html><head><title>Test</title></head><body>Content</body></html>"
        
        with patch('src.crawler.tasks._store_page_data', new_callable=AsyncMock) as mock_store:
            with patch('src.database.mongodb.MongoDBOperations.insert_html', new_callable=AsyncMock):
                with patch('src.database.mongodb.MongoDBOperations.insert_markdown', new_callable=AsyncMock):
                    mock_store.return_value = "page-123"
                    
                    result = await process_crawled_page(
                        crawl_job_id="job-123",
                        website_id="website-123",
                        url="https://test.com",
                        html=html,
                        status_code=200,
                        headers={"content-type": "text/html"}
                    )
                    
                    assert result is not None
                    assert result["page_id"] == "page-123"
                    assert result["url"] == "https://test.com"
                    assert result["title"] == "Test"
    
    @pytest.mark.asyncio
    async def test_process_crawled_page_skip_error(self):
        """Test skipping pages with errors."""
        result = await process_crawled_page(
            crawl_job_id="job-123",
            website_id="website-123",
            url="https://test.com",
            html="",
            status_code=404,
            headers={},
            error="Page not found"
        )
        
        assert result is None
    
    @patch('src.crawler.tasks.spider_crawl', new_callable=AsyncMock)
    @patch('src.crawler.tasks._update_crawl_job')
    @patch('src.crawler.tasks.process_crawled_page', new_callable=AsyncMock)
    def test_crawl_website_task(self, mock_process, mock_update, mock_spider):
        """Test crawl website task."""
        # Mock spider results
        mock_spider.return_value = {
            "results": [
                Mock(
                    url="https://test.com",
                    content="<html>Test</html>",
                    status_code=200,
                    headers={},
                    error=None
                )
            ],
            "total_pages": 1,
            "total_size_bytes": 1000,
            "duration_seconds": 5
        }
        
        # Mock page processing
        mock_process.return_value = {
            "page_id": "page-123",
            "url": "https://test.com"
        }
        
        # Run task
        result = crawl_website_task(
            "job-123",
            "website-123",
            "https://test.com",
            {"max_pages": 10}
        )
        
        assert result["status"] == "completed"
        assert result["processed_pages"] == 1
        assert mock_update.call_count >= 2  # Running and completed


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sample Page</title>
        <meta name="description" content="This is a sample page">
        <meta property="og:title" content="Sample OG Title">
    </head>
    <body>
        <header>
            <h1>Main Heading</h1>
            <nav>
                <a href="/about">About</a>
                <a href="/contact">Contact</a>
            </nav>
        </header>
        <main>
            <article>
                <h2>Article Title</h2>
                <p>This is the first paragraph with some <strong>important</strong> text.</p>
                <p>This is the second paragraph with a <a href="https://example.com">link</a>.</p>
                <img src="/images/sample.jpg" alt="Sample image">
            </article>
        </main>
        <footer>
            <p>&copy; 2024 Sample Site</p>
        </footer>
    </body>
    </html>
    """