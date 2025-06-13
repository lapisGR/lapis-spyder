#!/usr/bin/env python3
"""
Clean up code blocks in markdown by removing HTML syntax highlighting.
"""

import re
from bs4 import BeautifulSoup


def clean_code_block(code_html):
    """Remove syntax highlighting spans and extract clean code."""
    # Parse the HTML
    soup = BeautifulSoup(code_html, 'html.parser')
    
    # Extract just the text content
    code_text = soup.get_text()
    
    # Clean up extra whitespace
    lines = code_text.strip().split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    
    return '\n'.join(cleaned_lines)


def process_markdown_with_code(content):
    """Process markdown content to clean up code blocks."""
    # Pattern to match code blocks with HTML content
    code_block_pattern = r'```python\n(.*?)\n```'
    
    def replace_code_block(match):
        code_content = match.group(1)
        # If it contains HTML tags, clean it
        if '<span' in code_content or '<' in code_content:
            cleaned = clean_code_block(code_content)
            return f'```python\n{cleaned}\n```'
        return match.group(0)
    
    # Replace all code blocks
    cleaned_content = re.sub(code_block_pattern, replace_code_block, content, flags=re.DOTALL)
    
    # Also remove "Copy" text that appears before code blocks
    cleaned_content = re.sub(r'\nCopy```', '\n```', cleaned_content)
    
    return cleaned_content


# Test with the extracted content
if __name__ == "__main__":
    with open('advanced_patterns.md', 'r') as f:
        content = f.read()
    
    cleaned = process_markdown_with_code(content)
    
    print("CLEANED CONTENT:")
    print("="*60)
    print(cleaned)
    
    # Save cleaned version
    with open('advanced_patterns_clean.md', 'w') as f:
        f.write(cleaned)