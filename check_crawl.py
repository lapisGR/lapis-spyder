from src.database.postgres import SessionLocal
from src.database.mongodb import get_mongo_collection
from sqlalchemy import text

db = SessionLocal()
website_id = 'd41d8f44-4e19-4064-b4b7-218490cbcb77'

# Check crawl status
job = db.execute(
    text("SELECT status, pages_crawled FROM crawl_jobs WHERE website_id = :website_id ORDER BY created_at DESC LIMIT 1"),
    {"website_id": website_id}
).fetchone()

# Check pages
pages_count = db.execute(
    text("SELECT COUNT(*) FROM pages WHERE website_id = :website_id"),
    {"website_id": website_id}
).fetchone()[0]

collection = get_mongo_collection('markdown_documents')
docs_count = collection.count_documents({'website_id': website_id})

print(f'Crawl Status: {job[0] if job else "No job"}')
print(f'Pages in DB: {pages_count}')
print(f'Markdown docs: {docs_count}')

# Check for code blocks
if docs_count > 0:
    docs_with_code = 0
    total_code_blocks = 0
    
    for doc in collection.find({'website_id': website_id}):
        content = doc.get('raw_markdown', '')
        code_blocks = content.count('```') // 2
        if code_blocks > 0:
            docs_with_code += 1
            total_code_blocks += code_blocks
            if docs_with_code <= 5:
                print(f'  {doc["url"]}: {code_blocks} code blocks')
    
    print(f'\nTotal: {docs_with_code} docs with code blocks, {total_code_blocks} total code blocks')

db.close()
