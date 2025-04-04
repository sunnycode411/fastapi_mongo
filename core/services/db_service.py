from motor.motor_asyncio import AsyncIOMotorClient

from core.settings import DATABASE_URI


db_client: AsyncIOMotorClient = None


async def init_db() -> AsyncIOMotorClient:
    """Get the database connection."""
    global db_client
    if not db_client:
        db_client = AsyncIOMotorClient(DATABASE_URI)
        return db_client


async def close_db() -> None:
    """Close the database connection."""
    global db_client
    if db_client:
        db_client.close()
        db_client = None


async def db_status() -> bool:
    """Check the status of the database connection."""
    global db_client
    if db_client:
        return True
    return False
