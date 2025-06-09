#!/usr/bin/env python3
"""Database setup script."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database import init_db, check_db_connection
from src.database.mongodb import check_mongodb_connection_sync
from src.database.redis import check_redis_connection
from src.utils.logging import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Set up the database."""
    logger.info("Starting database setup...")
    
    # Check connections
    logger.info("Checking database connections...")
    
    if not check_db_connection():
        logger.error("PostgreSQL connection failed")
        sys.exit(1)
    logger.info("PostgreSQL connection: OK")
    
    if not check_mongodb_connection_sync():
        logger.error("MongoDB connection failed")
        sys.exit(1)
    logger.info("MongoDB connection: OK")
    
    if not check_redis_connection():
        logger.error("Redis connection failed")
        sys.exit(1)
    logger.info("Redis connection: OK")
    
    # Initialize PostgreSQL
    try:
        init_db()
        logger.info("PostgreSQL tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        sys.exit(1)
    
    logger.info("Database setup completed successfully!")


if __name__ == "__main__":
    main()