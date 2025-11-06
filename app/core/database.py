from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            # Test the connection
            await cls.client.admin.command('ping')
            cls.db = cls.client[settings.DATABASE_NAME]
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {str(e)}")
            raise RuntimeError("Failed to connect to MongoDB. Please ensure MongoDB is running.")

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed") 