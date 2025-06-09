"""Spider-rs integration wrapper for Python."""

import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor

from src.config import settings
from src.utils.logging import get_logger
from src.utils.performance import measure_performance, cached

logger = get_logger(__name__)


@dataclass
class SpiderConfig:
    """Spider crawler configuration."""
    
    url: str
    max_pages: int = 100
    max_depth: int = 3
    concurrent_requests: int = 10
    respect_robots_txt: bool = True
    user_agent: str = field(default_factory=lambda: settings.user_agent)
    request_timeout: int = 30
    crawl_delay: float = 0.5
    allowed_domains: List[str] = field(default_factory=list)
    blacklist_patterns: List[str] = field(default_factory=list)
    whitelist_patterns: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    
    def to_spider_args(self) -> List[str]:
        """Convert config to spider CLI arguments."""
        args = [
            self.url,
            "--max-pages", str(self.max_pages),
            "--max-depth", str(self.max_depth),
            "--concurrent-requests", str(self.concurrent_requests),
            "--user-agent", self.user_agent,
            "--request-timeout", str(self.request_timeout),
            "--delay", str(int(self.crawl_delay * 1000)),  # Convert to milliseconds
        ]
        
        if not self.respect_robots_txt:
            args.append("--no-respect-robots-txt")
        
        for domain in self.allowed_domains:
            args.extend(["--allowed-domain", domain])
        
        for pattern in self.blacklist_patterns:
            args.extend(["--blacklist", pattern])
            
        for pattern in self.whitelist_patterns:
            args.extend(["--whitelist", pattern])
        
        # Add custom headers
        for key, value in self.headers.items():
            args.extend(["--header", f"{key}: {value}"])
        
        return args


@dataclass
class CrawlResult:
    """Result from a crawl operation."""
    
    url: str
    status_code: int
    content: str
    headers: Dict[str, str]
    error: Optional[str] = None
    response_time: float = 0.0
    size_bytes: int = 0
    links: List[str] = field(default_factory=list)
    
    @classmethod
    def from_spider_output(cls, data: Dict[str, Any]) -> "CrawlResult":
        """Create CrawlResult from spider output."""
        return cls(
            url=data.get("url", ""),
            status_code=data.get("status_code", 0),
            content=data.get("content", ""),
            headers=data.get("headers", {}),
            error=data.get("error"),
            response_time=data.get("response_time", 0.0),
            size_bytes=len(data.get("content", "").encode("utf-8")),
            links=data.get("links", [])
        )


