"""MongoDB connection and operations."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from src.config import settings

# Synchronous client for Celery tasks
sync_client: Optional[MongoClient] = None
sync_db = None

# Asynchronous client for FastAPI
async_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
async_db = None


def get_sync_mongodb():
    """Get synchronous MongoDB client."""
    global sync_client, sync_db
    
    if sync_client is None:
        sync_client = MongoClient(
            settings.mongodb_connection_url,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            tlsAllowInvalidCertificates=True,  # For macOS SSL certificate issues
        )
        sync_db = sync_client[settings.mongodb_db]
    
    return sync_db


def get_async_mongodb():
    """Get asynchronous MongoDB client."""
    global async_client, async_db
    
    if async_client is None:
        async_client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.mongodb_connection_url,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            tlsAllowInvalidCertificates=True,  # For macOS SSL certificate issues
        )
        async_db = async_client[settings.mongodb_db]
    
    return async_db


def get_mongo_collection(collection_name: str, async_mode: bool = False):
    """Get MongoDB collection."""
    if async_mode:
        db = get_async_mongodb()
    else:
        db = get_sync_mongodb()
    
    return db[collection_name]


async def check_mongodb_connection():
    """Check if MongoDB is accessible."""
    try:
        db = get_async_mongodb()
        # Get the client from the database and ping
        await db.client.admin.command("ping")
        return True
    except Exception:
        return False


def check_mongodb_connection_sync():
    """Check if MongoDB is accessible (sync version)."""
    try:
        db = get_sync_mongodb()
        # Get the client from the database and ping
        db.client.admin.command("ping")
        return True
    except Exception:
        return False


@asynccontextmanager
async def get_mongodb_session():
    """Get MongoDB session for transactions."""
    client = get_async_mongodb()
    async with await client.start_session() as session:
        async with session.start_transaction():
            yield session


def close_mongodb_connections():
    """Close all MongoDB connections."""
    global sync_client, async_client, sync_db, async_db
    
    if sync_client:
        sync_client.close()
        sync_client = None
        sync_db = None
    
    if async_client:
        async_client.close()
        async_client = None
        async_db = None


# MongoDB operations helpers
class MongoDBOperations:
    """Common MongoDB operations."""
    
    @staticmethod
    async def insert_html(crawl_job_id: str, page_id: str, url: str, 
                         html: str, headers: dict, status_code: int):
        """Insert raw HTML document."""
        collection = get_mongo_collection("raw_html", async_mode=True)
        
        document = {
            "crawl_job_id": crawl_job_id,
            "page_id": page_id,
            "url": url,
            "raw_html": html,
            "headers": headers,
            "status_code": status_code,
            "crawled_at": asyncio.get_event_loop().time(),
            "content_type": headers.get("content-type", "text/html"),
            "size_bytes": len(html.encode("utf-8"))
        }
        
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_html(page_id: str):
        """Get raw HTML by page ID."""
        collection = get_mongo_collection("raw_html", async_mode=True)
        return await collection.find_one({"page_id": page_id})
    
    @staticmethod
    async def insert_markdown(page_id: str, website_id: str, url: str,
                            raw_markdown: str, structured_markdown: str = None,
                            metadata: dict = None, prompt_used: str = None):
        """Insert markdown document."""
        collection = get_mongo_collection("markdown_documents", async_mode=True)
        
        # Check if document exists
        existing = await collection.find_one({"page_id": page_id})
        version = 1 if not existing else existing.get("version", 0) + 1
        
        document = {
            "page_id": page_id,
            "website_id": website_id,
            "url": url,
            "raw_markdown": raw_markdown,
            "structured_markdown": structured_markdown,
            "metadata": metadata or {},
            "gemini_prompt_used": prompt_used,
            "processed_at": asyncio.get_event_loop().time(),
            "version": version
        }
        
        if existing:
            result = await collection.replace_one(
                {"page_id": page_id},
                document
            )
            return str(existing["_id"])
        else:
            result = await collection.insert_one(document)
            return str(result.inserted_id)
    
    @staticmethod
    async def get_markdown(page_id: str):
        """Get markdown document by page ID."""
        collection = get_mongo_collection("markdown_documents", async_mode=True)
        return await collection.find_one({"page_id": page_id})
    
    @staticmethod
    async def bulk_insert_html(documents: list):
        """Bulk insert HTML documents."""
        collection = get_mongo_collection("raw_html", async_mode=True)
        
        if not documents:
            return []
        
        result = await collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    @staticmethod
    def insert_markdown_sync(page_id: str, website_id: str, url: str,
                           raw_markdown: str, structured_markdown: str = None,
                           metadata: dict = None, prompt_used: str = None):
        """Insert markdown document (synchronous version)."""
        collection = get_mongo_collection("markdown_documents", async_mode=False)
        
        # Check if document exists
        existing = collection.find_one({"page_id": page_id})
        version = 1 if not existing else existing.get("version", 0) + 1
        
        document = {
            "page_id": page_id,
            "website_id": website_id,
            "url": url,
            "raw_markdown": raw_markdown,
            "structured_markdown": structured_markdown,
            "metadata": metadata or {},
            "gemini_prompt_used": prompt_used,
            "processed_at": datetime.utcnow(),
            "version": version
        }
        
        if existing:
            result = collection.replace_one(
                {"page_id": page_id},
                document
            )
            return str(existing["_id"])
        else:
            result = collection.insert_one(document)
            return str(result.inserted_id)
    
    @staticmethod
    def insert_html_sync(crawl_job_id: str, page_id: str, url: str, 
                        html: str, headers: dict, status_code: int):
        """Insert raw HTML document (synchronous version)."""
        collection = get_mongo_collection("raw_html", async_mode=False)
        
        document = {
            "crawl_job_id": crawl_job_id,
            "page_id": page_id,
            "url": url,
            "raw_html": html,
            "headers": headers,
            "status_code": status_code,
            "crawled_at": datetime.utcnow(),
            "content_type": headers.get("content-type", "text/html"),
            "size_bytes": len(html.encode("utf-8"))
        }
        
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    def get_markdown_sync(page_id: str):
        """Get markdown document by page ID (synchronous version)."""
        collection = get_mongo_collection("markdown_documents", async_mode=False)
        return collection.find_one({"page_id": page_id})