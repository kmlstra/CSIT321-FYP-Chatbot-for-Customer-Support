from motor.motor_asyncio import AsyncIOMotorClient
from api.config import Settings

settings = Settings()

class MongoDB:
    client: AsyncIOMotorClient = None

    @classmethod
    async def connect_db(cls):
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        return cls.client[settings.MONGODB_DB]

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close() 