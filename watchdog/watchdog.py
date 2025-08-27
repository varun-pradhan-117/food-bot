import time
import hashlib
from misc_utils.google_utils import fetch_sheet_as_df
from db.sync_utils import (
    get_all_users,
    upsert_inventory,
    get_user_sheet_hash,
    upsert_user_sheet
)
import pandas as pd

POLL_INTERVAL = 60  # seconds

def df_hash(df):
    """Compute a hash of the DataFrame contents"""
    return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()

def sync_sheet_for_user(user):
    user_id = user.get("user_id")
    sheet_url = user.get("sheet_url")
    if not user_id or not sheet_url:
        return

    df = fetch_sheet_as_df(sheet_url)
    if df.empty:
        print(f"[SYNC] User {user_id}: sheet empty or failed to fetch.")
        return

    current_hash = df_hash(df)
    last_hash = get_user_sheet_hash(user_id)

    if last_hash == current_hash:
        print(f"[SYNC] User {user_id}: no changes detected, skipping.")
        return

    # Upsert inventory rows
    for _, row in df.iterrows():
        item_key = row.get("item")
        if item_key:
            upsert_inventory(user_id, item_key, row.to_dict())

    # Update hash in Mongo
    upsert_user_sheet(user_id, sheet_url, current_hash)
    print(f"[SYNC] User {user_id}: {len(df)} records synced.")

def run_sync():
    """Run sync for all users once"""
    users = get_all_users()
    for user in users:
        sync_sheet_for_user(user)
        
if __name__ == "__main__":
    users=get_all_users()
    for user in users:
        sync_sheet_for_user(user)
    
