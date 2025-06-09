"""Tests for AI functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.ai.gemini import GeminiClient
from src.ai.prompts import SYSTEM_PROMPTS, create_prompt
from src.ai.tasks import process_page_with_ai, batch_process_pages_task


class TestGeminiClient:
    """Test Gemini AI client."""
    
    @pytest.fixture
    def gemini_client(self):
        """Create Gemini client instance."""
        with patch('src.ai.gemini.genai.configure'):
            with patch('src.ai.gemini.genai.GenerativeModel') as mock_model:
                mock_model.return_value.generate_content_async = AsyncMock()
                return GeminiClient(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_structure_markdown_success(self, gemini_client):
        """Test successful markdown structuring."""
        markdown_content = "# Test Page\n\nThis is test content."
        expected_response = {
            "summary": "A test page",
            "main_topics": ["testing"],
            "page_type": "article",
            "structured_content": "# Test Page\n\n## Overview\n\nThis is test content."
        }
        
        # Mock AI response
        mock_response = Mock()
        mock_response.text = str(expected_response)
        gemini_client.model.generate_content_async.return_value = mock_response
        
        result = await gemini_client.structure_markdown(
            markdown_content,
            url="https://test.com",
            title="Test Page"
        )
        
        assert result["status"] == "success"
        assert "summary" in result
        assert "structured_content" in result
    
    @pytest.mark.asyncio
    async def test_generate_llms_entry_success(self, gemini_client):
        """Test successful llms.txt entry generation."""
        structured_content = {
            "summary": "Test summary",
            "main_topics": ["topic1", "topic2"],
            "structured_content": "# Structured content"
        }
        
        expected_entry = """# Test Page
- URL: https://test.com
- Summary: Test summary
- Topics: topic1, topic2

## Content
Structured content
"""
        
        # Mock AI response
        mock_response = Mock()
        mock_response.text = expected_entry
        gemini_client.model.generate_content_async.return_value = mock_response
        
        result = await gemini_client.generate_llms_entry(
            structured_content,
            url="https://test.com",
            title="Test Page"
        )
        
        assert "# Test Page" in result
        assert "URL: https://test.com" in result
        assert "Summary: Test summary" in result
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, gemini_client):
        """Test rate limiting functionality."""
        # Set rate limit
        gemini_client.requests_per_minute = 2
        
        # Mock responses
        mock_response = Mock()
        mock_response.text = "response"
        gemini_client.model.generate_content_async.return_value = mock_response
        
        # Make rapid requests
        start_time = datetime.now()
        
        await gemini_client._rate_limited_request("prompt1")
        await gemini_client._rate_limited_request("prompt2")
        
        # Third request should be delayed
        await gemini_client._rate_limited_request("prompt3")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Should have waited at least 60 seconds
        assert elapsed >= 60.0


class TestPrompts:
    """Test AI prompt generation."""
    
    def test_system_prompts_exist(self):
        """Test that system prompts are defined."""
        assert "markdown_structuring" in SYSTEM_PROMPTS
        assert "llms_generation" in SYSTEM_PROMPTS
        assert "content_analysis" in SYSTEM_PROMPTS
    
    def test_create_prompt_basic(self):
        """Test basic prompt creation."""
        prompt = create_prompt(
            "markdown_structuring",
            markdown_content="# Test\n\nContent",
            url="https://test.com"
        )
        
        assert SYSTEM_PROMPTS["markdown_structuring"] in prompt
        assert "# Test" in prompt
        assert "https://test.com" in prompt
    
    def test_create_prompt_with_template(self):
        """Test prompt with template variables."""
        test_prompt = "Process {content} from {url}"
        prompt = create_prompt(
            "test",
            system_prompt=test_prompt,
            content="test data",
            url="https://example.com"
        )
        
        assert "Process test data from https://example.com" in prompt


class TestAITasks:
    """Test AI Celery tasks."""
    
    @patch('src.ai.tasks.MongoDBOperations.get_markdown', new_callable=AsyncMock)
    @patch('src.ai.tasks.GeminiClient')
    @patch('src.ai.tasks.MongoDBOperations.update_markdown', new_callable=AsyncMock)
    def test_process_page_with_ai_success(self, mock_update, mock_gemini_class, mock_get):
        """Test successful AI page processing."""
        # Mock markdown retrieval
        mock_get.return_value = {
            "raw_markdown": "# Test Page\n\nContent",
            "url": "https://test.com",
            "metadata": {"title": "Test Page"}
        }
        
        # Mock Gemini client
        mock_gemini = Mock()
        mock_gemini_class.return_value = mock_gemini
        
        # Use AsyncMock for async method
        async def mock_structure_markdown(*args, **kwargs):
            return {
                "status": "success",
                "structured_content": "# Structured Test",
                "summary": "Test summary"
            }
        
        mock_gemini.structure_markdown = mock_structure_markdown
        
        # Run task
        result = process_page_with_ai("page-123", "website-123")
        
        assert result["status"] == "completed"
        assert result["page_id"] == "page-123"
    
    @patch('src.ai.tasks.process_page_with_ai')
    def test_batch_process_pages_task(self, mock_process):
        """Test batch AI processing."""
        mock_process.return_value = {"status": "completed"}
        
        result = batch_process_pages_task(
            "website-123",
            ["page-1", "page-2", "page-3"]
        )
        
        assert result["website_id"] == "website-123"
        assert result["total_pages"] == 3
        assert mock_process.call_count == 3


@pytest.fixture
def sample_structured_content():
    """Sample structured content for testing."""
    return {
        "status": "success",
        "summary": "This is a comprehensive guide about web crawling",
        "main_topics": ["web crawling", "data extraction", "automation"],
        "page_type": "technical_guide",
        "structured_content": """# Web Crawling Guide

## Overview
This guide covers the fundamentals of web crawling.

## Key Concepts
- Spider architecture
- Rate limiting
- Content extraction

## Best Practices
1. Respect robots.txt
2. Implement delays
3. Handle errors gracefully""",
        "key_points": [
            "Web crawling basics",
            "Implementation details",
            "Best practices"
        ]
    }


@pytest.fixture
def sample_llms_entry():
    """Sample llms.txt entry for testing."""
    return """# Web Crawling Guide
- URL: https://example.com/guide
- Summary: This is a comprehensive guide about web crawling
- Topics: web crawling, data extraction, automation
- Type: technical_guide

## Overview
This guide covers the fundamentals of web crawling.

## Key Concepts
- Spider architecture
- Rate limiting  
- Content extraction

## Best Practices
1. Respect robots.txt
2. Implement delays
3. Handle errors gracefully

## Key Points
- Web crawling basics
- Implementation details
- Best practices
"""