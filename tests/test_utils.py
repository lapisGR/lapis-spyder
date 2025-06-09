"""Tests for utility functions."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.utils.hashing import hash_password, verify_password, hash_content, content_similarity_hash
from src.utils.diff import ChangeDetector, detect_changes, ContentChange
from src.utils.performance import CacheManager, cached, PerformanceMonitor, measure_performance
from src.notifications import NotificationManager, EmailChannel, SlackChannel, InAppChannel


class TestHashing:
    """Test hashing utilities."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        
        # Hash password
        hashed = hash_password(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False
        
        # Same password produces different hashes
        hashed2 = hash_password(password)
        assert hashed != hashed2
        assert verify_password(password, hashed2) is True
    
    def test_content_hashing(self):
        """Test content hashing."""
        content = "This is test content for hashing."
        
        # Hash content
        hash1 = hash_content(content)
        hash2 = hash_content(content)
        
        # Same content produces same hash
        assert hash1 == hash2
        
        # Different content produces different hash
        hash3 = hash_content("Different content")
        assert hash1 != hash3
        
        # Empty content
        empty_hash = hash_content("")
        assert empty_hash is not None
        assert len(empty_hash) == 64  # SHA256 hex length
    
    def test_similarity_hashing(self):
        """Test similarity hashing."""
        content1 = "The quick brown fox jumps over the lazy dog."
        content2 = "The quick brown fox jumps over the lazy dogs."  # Minor change
        content3 = "Something completely different."
        
        # Similar content should have same similarity hash
        hash1 = content_similarity_hash(content1)
        hash2 = content_similarity_hash(content2)
        hash3 = content_similarity_hash(content3)
        
        # Very similar content might have same hash (depending on implementation)
        # Different content should have different hash
        assert hash1 != hash3


class TestChangeDetection:
    """Test change detection utilities."""
    
    @pytest.fixture
    def detector(self):
        """Create change detector instance."""
        return ChangeDetector()
    
    def test_no_changes(self, detector):
        """Test detection when no changes."""
        content = "This is unchanged content."
        
        result = detector.detect_changes(content, content)
        
        assert result["changed"] is False
        assert result["hash_changed"] is False
        assert len(result["changes"]) == 0
    
    def test_simple_changes(self, detector):
        """Test detection of simple changes."""
        old_content = "Line 1\nLine 2\nLine 3"
        new_content = "Line 1\nLine 2 modified\nLine 3\nLine 4"
        
        result = detector.detect_changes(old_content, new_content)
        
        assert result["changed"] is True
        assert result["hash_changed"] is True
        assert result["total_changes"] > 0
        assert "modified" in result["summary"]
    
    def test_structural_changes(self, detector):
        """Test detection of structural changes."""
        old_content = """
# Title 1
Content 1

## Section 1.1
Subsection content
        """
        
        new_content = """
# Title 1
Content 1

## Section 1.1
Subsection content

## Section 1.2
New section

# Title 2
New title
        """
        
        result = detector.detect_changes(old_content, new_content)
        
        assert result["changed"] is True
        assert any(c["change_type"] == "modified" for c in result["changes"] 
                  if c.get("location") == "document structure")
    
    def test_line_significance(self, detector):
        """Test line significance calculation."""
        # Comment line
        assert detector._calculate_line_significance("# This is a comment") == 0.2
        
        # Import statement
        assert detector._calculate_line_significance("import something") == 0.7
        
        # Function definition
        assert detector._calculate_line_significance("def my_function():") == 0.8
        
        # Regular content
        assert detector._calculate_line_significance("Regular text") == 0.4
        
        # Empty line
        assert detector._calculate_line_significance("") == 0.0


class TestPerformance:
    """Test performance optimization utilities."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create cache manager instance."""
        with patch('src.utils.performance.get_redis') as mock:
            mock.return_value = Mock()
            return CacheManager()
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, cache_manager):
        """Test cache get/set/delete operations."""
        # Mock Redis operations
        cache_manager.redis.get.return_value = None
        cache_manager.redis.set.return_value = True
        cache_manager.redis.delete.return_value = 1
        
        # Test set
        result = await cache_manager.set("test_key", {"data": "value"}, ttl=60)
        assert result is True
        cache_manager.redis.set.assert_called_once()
        
        # Test get (miss)
        result = await cache_manager.get("test_key")
        assert result is None
        
        # Test get (hit)
        import pickle
        cache_manager.redis.get.return_value = pickle.dumps({"data": "value"})
        result = await cache_manager.get("test_key")
        assert result == {"data": "value"}
        
        # Test delete
        result = await cache_manager.delete("test_key")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_cached_decorator(self, cache_manager):
        """Test cached function decorator."""
        call_count = 0
        
        @cached(prefix="test", ttl=60)
        async def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        with patch('src.utils.performance.cache_manager', cache_manager):
            # First call - cache miss
            cache_manager.get = AsyncMock(return_value=None)
            cache_manager.set = AsyncMock(return_value=True)
            
            result = await expensive_function(1, 2)
            assert result == 3
            assert call_count == 1
            
            # Second call - cache hit
            cache_manager.get = AsyncMock(return_value=3)
            
            result = await expensive_function(1, 2)
            assert result == 3
            assert call_count == 1  # Function not called again
    
    def test_performance_monitor(self):
        """Test performance monitoring."""
        monitor = PerformanceMonitor()
        
        # Measure operations
        import time
        
        with monitor.measure("test_operation"):
            time.sleep(0.1)
        
        with monitor.measure("test_operation"):
            time.sleep(0.2)
        
        # Get metrics
        metrics = monitor.get_metrics()
        
        assert "test_operation" in metrics
        assert metrics["test_operation"]["count"] == 2
        assert metrics["test_operation"]["avg_time"] > 0.1
        assert metrics["test_operation"]["min_time"] >= 0.1
        assert metrics["test_operation"]["max_time"] >= 0.2