class SpiderWrapper:
    """Python wrapper for Spider-rs crawler."""
    
    def __init__(self):
        """Initialize spider wrapper."""
        self.spider_path = self._find_spider_executable()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def _find_spider_executable(self) -> Path:
        """Find spider executable in the project."""
        # Use Python wrapper for now
        python_wrapper = Path(__file__).parent / "spider_cli_wrapper.py"
        if python_wrapper.exists():
            logger.info(f"Using Python spider wrapper at: {python_wrapper}")
            return python_wrapper
        
        # Look for spider executable in multiple locations
        possible_paths = [
            Path("spider/target/release/spider_cli"),
            Path("spider/target/debug/spider_cli"),
            Path("/usr/local/bin/spider_cli"),
            Path.home() / ".cargo/bin/spider_cli",
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                logger.info(f"Found spider executable at: {path}")
                return path
        
        # If not found, try to build it
        spider_dir = Path("spider")
        if spider_dir.exists():
            logger.info("Spider executable not found, attempting to build...")
            try:
                subprocess.run(
                    ["cargo", "build", "--release", "-p", "spider_cli"],
                    cwd=spider_dir,
                    check=True
                )
                built_path = spider_dir / "target/release/spider_cli"
                if built_path.exists():
                    logger.info(f"Successfully built spider at: {built_path}")
                    return built_path
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to build spider: {e}")
        
        raise RuntimeError("Spider executable not found. Please build the spider project first.")
    
    @measure_performance("spider_crawl_url")
    async def crawl_url(self, url: str, config: Optional[SpiderConfig] = None) -> List[CrawlResult]:
        """Crawl a single URL and return results."""
        if config is None:
            config = SpiderConfig(url=url)
        else:
            config.url = url
        
        logger.info(f"Starting crawl for: {url}")
        
        try:
            # Run spider in subprocess
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                self._run_spider_subprocess,
                config
            )
            
            logger.info(f"Crawl completed for {url}: {len(results)} pages found")
            return results
            
        except Exception as e:
            logger.error(f"Crawl failed for {url}: {e}")
            return [CrawlResult(
                url=url,
                status_code=0,
                content="",
                headers={},
                error=str(e)
            )]
    
    @measure_performance("spider_subprocess")
    def _run_spider_subprocess(self, config: SpiderConfig) -> List[CrawlResult]:
        """Run spider in subprocess and parse results."""
        # Check if using Python wrapper
        if str(self.spider_path).endswith('.py'):
            args = ["python3", str(self.spider_path)] + config.to_spider_args()
        else:
            args = [str(self.spider_path)] + config.to_spider_args()
            # Add JSON output format
            args.extend(["--output-format", "json"])
        
        logger.debug(f"Running spider with args: {' '.join(args)}")
        
        try:
            # Run spider subprocess
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=settings.crawl_timeout_seconds
            )
            
            if result.returncode != 0:
                logger.error(f"Spider returned non-zero exit code: {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
                raise RuntimeError(f"Spider failed: {result.stderr}")
            
            # Parse JSON output
            crawl_results = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    crawl_results.append(CrawlResult.from_spider_output(data))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse spider output line: {e}")
                    continue
            
            return crawl_results
            
        except subprocess.TimeoutExpired:
            logger.error(f"Spider crawl timed out after {settings.crawl_timeout_seconds} seconds")
            raise
        except Exception as e:
            logger.error(f"Spider subprocess error: {e}")
            raise
    
    async def crawl_website(self, website_url: str, config: Optional[SpiderConfig] = None) -> Dict[str, Any]:
        """Crawl an entire website and return aggregated results."""
        if config is None:
            config = SpiderConfig(
                url=website_url,
                max_pages=settings.max_pages_per_crawl,
                concurrent_requests=settings.concurrent_requests
            )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Crawl the website
            results = await self.crawl_url(website_url, config)
            
            # Aggregate statistics
            total_pages = len(results)
            successful_pages = sum(1 for r in results if 200 <= r.status_code < 300)
            failed_pages = sum(1 for r in results if r.error or r.status_code >= 400)
            total_size = sum(r.size_bytes for r in results)
            
            duration = asyncio.get_event_loop().time() - start_time
            
            return {
                "url": website_url,
                "total_pages": total_pages,
                "successful_pages": successful_pages,
                "failed_pages": failed_pages,
                "total_size_bytes": total_size,
                "duration_seconds": duration,
                "pages_per_second": total_pages / duration if duration > 0 else 0,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Website crawl failed for {website_url}: {e}")
            return {
                "url": website_url,
                "total_pages": 0,
                "successful_pages": 0,
                "failed_pages": 1,
                "total_size_bytes": 0,
                "duration_seconds": asyncio.get_event_loop().time() - start_time,
                "error": str(e),
                "results": []
            }
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is crawlable."""
        if not url.startswith(("http://", "https://")):
            return False
        
        # Add more validation as needed
        return True


# Singleton instance
spider_wrapper = SpiderWrapper()


# Convenience functions
async def crawl_url(url: str, **kwargs) -> List[CrawlResult]:
    """Crawl a single URL."""
    config = SpiderConfig(url=url, **kwargs)
    return await spider_wrapper.crawl_url(url, config)


async def crawl_website(url: str, **kwargs) -> Dict[str, Any]:
    """Crawl an entire website."""
    config = SpiderConfig(url=url, **kwargs)
    return await spider_wrapper.crawl_website(url, config)