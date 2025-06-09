"""Advanced Markdown conversion and processing."""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MarkdownDocument:
    """Structured markdown document."""
    
    url: str
    title: str
    content: str
    metadata: Dict[str, any]
    headings: List[Dict[str, any]]
    links: List[str]
    images: List[str]
    code_blocks: List[Dict[str, str]]
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "headings": self.headings,
            "links": self.links,
            "images": self.images,
            "code_blocks": self.code_blocks,
            "word_count": len(self.content.split()),
            "char_count": len(self.content)
        }


class MarkdownProcessor:
    """Process and enhance markdown content."""
    
    def __init__(self):
        """Initialize markdown processor."""
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        self.code_block_pattern = re.compile(r'```(\w*)\n(.*?)\n```', re.DOTALL)
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
    
    def process_markdown(self, content: str, url: str, title: str = "", 
                        metadata: Optional[Dict] = None) -> MarkdownDocument:
        """Process markdown content into structured document."""
        try:
            # Clean content
            content = self._clean_markdown(content)
            
            # Extract components
            headings = self._extract_headings(content)
            links = self._extract_links(content)
            images = self._extract_images(content)
            code_blocks = self._extract_code_blocks(content)
            
            # Add front matter if title is provided
            if title and not content.startswith('#'):
                content = f"# {title}\n\n{content}"
            
            # Create structured document
            return MarkdownDocument(
                url=url,
                title=title or self._extract_title(headings),
                content=content,
                metadata=metadata or {},
                headings=headings,
                links=links,
                images=images,
                code_blocks=code_blocks
            )
            
        except Exception as e:
            logger.error(f"Failed to process markdown for {url}: {e}")
            return MarkdownDocument(
                url=url,
                title=title,
                content=content,
                metadata=metadata or {},
                headings=[],
                links=[],
                images=[],
                code_blocks=[]
            )
    
    def _clean_markdown(self, content: str) -> str:
        """Clean and normalize markdown content."""
        # Remove carriage returns
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Fix common markdown issues
        # Ensure headers have space after #
        content = re.sub(r'^(#{1,6})([^\s#])', r'\1 \2', content, flags=re.MULTILINE)
        
        # Fix list formatting
        content = re.sub(r'^(\s*)[\*\+]\s+', r'\1- ', content, flags=re.MULTILINE)
        
        # Ensure blank lines around headers
        content = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', content)
        content = re.sub(r'(#{1,6} [^\n]+)\n([^\n#])', r'\1\n\n\2', content)
        
        # Remove excessive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Ensure document ends with newline
        if not content.endswith('\n'):
            content += '\n'
        
        return content.strip()
    
    def _extract_headings(self, content: str) -> List[Dict[str, any]]:
        """Extract heading structure from markdown."""
        headings = []
        
        for match in self.heading_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            
            # Generate ID from heading text
            heading_id = re.sub(r'[^\w\s-]', '', text.lower())
            heading_id = re.sub(r'[-\s]+', '-', heading_id)
            
            headings.append({
                "level": level,
                "text": text,
                "id": heading_id,
                "line": content[:match.start()].count('\n') + 1
            })
        
        return headings
    
    def _extract_title(self, headings: List[Dict[str, any]]) -> str:
        """Extract title from headings."""
        # Find first H1 heading
        for heading in headings:
            if heading["level"] == 1:
                return heading["text"]
        
        # Fallback to first heading
        if headings:
            return headings[0]["text"]
        
        return ""
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract all links from markdown."""
        links = []
        seen = set()
        
        for match in self.link_pattern.finditer(content):
            url = match.group(2).strip()
            if url and url not in seen:
                seen.add(url)
                links.append(url)
        
        return links
    
    def _extract_images(self, content: str) -> List[str]:
        """Extract all images from markdown."""
        images = []
        seen = set()
        
        for match in self.image_pattern.finditer(content):
            url = match.group(2).strip()
            if url and url not in seen:
                seen.add(url)
                images.append(url)
        
        return images
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown."""
        code_blocks = []
        
        for match in self.code_block_pattern.finditer(content):
            language = match.group(1) or "plaintext"
            code = match.group(2).strip()
            
            code_blocks.append({
                "language": language,
                "code": code,
                "line": content[:match.start()].count('\n') + 1
            })
        
        return code_blocks
    
    def enhance_markdown(self, content: str, enhancements: Dict[str, bool]) -> str:
        """Enhance markdown with additional formatting."""
        if enhancements.get("add_toc", False):
            content = self._add_table_of_contents(content)
        
        if enhancements.get("add_anchors", False):
            content = self._add_heading_anchors(content)
        
        if enhancements.get("format_links", False):
            content = self._format_links(content)
        
        if enhancements.get("highlight_code", False):
            content = self._enhance_code_blocks(content)
        
        return content
    
    def _add_table_of_contents(self, content: str) -> str:
        """Add table of contents to markdown."""
        headings = self._extract_headings(content)
        
        if len(headings) < 3:
            return content
        
        toc = ["## Table of Contents\n"]
        
        for heading in headings:
            if heading["level"] <= 3:  # Only include H1-H3
                indent = "  " * (heading["level"] - 1)
                link = f"[{heading['text']}](#{heading['id']})"
                toc.append(f"{indent}- {link}")
        
        toc_text = "\n".join(toc) + "\n\n"
        
        # Insert after first heading if exists
        first_heading_match = self.heading_pattern.search(content)
        if first_heading_match:
            insert_pos = first_heading_match.end()
            return content[:insert_pos] + "\n\n" + toc_text + content[insert_pos:]
        
        return toc_text + content
    
    def _add_heading_anchors(self, content: str) -> str:
        """Add anchor links to headings."""
        def add_anchor(match):
            level = match.group(1)
            text = match.group(2)
            heading_id = re.sub(r'[^\w\s-]', '', text.lower())
            heading_id = re.sub(r'[-\s]+', '-', heading_id)
            return f'{level} <a name="{heading_id}"></a>{text}'
        
        return self.heading_pattern.sub(add_anchor, content)
    
    def _format_links(self, content: str) -> str:
        """Format links with additional attributes."""
        def format_link(match):
            text = match.group(1)
            url = match.group(2)
            
            # Check if external link
            if url.startswith(('http://', 'https://')):
                domain = urlparse(url).netloc
                return f'[{text}]({url} "{domain}")'
            
            return match.group(0)
        
        return self.link_pattern.sub(format_link, content)
    
    def _enhance_code_blocks(self, content: str) -> str:
        """Enhance code blocks with syntax hints."""
        def enhance_code(match):
            language = match.group(1) or self._detect_language(match.group(2))
            code = match.group(2)
            
            if not language:
                language = "plaintext"
            
            return f'```{language}\n{code}\n```'
        
        return self.code_block_pattern.sub(enhance_code, content)
    
    def _detect_language(self, code: str) -> str:
        """Simple language detection for code blocks."""
        patterns = {
            'python': [r'def\s+\w+\s*\(', r'import\s+\w+', r'print\s*\('],
            'javascript': [r'function\s+\w+\s*\(', r'const\s+\w+', r'console\.log'],
            'html': [r'<html', r'<div', r'<body', r'</\w+>'],
            'css': [r'\.\w+\s*{', r'#\w+\s*{', r':\s*\w+;'],
            'json': [r'{\s*"', r'"\s*:\s*["{[]', r'}\s*,?\s*$'],
            'yaml': [r'^\s*\w+:', r'^\s*-\s+\w+'],
            'sql': [r'SELECT\s+', r'FROM\s+', r'WHERE\s+', r'INSERT\s+INTO'],
        }
        
        code_lower = code.lower()
        
        for language, patterns_list in patterns.items():
            for pattern in patterns_list:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    return language
        
        return ""
    
    def merge_markdown_documents(self, documents: List[MarkdownDocument]) -> str:
        """Merge multiple markdown documents into one."""
        if not documents:
            return ""
        
        merged_content = []
        
        for i, doc in enumerate(documents):
            if i > 0:
                merged_content.append("\n\n---\n\n")
            
            # Add document header
            merged_content.append(f"## {doc.title}")
            merged_content.append(f"*Source: {doc.url}*\n")
            
            # Add content
            merged_content.append(doc.content)
        
        return "\n".join(merged_content)


# Singleton instance
markdown_processor = MarkdownProcessor()


# Convenience functions
def process_markdown(content: str, url: str, title: str = "", 
                    metadata: Optional[Dict] = None) -> MarkdownDocument:
    """Process markdown content into structured document."""
    return markdown_processor.process_markdown(content, url, title, metadata)


def enhance_markdown(content: str, **enhancements) -> str:
    """Enhance markdown with additional formatting."""
    return markdown_processor.enhance_markdown(content, enhancements)


def merge_documents(documents: List[MarkdownDocument]) -> str:
    """Merge multiple markdown documents."""
    return markdown_processor.merge_markdown_documents(documents)