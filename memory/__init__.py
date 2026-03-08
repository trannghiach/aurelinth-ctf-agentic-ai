# Aurelinth - Database connections

from pymongo import MongoClient
from redis import Redis
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_mongo():
    """Get a MongoDB client."""
    client = MongoClient(os.getenv("MONGO_URL"))
    return client["aurelinth"]

def get_redis():
    """Get a Redis client."""
    return Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

def get_qdrant():
    """Get a Qdrant client."""
    return QdrantClient(url=os.getenv("QDRANT_URL"))