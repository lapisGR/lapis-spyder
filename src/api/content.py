"""Content retrieval and processing API endpoints."""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.database.postgres import get_db
from src.database.mongodb import get_mongo_collection
from src.ai.tasks import process_page_with_ai, batch_process_pages_task
from src.utils.logging import get_logger
import zipfile
import io
from pathlib import Path

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models
class PageSummary(BaseModel):
    """Page summary information."""
    
    id: str
    url: str
    title: str
    content_hash: str
    last_modified: Optional[datetime]
    ai_processed: bool = False
    summary: Optional[str]
    page_type: Optional[str]
    
    class Config:
        from_attributes = True


class PageContent(BaseModel):
    """Full page content."""
    
    id: str
    url: str
    title: str
    raw_markdown: str
    structured_markdown: Optional[str]
    metadata: dict
    ai_processed: bool
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProcessingRequest(BaseModel):
    """Request to process pages with AI."""
    
    page_ids: List[str] = Field(..., min_items=1, max_items=100)


class ProcessingStatus(BaseModel):
    """Processing job status."""
    
    job_id: str
    status: str
    total_pages: int
    processed_pages: int
    failed_pages: int


# API Endpoints
@router.get("/{website_id}/pages", response_model=List[PageSummary])
async def list_website_pages(
    website_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    ai_processed_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all pages for a website."""
    # Verify website belongs to user
    website = db.execute(
        text("""
        SELECT id FROM websites 
        WHERE id = :website_id AND user_id = :user_id
        """),
        {"website_id": website_id, "user_id": str(current_user.id)}
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Get pages from PostgreSQL
    query = """
        SELECT id, url, title, content_hash, last_modified
        FROM pages
        WHERE website_id = :website_id
        ORDER BY url
        LIMIT :limit OFFSET :offset
    """
    
    pages = db.execute(
        text(query), 
        {"website_id": website_id, "limit": limit, "offset": offset}
    ).fetchall()
    
    # Get AI processing status from MongoDB
    collection = get_mongo_collection("markdown_documents")
    page_summaries = []
    
    for page in pages:
        page_id = str(page[0])
        
        # Check if processed
        mongo_doc = collection.find_one({"page_id": page_id})
        ai_processed = False
        summary = None
        page_type = None
        
        if mongo_doc and mongo_doc.get("metadata", {}).get("ai_processed"):
            ai_processed = True
            summary = mongo_doc["metadata"].get("summary")
            page_type = mongo_doc["metadata"].get("page_type")
        
        if not ai_processed_only or ai_processed:
            page_summaries.append(PageSummary(
                id=page_id,
                url=page[1],
                title=page[2] or "Untitled",
                content_hash=page[3],
                last_modified=page[4],
                ai_processed=ai_processed,
                summary=summary,
                page_type=page_type
            ))
    
    return page_summaries


@router.get("/{website_id}/page/{page_id}", response_model=PageContent)
async def get_page_content(
    website_id: str,
    page_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full content for a specific page."""
    # Verify page belongs to user's website
    page = db.execute(
        text("""
        SELECT p.id, p.url, p.title
        FROM pages p
        JOIN websites w ON p.website_id = w.id
        WHERE p.id = :page_id AND p.website_id = :website_id AND w.user_id = :user_id
        """),
        {"page_id": page_id, "website_id": website_id, "user_id": str(current_user.id)}
    ).fetchone()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Get content from MongoDB
    collection = get_mongo_collection("markdown_documents")
    mongo_doc = collection.find_one({"page_id": page_id})
    
    if not mongo_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page content not found"
        )
    
    return PageContent(
        id=page_id,
        url=page[1],
        title=page[2] or "Untitled",
        raw_markdown=mongo_doc.get("raw_markdown", ""),
        structured_markdown=mongo_doc.get("structured_markdown"),
        metadata=mongo_doc.get("metadata", {}),
        ai_processed=mongo_doc.get("metadata", {}).get("ai_processed", False),
        processed_at=mongo_doc.get("processed_at")
    )


