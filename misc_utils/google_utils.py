import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

load_dotenv()
GOOGLE_SERVICE_CREDENTIALS= os.getenv("GOOGLE_SERVICE_CREDENTIALS")


SECRETS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..",GOOGLE_SERVICE_CREDENTIALS)
)

# Setup gspread client
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SECRETS_FILE, scope)
client = gspread.authorize(creds)


async def read_sheet_to_string(sheet_url: str) -> str:
    """
    Reads a Google Sheet with columns 'Item' and 'Quantity' and returns a bullet-point string.
    
    Args:
        sheet_url (str): Full URL of the Google Sheet.
    
    Returns:
        str: Bullet-point string of items, e.g.,
            - Milk (2)
            - Eggs
            - Butter (250g)
    """
    
    
    # Extract the sheet ID from URL
    try:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    except IndexError:
        return "- Invalid sheet URL."
    
    try:
        sheet = client.open_by_key(sheet_id).sheet1  # assuming first sheet
        rows = sheet.get_all_records()  # list of dicts
    except Exception:
        return "- Could not read the sheet."

    if not rows:
        return "- Sheet is empty."

    lines = []
    for row in rows:
        item = row.get("Item") or "Unknown"
        quantity = row.get("Quantity")
        line = f"- {item}" + (f" ({quantity})" if quantity else "")
        lines.append(line)

    return "\n".join(lines)

# --- Sync function for listener ---
def fetch_sheet_as_df(sheet_url: str, sheet_name: str = "Sheet1") -> pd.DataFrame:
    """
    Fetches a Google Sheet and returns a DataFrame with normalized column names.
    """
    # Extract the sheet ID from URL
    try:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    except IndexError:
        return "- Invalid sheet URL."
    try:
        sheet = client.open_by_key(sheet_id).sheet1  # assuming first sheet
        data = sheet.get_all_records()  # list of dicts
    except Exception:
        return "- Could not read the sheet."
    try:
        df = pd.DataFrame(data)
        df.columns = [col.strip().lower() for col in df.columns]
        return df
    except Exception as e:
        print(f"[ERROR] Could not fetch sheet: {e}")
        return pd.DataFrame()  # empty DF if fail
