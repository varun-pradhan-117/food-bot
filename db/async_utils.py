import os
from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "grocerbot"
COLLECTION_NAME = "pantry_sheets"

# init client
mongo_client = AsyncMongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# helpers
async def get_user(user_id: str):
    return await collection.find_one({"user_id": user_id})

async def save_user(user_id: str, sheet_url: str = None, preferences: dict = None):
    update = {}
    if sheet_url:
        update["sheet_url"] = sheet_url
    if preferences:
        update["preferences"] = preferences

    return await collection.update_one(
        {"user_id": user_id},
        {"$set": update},
        upsert=True
    )