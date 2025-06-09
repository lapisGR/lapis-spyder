"""Database module for Lapis Spider."""

from .postgres import Base, get_db, init_db
from .mongodb import get_mongodb, get_mongo_collection
from .redis import get_redis, RedisCache

__all__ = [
    "Base",
    "get_db",
    "init_db",
    "get_mongodb",
    "get_mongo_collection",
    "get_redis",
    "RedisCache",
]