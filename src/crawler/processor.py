"""HTML processing and content extraction."""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

from bs4 import BeautifulSoup, Comment
from markdownify import markdownify as md

from src.utils.logging import get_logger

logger = get_logger(__name__)


class HTMLProcessor:
    """Process and extract content from HTML."""
    
    def __init__(self):
        """Initialize HTML processor."""
        # Tags to remove completely with their content
        self.remove_tags = {
            'script', 'style', 'noscript', 'iframe', 'object', 
            'embed', 'form', 'input', 'button', 'select', 'textarea'
        }
        
        # Tags to unwrap (keep content, remove tag)
        self.unwrap_tags = {'font', 'span', 'div'}
        
        # Inline tags that should not add newlines
        self.inline_tags = {
            'a', 'abbr', 'acronym', 'b', 'bdo', 'big', 'br', 'cite',
            'code', 'dfn', 'em', 'i', 'kbd', 'label', 'q', 'samp',
            'small', 'span', 'strong', 'sub', 'sup', 'time', 'tt', 'var'
        }
    
    def extract_content(self, html: str, url: str) -> Dict[str, any]:
        """Extract structured content from HTML."""
        try:
            soup = BeautifulSoup(html, 'html5lib')
            
            # Remove unwanted elements
            self._clean_html(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract links
            links = self._extract_links(soup, url)
            
            # Extract images
            images = self._extract_images(soup, url)
            
            # Extract headings structure
            headings = self._extract_headings(soup)
            
            return {
                "url": url,
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "metadata": metadata,
                "content": content,
                "links": links,
                "images": images,
                "headings": headings,
                "text_content": soup.get_text(separator=' ', strip=True),
                "word_count": len(soup.get_text().split()),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            return {
                "url": url,
                "title": "",
                "description": "",
                "content": "",
                "error": str(e)
            }
    
    def _clean_html(self, soup: BeautifulSoup) -> None:
        """Clean HTML by removing unwanted elements."""
        # Remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove specific tags
        for tag in self.remove_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove navigation elements by tag
        for tag in ['nav', 'header', 'footer', 'aside']:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove elements with navigation-related classes
        nav_classes = ['navigation', 'nav', 'menu', 'sidebar', 'header', 'footer', 
                      'breadcrumb', 'toc', 'table-of-contents']
        for class_name in nav_classes:
            for element in soup.find_all(class_=re.compile(rf'\b{class_name}\b', re.I)):
                element.decompose()
        
        # Remove hidden elements
        for element in soup.find_all(attrs={'style': re.compile(r'display:\s*none', re.I)}):
            element.decompose()
        
        for element in soup.find_all(class_=re.compile(r'hidden|invisible', re.I)):
            element.decompose()
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """Extract metadata from HTML."""
        metadata = {
            "url": url,
            "domain": urlparse(url).netloc
        }
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name', '').lower()
            property = tag.get('property', '').lower()
            content = tag.get('content', '')
            
            if name == 'description':
                metadata["description"] = content
            elif name == 'keywords':
                metadata["keywords"] = content
            elif name == 'author':
                metadata["author"] = content
            elif name == 'viewport':
                metadata["viewport"] = content
            elif property == 'og:title':
                metadata["og_title"] = content
            elif property == 'og:description':
                metadata["og_description"] = content
            elif property == 'og:image':
                metadata["og_image"] = content
            elif property == 'og:type':
                metadata["og_type"] = content
        
        # Language
        html_tag = soup.find('html')
        if html_tag:
            metadata["language"] = html_tag.get('lang', '')
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            metadata["canonical_url"] = canonical.get('href', '')
        
        return metadata
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content area from HTML."""
        # Try to find main content areas
        main_selectors = [
            'main',
            'article',
            '[role="main"]',
            '#main',
            '#content',
            '.main',
            '.content',
            '.post',
            '.article'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return self._clean_text(main_content.get_text(separator=' ', strip=True))
        
        # Fallback to body
        body = soup.find('body')
        if body:
            # Remove navigation, footer, etc.
            for tag in ['nav', 'header', 'footer', 'aside']:
                for element in body.find_all(tag):
                    element.decompose()
            
            return self._clean_text(body.get_text(separator=' ', strip=True))
        
        return ""
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links from HTML."""
        links = []
        seen_urls = set()
        
        for tag in soup.find_all('a', href=True):
            href = tag['href'].strip()
            if not href or href.startswith('#'):
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            
            # Skip duplicates
            if absolute_url in seen_urls:
                continue
            
            seen_urls.add(absolute_url)
            
            link_data = {
                "url": absolute_url,
                "text": tag.get_text(strip=True),
                "title": tag.get('title', ''),
                "rel": tag.get('rel', []),
                "target": tag.get('target', '')
            }
            
            # Classify link type
            if urlparse(absolute_url).netloc != urlparse(base_url).netloc:
                link_data["type"] = "external"
            else:
                link_data["type"] = "internal"
            
            links.append(link_data)
        
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all images from HTML."""
        images = []
        seen_urls = set()
        
        for tag in soup.find_all('img'):
            src = tag.get('src', '').strip()
            if not src:
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, src)
            
            # Skip duplicates
            if absolute_url in seen_urls:
                continue
            
            seen_urls.add(absolute_url)
            
            images.append({
                "url": absolute_url,
                "alt": tag.get('alt', ''),
                "title": tag.get('title', ''),
                "width": tag.get('width', ''),
                "height": tag.get('height', '')
            })
        
        return images
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, any]]:
        """Extract heading structure from HTML."""
        headings = []
        
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])
            text = tag.get_text(strip=True)
            
            if text:
                headings.append({
                    "level": level,
                    "text": text,
                    "id": tag.get('id', ''),
                    "tag": tag.name
                })
        
        return headings
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[tuple]:
        """Extract code blocks and convert them to clean markdown format."""
        code_blocks = []
        
        # First look for div elements with code-block class (modern documentation sites)
        all_divs = soup.find_all('div')
        for div in all_divs:
            classes = div.get('class', [])
            if classes and any('code-block' in cls for cls in classes):
                pre_tag = div.find('pre')
                if pre_tag:
                    # Extract language from div classes
                    language = ''
                    div_classes = ' '.join(classes)
                    if 'language-' in div_classes:
                        lang_match = re.search(r'language-(\w+)', div_classes)
                        if lang_match:
                            language = lang_match.group(1)
                    
                    # Get code content
                    code_text = pre_tag.get_text()
                    
                    # Create clean code block
                    clean_code = f"\n```{language}\n{code_text.strip()}\n```\n"
                    
                    # Replace the entire div with placeholder
                    code_blocks.append((div, clean_code))
        
        # Also look for standalone pre tags (fallback for simpler sites)
        for pre_tag in soup.find_all('pre'):
            # Skip if already processed as part of code-block div
            parent = pre_tag.parent
            is_in_code_block = False
            while parent:
                if parent.name == 'div':
                    parent_classes = parent.get('class', [])
                    if parent_classes and any('code-block' in cls for cls in parent_classes):
                        is_in_code_block = True
                        break
                parent = parent.parent
            
            if not is_in_code_block:
                # No code-block parent found, process this pre tag
                # Extract code content
                code_tag = pre_tag.find('code')
                if code_tag:
                    # Modern syntax highlighted code - extract text without spans
                    code_text = code_tag.get_text()
                else:
                    # Simple pre block
                    code_text = pre_tag.get_text()
                
                # Determine language from pre or code tag classes
                language = ''
                element_with_class = code_tag if code_tag and code_tag.get('class') else pre_tag
                if element_with_class and element_with_class.get('class'):
                    classes = ' '.join(element_with_class.get('class', []))
                    # Look for language indicators
                    if 'language-' in classes:
                        lang_match = re.search(r'language-(\w+)', classes)
                        if lang_match:
                            language = lang_match.group(1)
                    elif 'python' in classes.lower():
                        language = 'python'
                    elif 'javascript' in classes.lower() or 'js' in classes.lower():
                        language = 'javascript'
                
                # Create clean code block
                clean_code = f"\n```{language}\n{code_text.strip()}\n```\n"
                
                code_blocks.append((pre_tag, clean_code))
        
        return code_blocks
    
    def html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        soup = BeautifulSoup(html, 'html5lib')
        self._clean_html(soup)
        return self._clean_text(soup.get_text(separator=' ', strip=True))
    
    def html_to_markdown(self, html: str, base_url: str = "") -> str:
        """Convert HTML to Markdown format."""
        try:
            soup = BeautifulSoup(html, 'html5lib')
            
            # Extract and preserve code blocks before cleaning
            code_blocks = self._extract_code_blocks(soup)
            
            # Replace code blocks with placeholders
            for i, (element, _) in enumerate(code_blocks):
                placeholder = soup.new_tag('p')
                placeholder.string = f"CODEBLOCKPLACEHOLDER{i:04d}"
                element.replace_with(placeholder)
            
            self._clean_html(soup)
            
            # Convert to markdown
            markdown = md(
                str(soup),
                heading_style="ATX",
                bullets="-",
                code_language="python",
                wrap=False,  # Don't wrap lines
                convert=['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                        'strong', 'em', 'b', 'i', 'a', 'ul', 'ol', 'li', 
                        'blockquote', 'code', 'pre', 'img', 'hr', 'br',
                        'table', 'thead', 'tbody', 'tr', 'th', 'td']  # Explicitly convert these tags
            )
            
            # Restore code blocks
            for i, (_, clean_code) in enumerate(code_blocks):
                placeholder = f"CODEBLOCKPLACEHOLDER{i:04d}"
                markdown = markdown.replace(placeholder, clean_code)
            
            # Post-process markdown
            markdown = self._post_process_markdown(markdown, base_url)
            
            return markdown
            
        except Exception as e:
            logger.error(f"Failed to convert HTML to markdown: {e}")
            return ""
    
    def _post_process_markdown(self, markdown: str, base_url: str) -> str:
        """Post-process markdown content."""
        # Fix relative URLs
        if base_url:
            # Fix image URLs
            markdown = re.sub(
                r'!\[([^\]]*)\]\((?!http)([^)]+)\)',
                lambda m: f'![{m.group(1)}]({urljoin(base_url, m.group(2))})',
                markdown
            )
            
            # Fix link URLs
            markdown = re.sub(
                r'(?<!!)\[([^\]]+)\]\((?!http)([^)]+)\)',
                lambda m: f'[{m.group(1)}]({urljoin(base_url, m.group(2))})',
                markdown
            )
        
        # Remove excessive blank lines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Remove standalone "Copy" lines
        markdown = re.sub(r'^Copy\s*$', '', markdown, flags=re.MULTILINE)
        
        # Remove [​] artifacts
        markdown = re.sub(r'\[​\]', '', markdown)
        
        # Clean up headers with [​] links
        markdown = re.sub(r'^(#{1,6})\s*\[​\]\([^)]+\)\s*(.+)$', r'\1 \2', markdown, flags=re.MULTILINE)
        
        # Ensure headers have blank lines around them
        markdown = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', markdown)
        markdown = re.sub(r'(#{1,6} [^\n]+)\n([^\n])', r'\1\n\n\2', markdown)
        
        return markdown.strip()


# Singleton instance
html_processor = HTMLProcessor()


# Convenience functions
def extract_content(html: str, url: str) -> Dict[str, any]:
    """Extract structured content from HTML."""
    return html_processor.extract_content(html, url)


def html_to_markdown(html: str, base_url: str = "") -> str:
    """Convert HTML to Markdown."""
    return html_processor.html_to_markdown(html, base_url)


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    return html_processor.html_to_text(html)