@router.get("/{website_id}/llms.txt")
async def get_llms_txt(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get llms.txt format index for the website."""
    # Verify website belongs to user
    website = db.execute(
        text("""
        SELECT id, domain FROM websites 
        WHERE id = :website_id AND user_id = :user_id
        """),
        {"website_id": website_id, "user_id": str(current_user.id)}
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Get all pages for the website
    pages = db.execute(
        text("""
        SELECT id, url, title, url_path
        FROM pages
        WHERE website_id = :website_id
        ORDER BY url_path
        """),
        {"website_id": website_id}
    ).fetchall()
    
    # Get markdown documents from MongoDB to extract sections
    collection = get_mongo_collection("markdown_documents")
    
    # Build comprehensive documentation structure
    content = f"# {website[1]} Documentation\n\n"
    
    # Process each page
    for page in pages:
        page_id = str(page[0])
        url = page[1]
        title = page[2] or "Untitled"
        url_path = page[3]
        
        # Get MongoDB document for full content and sections
        mongo_doc = collection.find_one({"page_id": page_id})
        
        # Main page entry
        description = ""
        if mongo_doc and mongo_doc.get("metadata", {}).get("ai_processed"):
            description = mongo_doc["metadata"].get("summary", "")
        
        # Add main page
        content += f"- [{title}]({url})"
        if description:
            content += f": {description}"
        content += "\n"
        
        # Extract sections from markdown content
        if mongo_doc and mongo_doc.get("raw_markdown"):
            import re
            markdown_content = mongo_doc.get("raw_markdown", "")
            
            # Find all headers in the markdown
            # Match headers that may contain [​](url) prefix
            headers = re.findall(r'^(#{1,6})\s+(?:\[​\]\([^)]+\))?(.+)$', markdown_content, re.MULTILINE)
            
            # Track header hierarchy
            current_level = 0
            section_stack = []
            
            for header_match in headers:
                level = len(header_match[0])  # Number of # symbols
                header_text = header_match[1].strip()
                
                # Skip the main title (usually H1)
                if level == 1 and header_text == title:
                    continue
                
                # Clean header text first
                # Remove (URL) prefix if present
                clean_header = re.sub(r'^\([^)]+\)\s*', '', header_text).strip()
                clean_header = re.sub(r'\[​\]', '', clean_header).strip()
                
                # Create anchor from clean header text
                anchor = clean_header.lower()
                anchor = re.sub(r'[^\w\s-]', '', anchor)  # Remove special chars
                anchor = re.sub(r'\s+', '-', anchor)  # Replace spaces with dashes
                anchor = re.sub(r'-+', '-', anchor)  # Replace multiple dashes with single
                anchor = anchor.strip('-')  # Remove leading/trailing dashes
                
                # Determine indentation based on header level
                indent = "  " * level
                
                # Add section with proper indentation
                content += f"{indent}- [{clean_header}]({url}#{anchor})"
                
                # Try to find description for this section
                # Look for content after the header
                section_pattern = rf'^#{{{level}}}\s+(?:\[​\]\([^)]+\))?{re.escape(clean_header)}\s*\n+([^#]+?)(?=\n#{{{level},}}|\n\n#{{{level},}}|\Z)'
                section_match = re.search(section_pattern, markdown_content, re.MULTILINE | re.DOTALL)
                if section_match:
                    section_content = section_match.group(1).strip()
                    # Extract first meaningful paragraph
                    paragraphs = section_content.split('\n\n')
                    for para in paragraphs:
                        para = para.strip()
                        # Skip code blocks, copy indicators, empty lines
                        if para and not para.startswith('```') and not para.startswith('Copy') and para != '​':
                            # Clean up the description
                            section_desc = re.sub(r'\s+', ' ', para)  # Normalize whitespace
                            section_desc = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', section_desc)  # Remove markdown links
                            section_desc = re.sub(r'[*_`]', '', section_desc)  # Remove markdown formatting
                            # Limit length but keep it informative
                            if len(section_desc) > 300:
                                section_desc = section_desc[:297] + "..."
                            content += f": {section_desc}"
                            break
                
                content += "\n"
        
        # Add some spacing between pages
        content += "\n"
    
    # Add metadata section
    content += "## Metadata\n\n"
    content += f"- **Domain**: {website[1]}\n"
    content += f"- **Total Pages**: {len(pages)}\n"
    
    # Add page statistics
    processed_count = 0
    unprocessed_pages = []
    for page in pages:
        page_id = str(page[0])
        mongo_doc = collection.find_one({"page_id": page_id})
        if mongo_doc and mongo_doc.get("metadata", {}).get("ai_processed"):
            processed_count += 1
        else:
            unprocessed_pages.append({"id": page_id, "url": page[1], "title": page[2]})
    
    content += f"- **AI Processed Pages**: {processed_count}/{len(pages)}\n"
    content += f"- **Website ID**: {website_id}\n"
    
    # Add generation timestamp
    from datetime import datetime
    content += f"- **Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    
    # Add AI enhancement notice if needed
    if unprocessed_pages:
        content += "\n## AI Enhancement Available\n\n"
        content += f"**{len(unprocessed_pages)} pages** have not been processed with AI enhancement. "
        content += "AI processing adds:\n\n"
        content += "- Detailed summaries for each page and section\n"
        content += "- Semantic categorization and tagging\n"
        content += "- Improved content structure and navigation\n"
        content += "- Enhanced search and discovery capabilities\n"
        content += "\nTo process these pages, use the `/content/{website_id}/process` endpoint with the following page IDs:\n\n"
        content += "```json\n{\n  \"page_ids\": [\n"
        for i, page in enumerate(unprocessed_pages[:5]):  # Show first 5
            content += f'    "{page["id"]}"'
            if i < min(len(unprocessed_pages), 5) - 1:
                content += ","
            content += f'  // {page["title"]}\n'
        if len(unprocessed_pages) > 5:
            content += f"    // ... and {len(unprocessed_pages) - 5} more pages\n"
        content += "  ]\n}\n```"
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'inline; filename="{website[1]}_llms.txt"'
        }
    )


@router.post("/{website_id}/process", response_model=ProcessingStatus)
async def process_pages_with_ai(
    website_id: str,
    request: ProcessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process pages with AI enhancement."""
    # Verify website belongs to user
    website = db.execute(
        text("""
        SELECT id FROM websites 
        WHERE id = :website_id AND user_id = :user_id
        """),
        {"website_id": website_id, "user_id": str(current_user.id)}
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Verify all pages belong to the website
    placeholders = ','.join([f':page_{i}' for i in range(len(request.page_ids))])
    query = f"""
        SELECT COUNT(*) FROM pages 
        WHERE website_id = :website_id AND id IN ({placeholders})
    """
    params = {"website_id": website_id}
    for i, page_id in enumerate(request.page_ids):
        params[f"page_{i}"] = page_id
    
    count = db.execute(text(query), params).fetchone()[0]
    
    if count != len(request.page_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some pages do not belong to this website"
        )
    
    # Queue batch processing task
    task = batch_process_pages_task.apply_async(
        args=[website_id, request.page_ids]
    )
    
    logger.info(f"Queued AI processing for {len(request.page_ids)} pages in website {website_id}")
    
    return ProcessingStatus(
        job_id=task.id,
        status="processing",
        total_pages=len(request.page_ids),
        processed_pages=0,
        failed_pages=0
    )


@router.get("/{website_id}/changes")
async def get_content_changes(
    website_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    since: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent content changes for a website."""
    # Verify website belongs to user
    website = db.execute(
        text("""
        SELECT id FROM websites 
        WHERE id = :website_id AND user_id = :user_id
        """),
        {"website_id": website_id, "user_id": str(current_user.id)}
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Get changes
    query = """
        SELECT pc.id, pc.page_id, p.url, p.title, pc.change_type,
               pc.detected_at, pc.old_hash, pc.new_hash
        FROM page_changes pc
        JOIN pages p ON pc.page_id = p.id
        WHERE p.website_id = :website_id
    """
    params = {"website_id": website_id}
    
    if since:
        query += " AND pc.detected_at > :since"
        params["since"] = since
    
    query += " ORDER BY pc.detected_at DESC LIMIT :limit"
    params["limit"] = limit
    
    changes = db.execute(text(query), params).fetchall()
    
    return {
        "website_id": website_id,
        "changes": [
            {
                "id": str(change[0]),
                "page_id": str(change[1]),
                "url": change[2],
                "title": change[3],
                "change_type": change[4],
                "detected_at": change[5],
                "old_hash": change[6],
                "new_hash": change[7]
            }
            for change in changes
        ]
    }


@router.get("/{website_id}/statistics")
async def get_website_statistics(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content statistics for a website."""
    # Verify website belongs to user
    website = db.execute(
        text("""
        SELECT id, domain, created_at FROM websites 
        WHERE id = :website_id AND user_id = :user_id
        """),
        {"website_id": website_id, "user_id": str(current_user.id)}
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Get page statistics
    stats = db.execute(
        text("""
        SELECT 
            COUNT(*) as total_pages,
            COUNT(DISTINCT url_path) as unique_paths,
            MIN(created_at) as first_crawled,
            MAX(updated_at) as last_updated
        FROM pages
        WHERE website_id = :website_id
        """),
        {"website_id": website_id}
    ).fetchone()
    
    # Get AI processing statistics from MongoDB
    collection = get_mongo_collection("markdown_documents")
    ai_stats = collection.aggregate([
        {"$match": {"website_id": website_id}},
        {"$group": {
            "_id": None,
            "total_processed": {"$sum": 1},
            "ai_processed": {
                "$sum": {"$cond": [{"$eq": ["$metadata.ai_processed", True]}, 1, 0]}
            },
            "avg_quality_score": {"$avg": "$metadata.quality_score"}
        }}
    ])
    
    ai_stats_result = list(ai_stats)
    ai_data = ai_stats_result[0] if ai_stats_result else {}
    
    return {
        "website_id": website_id,
        "domain": website[1],
        "created_at": website[2],
        "statistics": {
            "total_pages": stats[0] or 0,
            "unique_paths": stats[1] or 0,
            "first_crawled": stats[2],
            "last_updated": stats[3],
            "ai_processed_pages": ai_data.get("ai_processed", 0),
            "average_quality_score": ai_data.get("avg_quality_score", 0.0)
        }
    }


@router.get("/{website_id}/docs.zip")
async def download_docs_folder(
    website_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate and download a complete documentation folder structure as a ZIP file."""
    # Verify website belongs to user
    website = db.execute(
        text("""
        SELECT id, domain FROM websites 
        WHERE id = :website_id AND user_id = :user_id
        """),
        {"website_id": website_id, "user_id": str(current_user.id)}
    ).fetchone()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    domain = website[1]
    
    # Get all pages
    pages = db.execute(
        text("""
        SELECT id, url, title, url_path
        FROM pages
        WHERE website_id = :website_id
        ORDER BY url_path
        """),
        {"website_id": website_id}
    ).fetchall()
    
    # Get markdown documents from MongoDB
    collection = get_mongo_collection("markdown_documents")
    
    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Create root index.md with the llms.txt content
        llms_response = await get_llms_txt(website_id, current_user, db)
        zip_file.writestr("index.md", llms_response.body.decode('utf-8'))
        
        # Process each page
        for page in pages:
            page_id = str(page[0])
            url = page[1]
            title = page[2] or "Untitled"
            url_path = page[3]
            
            # Get MongoDB document
            mongo_doc = collection.find_one({"page_id": page_id})
            if not mongo_doc:
                continue
            
            # Parse URL to create folder structure
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.strip('/').split('/') if p]
            
            # Determine file path based on URL structure
            if not path_parts or (len(path_parts) == 1 and path_parts[0] == ''):
                # Root page - skip it as we already have index.md
                continue
            else:
                # Create nested folder structure matching URL
                # For a URL like /environments/browser, create environments/browser.md
                file_name = path_parts[-1] if path_parts else 'index'
                if len(path_parts) > 1:
                    # Nested path
                    folder_path = "/".join(path_parts[:-1])
                    file_path = f"{folder_path}/{file_name}.md"
                else:
                    # Top-level path
                    file_path = f"{file_name}.md"
            
            # Create main page content
            page_content = f"# {title}\n\n"
            page_content += f"**URL**: {url}\n\n"
            
            # Add AI-generated summary if available
            if mongo_doc.get("metadata", {}).get("ai_processed"):
                if summary := mongo_doc["metadata"].get("summary"):
                    page_content += f"## Summary\n\n{summary}\n\n"
            
            # Add table of contents for sections
            raw_markdown = mongo_doc.get("raw_markdown", "")
            if raw_markdown:
                import re
                # Find all headers
                headers = re.findall(r'^(#{1,6})\s+(?:\[​\]\([^)]+\))?(.+)$', raw_markdown, re.MULTILINE)
                
                if headers:
                    page_content += "## Table of Contents\n\n"
                    for header_match in headers:
                        level = len(header_match[0])
                        header_text = header_match[1].strip()
                        
                        # Skip main title
                        if level == 1 and header_text == title:
                            continue
                        
                        # Clean header text
                        clean_header = re.sub(r'\[​\]', '', header_text).strip()
                        
                        # Create anchor
                        anchor = clean_header.lower()
                        anchor = re.sub(r'[^\w\s-]', '', anchor)
                        anchor = re.sub(r'\s+', '-', anchor)
                        anchor = re.sub(r'-+', '-', anchor).strip('-')
                        
                        # Add to TOC with indentation
                        indent = "  " * (level - 1)
                        page_content += f"{indent}- [{clean_header}](#{anchor})\n"
                    
                    page_content += "\n"
                
                # Add the actual content
                page_content += "## Content\n\n"
                # Clean up the markdown content
                clean_content = raw_markdown
                # Remove [​] links
                clean_content = re.sub(r'\[​\]\([^)]+\)', '', clean_content)
                # Remove standalone "Copy" lines
                clean_content = re.sub(r'^Copy\s*$', '', clean_content, flags=re.MULTILINE)
                # Remove multiple blank lines
                clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)
                # Remove trailing whitespace
                clean_content = re.sub(r'[ \t]+$', '', clean_content, flags=re.MULTILINE)
                page_content += clean_content
                
                # Create separate files for major sections
                # Only match the header line, not the content
                section_headers = re.findall(r'^(#{2,3})\s+(?:\[​\]\([^)]+\))?(.+)$', raw_markdown, re.MULTILINE)
                
                for section_match in section_headers:
                    section_level = len(section_match[0])
                    section_title = section_match[1].strip()
                    
                    # Only create separate files for level 2 headers
                    if section_level == 2:
                        # Clean section title
                        # Remove (URL) prefix if present
                        clean_section = re.sub(r'^\([^)]+\)\s*', '', section_title).strip()
                        clean_section = re.sub(r'\[​\]', '', clean_section).strip()
                        
                        # Create section file name (limit length)
                        section_slug = clean_section.lower()
                        section_slug = re.sub(r'[^\w\s-]', '', section_slug)
                        section_slug = re.sub(r'\s+', '-', section_slug)
                        section_slug = re.sub(r'-+', '-', section_slug).strip('-')
                        # Limit to first 50 characters
                        if len(section_slug) > 50:
                            section_slug = section_slug[:50].rstrip('-')
                        
                        # Create section file path in the same directory as the parent
                        if len(path_parts) > 1:
                            # Nested path - put section in same folder
                            folder_path = "/".join(path_parts[:-1])
                            section_path = f"{folder_path}/{section_slug}.md"
                        elif len(path_parts) == 1:
                            # Top-level page - put sections in subfolder
                            section_path = f"{path_parts[0]}/{section_slug}.md"
                        else:
                            # Root page sections
                            section_path = f"sections/{section_slug}.md"
                        
                        # Find section content
                        section_content_pattern = rf'^#{{{section_level}}}\s+(?:\[​\]\([^)]+\))?{re.escape(section_title)}\s*\n(.*?)(?=^#{{{1,section_level}}}\s|\Z)'
                        section_content_match = re.search(section_content_pattern, raw_markdown, re.MULTILINE | re.DOTALL)
                        
                        if section_content_match:
                            section_content = f"# {clean_section}\n\n"
                            section_content += f"**Parent**: [{title}](../{path_parts[-1] if path_parts else 'home'}.md)\n\n"
                            
                            # Get and clean the section content
                            content_body = section_content_match.group(1).strip()
                            # Remove [​] links
                            content_body = re.sub(r'\[​\]\([^)]+\)', '', content_body)
                            # Remove standalone "Copy" lines
                            content_body = re.sub(r'^Copy\s*$', '', content_body, flags=re.MULTILINE)
                            # Remove multiple blank lines
                            content_body = re.sub(r'\n{3,}', '\n\n', content_body)
                            # Remove trailing whitespace
                            content_body = re.sub(r'[ \t]+$', '', content_body, flags=re.MULTILINE)
                            
                            section_content += content_body
                            
                            # Add to zip
                            zip_file.writestr(section_path, section_content)
            
            # Add the main page to zip
            zip_file.writestr(file_path, page_content)
        
        # Create a README.md
        readme_content = f"""# {domain} Documentation

This documentation was generated from the website {domain} using Lapis Spider.

## Structure

- `index.md` - Main documentation index (llms.txt format)
- Each page from the website has its own markdown file
- Major sections (H2 headers) are extracted into separate files in subdirectories

## Navigation

Start with `index.md` to see the complete documentation structure.

## Metadata

- **Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Total Pages**: {len(pages)}
- **Website ID**: {website_id}
"""
        zip_file.writestr(f"{domain}/README.md", readme_content)
    
    # Prepare the ZIP file for download
    zip_buffer.seek(0)
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{domain}_docs.zip"'
        }
    )