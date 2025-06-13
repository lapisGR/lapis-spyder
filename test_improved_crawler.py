#!/usr/bin/env python3
"""
Test the improved crawler on existing HTML to verify code block extraction.
"""

from src.database.mongodb import get_mongo_collection
from src.crawler.processor import html_processor
from src.utils.logging import get_logger

logger = get_logger(__name__)


def test_improved_conversion():
    # Get raw HTML collection
    html_collection = get_mongo_collection('raw_html')
    
    # Find the task-creation page
    doc = html_collection.find_one({'url': 'https://docs.hud.so/task-creation'})
    
    if not doc or not doc.get('raw_html'):
        logger.error("Could not find HTML for task-creation page")
        return
    
    logger.info("Testing improved HTML to Markdown conversion...")
    
    # Convert using improved processor
    markdown = html_processor.html_to_markdown(doc['raw_html'], doc['url'])
    
    # Check for code blocks
    code_block_count = markdown.count('```')
    logger.info(f"Found {code_block_count // 2} code blocks")
    
    # Look for the Advanced Patterns section
    if '## Advanced Patterns' in markdown or '## ​Advanced Patterns' in markdown:
        logger.info("Found Advanced Patterns section")
        
        # Extract that section
        import re
        pattern = r'##.*?Advanced Patterns.*?(?=^##\s|\Z)'
        match = re.search(pattern, markdown, re.MULTILINE | re.DOTALL)
        
        if match:
            section = match.group(0)
            print("\n" + "="*60)
            print("ADVANCED PATTERNS SECTION:")
            print("="*60)
            print(section[:1000] + "..." if len(section) > 1000 else section)
            
            # Save full markdown for inspection
            with open('improved_task_creation.md', 'w') as f:
                f.write(markdown)
            logger.info("Saved full markdown to improved_task_creation.md")
    else:
        logger.warning("Could not find Advanced Patterns section")
        # Save anyway for debugging
        with open('improved_task_creation_debug.md', 'w') as f:
            f.write(markdown)
        logger.info("Saved markdown to improved_task_creation_debug.md for debugging")


if __name__ == "__main__":
    test_improved_conversion()