class TestNotifications:
    """Test notification system."""
    
    @pytest.fixture
    def notification_manager(self):
        """Create notification manager instance."""
        return NotificationManager()
    
    @pytest.mark.asyncio
    async def test_email_channel(self):
        """Test email notification channel."""
        channel = EmailChannel()
        
        # Mock SMTP
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # Configure channel
            channel.smtp_host = "smtp.test.com"
            channel.smtp_username = "test@test.com"
            channel.smtp_password = "password"
            channel.from_email = "noreply@test.com"
            
            # Send notification
            result = await channel.send(
                "Test Subject",
                "Test message",
                {"recipients": ["user@example.com"]}
            )
            
            assert result is True
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_slack_channel(self):
        """Test Slack notification channel."""
        channel = SlackChannel()
        channel.webhook_url = "https://hooks.slack.com/test"
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = await channel.send(
                "Test Alert",
                "Test message",
                {"details": {"key": "value"}}
            )
            
            assert result is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notification_manager(self, notification_manager):
        """Test notification manager."""
        # Mock channels
        mock_email = Mock()
        mock_email.send = AsyncMock(return_value=True)
        
        mock_slack = Mock()
        mock_slack.send = AsyncMock(return_value=True)
        
        notification_manager.channels["email"] = mock_email
        notification_manager.channels["slack"] = mock_slack
        
        # Send notification
        results = await notification_manager.send(
            "website_changes",
            {
                "website_id": "website-123",
                "changes_count": 5,
                "recipients": ["user@example.com"]
            }
        )
        
        assert results["email"] is True
        assert results["slack"] is True
        
        # Verify template variables were replaced
        mock_email.send.assert_called_once()
        call_args = mock_email.send.call_args[0]
        assert "website-123" in call_args[1]  # Message
        assert "5 pages" in call_args[1]


@pytest.fixture
def sample_diff():
    """Sample diff output for testing."""
    return """--- Previous Version
+++ Current Version
@@ -1,4 +1,5 @@
 # Title
 
-Old content here
+New content here
+Additional line
 
 Footer"""