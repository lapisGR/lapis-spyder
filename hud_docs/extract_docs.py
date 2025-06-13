import os
from pathlib import Path
from urllib.parse import urlparse
from src.database.mongodb import get_mongo_collection
from src.database.postgres import SessionLocal
from sqlalchemy import text
import re

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
        text("SELECT id, url FROM pages WHERE website_id = :website_id"),
        {"website_id": website_id}
    ).fetchall()
    
    print(f"Processing {len(pages)} pages...")
    
    # Get markdown collection
    collection = get_mongo_collection("markdown_documents")
    
    # Create index.md with llms.txt style content
    index_content = f"# {domain} Documentation\n\n"
    index_content += "Complete documentation extracted from https://docs.hud.so\n\n"
    index_content += "## Table of Contents\n\n"
    
    # Process each page
    for page in pages:
        page_id = str(page[0])
        url = page[1]
        
        # Get markdown content
        doc = collection.find_one({"page_id": page_id})
        if not doc:
            continue
            
        content = doc.get("raw_markdown", "")
        
        # Parse URL to create file path
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip('/').split('/') if p]
        
        if not path_parts:
            # Root page
            file_path = base_dir / "index.md"
        else:
            # Create nested structure
            if len(path_parts) == 1:
                file_path = base_dir / f"{path_parts[0]}.md"
            else:
                # Create subdirectory
                sub_dir = base_dir / "/".join(path_parts[:-1])
                sub_dir.mkdir(parents=True, exist_ok=True)
                file_path = sub_dir / f"{path_parts[-1]}.md"
        
        # Clean up content
        content = re.sub(r'\[​\]\([^)]+\)', '', content)  # Remove [​] links
        content = re.sub(r'^Copy\s*$', '', content, flags=re.MULTILINE)  # Remove Copy lines
        
        # Write file
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Add to index
        relative_path = file_path.relative_to(base_dir)
        index_content += f"- [{url}]({relative_path})\n"
        
        print(f"Created: {file_path}")
    
    # Write main index
    with open(base_dir / "README.md", 'w') as f:
        f.write(index_content)
    
    print(f"\nCreated documentation folder with {len(pages)} files")
    print(f"Main index: {base_dir}/README.md")
    
    db.close()

if __name__ == "__main__":
    create_docs_folder()
