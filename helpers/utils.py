import gspread
from oauth2client.service_account import ServiceAccountCredentials


secrets_file="secrets/grocerbot-469403-e0151322280c.json"

def discounts_to_string(all_items, max_items=20):
    """
    Convert scraped discounts into a simple bullet-point list string.

    Args:
        all_items (List[Dict[str, Any]]): List of discounts from scrape_aanbiedingen.
        max_items (int, optional): Max number of items to include. Defaults to 20.

    Returns:
        str: Bullet-point formatted string summarizing the discounts.
    """
    if not all_items:
        return "- No discounts available today."

    lines = []
    for item in all_items:
        name = item.get("name") or "Unknown"
        promo = item.get("promotion") or "No promo"
        discounted = item.get("discounted_price") or "N/A"
        original = item.get("original_price") or "N/A"
        extra = item.get("extra_info") or ""

        line = f"- {name}{f' ({extra})' if extra else ''} | {promo} | {discounted} (was {original})"
        lines.append(line)


    return "\n".join(lines)


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
    # Setup gspread client
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(secrets_file, scope)
    client = gspread.authorize(creds)
    
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