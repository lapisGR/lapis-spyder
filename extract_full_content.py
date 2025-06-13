#!/usr/bin/env python3
"""
Extract full content from HTML including code blocks.
"""

import re
import json
from bs4 import BeautifulSoup
from src.database.mongodb import get_mongo_collection
from src.utils.logging import get_logger

logger = get_logger(__name__)


def extract_text_from_element(element):
    """Extract text from an element, preserving code blocks."""
    if element.name == 'pre':
        # This is a code block
        code_lines = []
        # Extract all text while preserving structure
        for child in element.descendants:
            if hasattr(child, 'name'):
                if child.name == 'br':
                    code_lines.append('\n')
                elif child.name == 'span' and 'line' in child.get('class', []):
                    # Line span - get all its text
                    line_text = ''.join(str(x) for x in child.children if x.string)
                    code_lines.append(line_text + '\n')
            elif child.string:
                code_lines.append(child.string)
        
        code_content = ''.join(code_lines).strip()
        return f"\n\n```python\n{code_content}\n```\n\n"
    
    elif element.name == 'code' and element.parent.name != 'pre':
        # Inline code
        return f"`{element.get_text(strip=True)}`"
    
    elif element.name in ['p', 'div', 'li']:
        # Regular text elements
        text_parts = []
        for child in element.children:
            if hasattr(child, 'name'):
                text_parts.append(extract_text_from_element(child))
            else:
                text_parts.append(str(child))
        return ''.join(text_parts).strip()
    
    elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level = int(element.name[1])
        return f"\n\n{'#' * level} {element.get_text(strip=True)}\n\n"
    
    elif element.name == 'ul':
        items = []
        for li in element.find_all('li', recursive=False):
            items.append(f"- {extract_text_from_element(li)}")
        return '\n'.join(items) + '\n'
    
    elif element.name == 'ol':
        items = []
        for i, li in enumerate(element.find_all('li', recursive=False), 1):
            items.append(f"{i}. {extract_text_from_element(li)}")
        return '\n'.join(items) + '\n'
    
    else:
        return element.get_text(strip=True)


def extract_advanced_patterns_section(html_content):
    """Extract the Advanced Patterns section with code blocks."""
    soup = BeautifulSoup(html_content, 'html5lib')
    
    # Find main content area (usually in article or main tag)
    main_content = soup.find('main') or soup.find('article') or soup.find('div', {'class': re.compile('content|main')})
    
    if not main_content:
        logger.warning("Could not find main content area")
        return None
    
    # Find Advanced Patterns heading
    advanced_heading = None
    for heading in main_content.find_all(re.compile('^h[1-6]$')):
        if 'Advanced Patterns' in heading.get_text():
            advanced_heading = heading
            break
    
    if not advanced_heading:
        logger.warning("Could not find Advanced Patterns heading")
        return None
    
    # Extract content after the heading until next major heading
    content = [f"## Advanced Patterns\n"]
    
    current = advanced_heading.find_next_sibling()
    while current:
        # Stop if we hit another major heading
        if current.name and re.match(r'^h[1-3]$', current.name) and 'Related Guides' not in current.get_text():
            # Found a sub-heading, include it
            content.append(extract_text_from_element(current))
        elif current.name and re.match(r'^h[1-2]$', current.name):
            # Major heading, stop here
            break
        elif current.name:
            # Regular content
            extracted = extract_text_from_element(current)
            if extracted.strip():
                content.append(extracted)
        
        current = current.find_next_sibling()
    
    return '\n'.join(content)


def main():
    # Get collections
    html_collection = get_mongo_collection('raw_html')
    
    # Find the task-creation page
    doc = html_collection.find_one({'url': 'https://docs.hud.so/task-creation'})
    
    if not doc or not doc.get('raw_html'):
        logger.error("Could not find HTML for task-creation page")
        return
    
    logger.info("Extracting Advanced Patterns section...")
    
    # Extract the section
    section_content = extract_advanced_patterns_section(doc['raw_html'])
    
    if section_content:
        print("\n" + "="*60)
        print("ADVANCED PATTERNS SECTION:")
        print("="*60)
        print(section_content)
        
        # Save to file
        with open('advanced_patterns.md', 'w') as f:
            f.write(section_content)
        logger.info("Saved to advanced_patterns.md")
    else:
        logger.error("Failed to extract Advanced Patterns section")
        
        # Debug: save raw HTML to inspect
        with open('task_creation_raw.html', 'w') as f:
            f.write(doc['raw_html'])
        logger.info("Saved raw HTML to task_creation_raw.html for inspection")


if __name__ == "__main__":
    main()