from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

# ---------------------------------------------------------------------------
# MongoDB async client (Motor)
# ---------------------------------------------------------------------------
client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Called on app startup — creates the Motor client and selects the DB."""
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Extract DB name from the connection string, defaulting to "edusphere_db"
    db_name = settings.MONGODB_URL.split("/")[-1].split("?")[0] or "edusphere_db"
    db = client[db_name]
    print(f"✅  Connected to MongoDB — database: {db_name}")


async def close_db():
    """Called on app shutdown — closes the Motor client."""
    global client
    if client:
        client.close()
        print("🔌  MongoDB connection closed.")


def get_db():
    """Dependency injector that returns the active database handle."""
    return db
