import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "grocerbot"
PANTRY_COLLECTION = "pantry_sheets"
INVENTORY_COLLECTION = "inventory"

# --- Mongo client ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
pantry_col = db[PANTRY_COLLECTION]
inventory_col = db[INVENTORY_COLLECTION]

# --- Pantry helpers ---
def get_all_users():
    """Return all users with pantry sheets"""
    return list(pantry_col.find())

def upsert_user(user_id: str, sheet_url: str = None, sheet_hash: str = None, preferences: dict = None):
    """Save or update a user's sheet URL, hash, and preferences"""
    update = {}
    if sheet_url:
        update["sheet_url"] = sheet_url
    if sheet_hash:
        update["last_hash"] = sheet_hash
    if preferences:
        update["preferences"] = preferences

    pantry_col.update_one(
        {"user_id": user_id},
        {"$set": update},
        upsert=True
    )

def get_user(user_id: str):
    """Fetch a user's document"""
    return pantry_col.find_one({"user_id": user_id})

def get_user_sheet_hash(user_id: str):
    """Retrieve the last hash for a user's sheet"""
    doc = pantry_col.find_one({"user_id": user_id})
    if doc:
        return doc.get("last_hash")
    return None

# --- Inventory helpers ---
def upsert_inventory(user_id: str, item_key: str, record: dict):
    """Upsert a single inventory record for a user"""
    record["user_id"] = user_id
    inventory_col.update_one(
        {"user_id": user_id, "item": item_key},
        {"$set": record},
        upsert=True
    )

def get_inventory_for_user(user_id: str):
    """Fetch all inventory records for a user"""
    return list(inventory_col.find({"user_id": user_id}).sort("item", ASCENDING))

def get_item(user_id: str, item_key: str):
    """Fetch a specific inventory item for a user"""
    return inventory_col.find_one({"user_id": user_id, "item": item_key})

def delete_item(user_id: str, item_key: str):
    """Delete a specific inventory item for a user"""
    return inventory_col.delete_one({"user_id": user_id, "item": item_key})
