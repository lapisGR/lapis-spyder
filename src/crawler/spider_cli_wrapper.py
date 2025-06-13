#!/usr/bin/env python3
"""
Simple Python wrapper for Spider CLI that outputs JSON.
This is a temporary solution until the Rust spider is properly integrated.
"""

import json
import sys
import time
import asyncio
from typing import List, Dict, Any
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup

try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False
    print("Warning: html2text not available, markdown conversion disabled")


class SimpleSpider:
    """Simple spider implementation for development."""
    
    def __init__(self, args: List[str]):
        self.url = args[0] if args else ""
        self.max_pages = 10
        self.max_depth = 2
        self.visited_urls = set()
        self.to_visit = []
        if HAS_HTML2TEXT:
            self.h2t = html2text.HTML2Text()
            self.h2t.ignore_links = False
            self.h2t.ignore_images = False
            self.h2t.body_width = 0  # Don't wrap lines
            self.h2t.mark_code = True  # Preserve code blocks
            self.h2t.wrap_links = False  # Don't wrap links
            self.h2t.wrap_list_items = False  # Don't wrap list items
            self.h2t.skip_internal_links = False  # Keep internal links
        else:
            self.h2t = None
        
        # Parse arguments
        i = 1
        while i < len(args):
            if args[i] == "--max-pages" and i + 1 < len(args):
                self.max_pages = int(args[i + 1])
                i += 2
            elif args[i] == "--max-depth" and i + 1 < len(args):
                self.max_depth = int(args[i + 1])
                i += 2
            else:
                i += 1
    
    async def crawl(self):
        """Perform the crawl."""
        if not self.url:
            return
        
        self.to_visit.append((self.url, 0))
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while self.to_visit and len(self.visited_urls) < self.max_pages:
                url, depth = self.to_visit.pop(0)
                
                if url in self.visited_urls or depth > self.max_depth:
                    continue
                
                self.visited_urls.add(url)
                
                try:
                    response = await client.get(url, follow_redirects=True)
                    
                    # Convert HTML to markdown
                    markdown = ""
                    if 200 <= response.status_code < 300 and self.h2t:
                        try:
                            markdown = self.h2t.handle(response.text)
                        except Exception as e:
                            markdown = f"Error converting to markdown: {e}"
                    
                    # Output result as JSON
                    result = {
                        "url": url,
                        "status_code": response.status_code,
                        "content": response.text,
                        "markdown": markdown,
                        "headers": dict(response.headers),
                        "response_time": response.elapsed.total_seconds(),
                        "links": []
                    }
                    
                    # Extract links if successful
                    if 200 <= response.status_code < 300:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        base_domain = urlparse(self.url).netloc
                        
                        for link in soup.find_all('a', href=True):
                            href = urljoin(url, link['href'])
                            if urlparse(href).netloc == base_domain:
                                result["links"].append(href)
                                if depth < self.max_depth:
                                    self.to_visit.append((href, depth + 1))
                    
                    print(json.dumps(result))
                    
                except Exception as e:
                    result = {
                        "url": url,
                        "status_code": 0,
                        "content": "",
                        "headers": {},
                        "error": str(e),
                        "response_time": 0
                    }
                    print(json.dumps(result))
                
                # Small delay between requests
                await asyncio.sleep(0.5)


async def main():
    """Main entry point."""
    spider = SimpleSpider(sys.argv[1:])
    await spider.crawl()


if __name__ == "__main__":
    asyncio.run(main())