from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "")

client = None
database = None

async def connect_db():
    global client, database
    try:
        client = AsyncIOMotorClient(DB_URL)
        # Extract database name from URL or use default
        if "/" in DB_URL:
            db_name = DB_URL.split("/")[-1].split("?")[0]
        else:
            db_name = "hopefund"
        database = client[db_name]
        print(f"Database connected with {client.address}")
    except Exception as error:
        print(f"Database connection error: {error}")
        raise

async def close_db():
    global client
    if client:
        client.close()
        
def get_database():
    return database

