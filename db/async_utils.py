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
async def get_user_sheet(user_id: str):
    return await collection.find_one({"user_id": user_id})

async def save_user_sheet(user_id: str, sheet_url: str):
    return await collection.update_one(
        {"user_id": user_id},
        {"$set": {"sheet_url": sheet_url}},
        upsert=True
    )
    
