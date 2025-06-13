#!/usr/bin/env python3
"""Create a complete documentation folder structure from crawled data."""

import os
import re
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

from src.database.mongodb import get_mongo_collection
from src.database.postgres import SessionLocal
from sqlalchemy import text


def clean_filename(name):
    """Clean filename to be filesystem safe."""
    # Remove special characters
    name = re.sub(r'[<>:"/\\|?*]', '-', name)
    # Limit length
    if len(name) > 50:
        name = name[:50].rstrip('-')
    return name


def create_docs_folder():
    """Extract all documents and create folder structure."""
    db = SessionLocal()
    
    # Get HUD website
    website = db.execute(
        text("SELECT id, domain FROM websites WHERE domain = 'docs.hud.so'")
    ).fetchone()
    
    if not website:
        print("HUD website not found")
        return
        
    website_id = str(website[0])
    domain = website[1]
    
    # Create base directory
    base_dir = Path("hud_docs")
    base_dir.mkdir(exist_ok=True)
    
    # Get all pages
    pages = db.execute(
        text("SELECT id, url, title FROM pages WHERE website_id = :website_id ORDER BY url"),
        {"website_id": website_id}
    ).fetchall()
    
    print(f"Processing {len(pages)} pages...")
    
    # Get markdown collection
    collection = get_mongo_collection("markdown_documents")
    
    # Create main index content
    index_content = f"# {domain} Documentation\n\n"
    index_content += f"Complete documentation extracted from https://{domain}\n\n"
    index_content += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    index_content += f"**Total Pages**: {len(pages)}\n\n"
    index_content += "## Table of Contents\n\n"
    
    # Track statistics
    total_code_blocks = 0
    files_created = []
    
    # Group pages by path structure
    page_structure = {}
    
    for page in pages:
        page_id = str(page[0])
        url = page[1]
        title = page[2] or "Untitled"
        
        # Get markdown content
        doc = collection.find_one({"page_id": page_id})
        if not doc:
            continue
            
        content = doc.get("raw_markdown", "")
        code_blocks = content.count("```") // 2
        total_code_blocks += code_blocks
        
        # Parse URL to create file path
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip('/').split('/') if p]
        
        # Clean up content
        content = re.sub(r'\[​\]\([^)]+\)', '', content)  # Remove [​] links
        content = re.sub(r'^Copy\s*$', '', content, flags=re.MULTILINE)  # Remove Copy lines
        content = re.sub(r'\(https://[^)]+#([^)]+)\)', r'(#\1)', content)  # Fix internal links
        
        if not path_parts:
            # Root page
            file_path = base_dir / "home.md"
            section = "Home"
        else:
            # Create nested structure
            section = path_parts[0].title()
            
            if len(path_parts) == 1:
                filename = clean_filename(path_parts[0]) + ".md"
                file_path = base_dir / filename
            else:
                # Create subdirectory
                sub_dir = base_dir / path_parts[0]
                sub_dir.mkdir(parents=True, exist_ok=True)
                
                # Create filename from last part
                filename = clean_filename(path_parts[-1]) + ".md"
                file_path = sub_dir / filename
        
        # Add navigation header to content
        nav_content = f"# {title}\n\n"
        nav_content += f"**URL**: {url}\n\n"
        if code_blocks > 0:
            nav_content += f"**Code Examples**: {code_blocks}\n\n"
        nav_content += "---\n\n"
        nav_content += content
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(nav_content)
        
        files_created.append(file_path)
        
        # Add to page structure for index
        if section not in page_structure:
            page_structure[section] = []
        
        relative_path = file_path.relative_to(base_dir)
        page_structure[section].append({
            'title': title,
            'path': relative_path,
            'url': url,
            'code_blocks': code_blocks
        })
        
        print(f"Created: {file_path} ({code_blocks} code blocks)")
    
    # Create structured index
    for section, pages in sorted(page_structure.items()):
        index_content += f"\n### {section}\n\n"
        for page in pages:
            index_content += f"- [{page['title']}]({page['path']})"
            if page['code_blocks'] > 0:
                index_content += f" - *{page['code_blocks']} code examples*"
            index_content += "\n"
    
    # Add statistics
    index_content += f"\n## Statistics\n\n"
    index_content += f"- **Total Files**: {len(files_created)}\n"
    index_content += f"- **Total Code Blocks**: {total_code_blocks}\n"
    index_content += f"- **Average Code Blocks per Page**: {total_code_blocks / len(files_created):.1f}\n"
    
    # Write main index
    with open(base_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    # Create a code examples file
    examples_content = "# Code Examples\n\n"
    examples_content += "All code examples from the documentation.\n\n"
    
    example_count = 0
    # Second pass for code examples
    for page in pages:
        page_id = str(page[0])
        url = page[1]
        title = page[2] or "Untitled"
        
        doc = collection.find_one({"page_id": page_id})
        if not doc:
            continue
            
        content = doc.get("raw_markdown", "")
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w*)\n(.*?)\n```', content, re.DOTALL)
        if code_blocks:
            examples_content += f"\n## {title}\n\n"
            examples_content += f"Source: {url}\n\n"
            
            for lang, code in code_blocks:
                example_count += 1
                examples_content += f"### Example {example_count}"
                if lang:
                    examples_content += f" ({lang})"
                examples_content += "\n\n"
                examples_content += f"```{lang}\n{code}\n```\n\n"
    
    # Write code examples
    with open(base_dir / "CODE_EXAMPLES.md", 'w', encoding='utf-8') as f:
        f.write(examples_content)
    
    print(f"\n✅ Created documentation folder with {len(files_created)} files")
    print(f"📁 Location: {base_dir.absolute()}")
    print(f"📄 Main index: {base_dir}/README.md")
    print(f"💻 Code examples: {base_dir}/CODE_EXAMPLES.md")
    print(f"📊 Total code blocks: {total_code_blocks}")
    
    db.close()


if __name__ == "__main__":
    create_docs_folder()