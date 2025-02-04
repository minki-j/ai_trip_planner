import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set in the .env file")
main_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
main_db = main_client.get_database("test")

async def ping_mongodb():
    try:
        await main_client.admin.command("ping")
        print("Successfully connected to main")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise e
