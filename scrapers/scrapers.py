import time
import random
import os
import json
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


maps={
    "plus":"plus",
    "albert heijn":"ah",
    "dekamarkt":"dm"
}

def get_html(url="https://www.plus.nl/aanbiedingen"):
    """
    Get HTML content from the given URL using Selenium with Firefox.

    This function sets up a Firefox WebDriver, navigates to the specified URL,
    waits for the page to load, and returns the HTML content.

    Args:
        url (str, optional): URL of page to be fetched. Defaults to "https://www.plus.nl/aanbiedingen".

    Returns:
        str: The HTML content of the page.
    """
    # Setup Firefox options
    options = Options()
    options.add_argument("--start-maximized")  # Normal browser mode

    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(30)

    # Navigate to aanbiedingen page
    driver.get(url)

    # Wait a bit to let JS load
    time.sleep(random.uniform(3, 6))

    # Mimic simple scrolling
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
    time.sleep(random.uniform(2, 4))
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(random.uniform(1, 2))

    # Get the HTML
    html = driver.page_source
    driver.quit()
    return html
    
def save_offers(all_items,out_file):
    # Save as JSON
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_items)} items to {out_file}")
    
def scrape_plus(url="https://www.plus.nl/aanbiedingen", out_dir="data"):
    """
    Scrape PLUS aanbiedingen page and save the items to a JSON file.

    Args:
        url (str, optional): URL to PLUS aanbiedingen. Defaults to "https://www.plus.nl/aanbiedingen".
        out_dir (str, optional): Directory for storing the day's discounts. Defaults to "data".

    Returns:
        str: Path to the saved JSON file with today's discounts.
        Optional[List[Dict[str, Any]]]: List of scraped items if successful.
    """
    # Make sure output dir exists
    os.makedirs(out_dir, exist_ok=True)

    # Generate today's filename
    today = datetime.now().strftime("%Y-%m-%d")
    out_file = os.path.join(out_dir, f"plus_{today}.json")

    # If today's file already exists, skip scraping
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            all_items = json.load(f)
        print(f"Loaded existing file: {out_file}")
        return out_file, all_items
    
    # If older files exist, delete them
    for fname in os.listdir(out_dir):
        if fname.startswith("plus_") and fname.endswith(".json"):
            os.remove(os.path.join(out_dir, fname))
            print(f"Deleted old file: {fname}")
    
    # Get HTML content
    html= get_html(url)
    soup = BeautifulSoup(html, "html.parser")

    main_list=soup.select("div.list.list-group.promotions-category-list")
    if not main_list:
        print("Promotions list not found.")
        return out_file, []

    containers=main_list[0].select("div[data-container].plp-results-wrapper")
    # Exclude the first container
    containers=containers[1:]
    # Parse items in each container
    all_items = []
    for container in containers[:-3]: #Exclude last 3 containers as they are for household items
        links=container.select("a[data-link]")
        hrefs=[link["href"] for link in links]
        items=container.select("div[data-container].list-item-content-center")
        for item in items:
            # Promotion
            promo_tag = item.select_one('.promo-offer-label span')
            promotion = promo_tag.get_text(strip=True) if promo_tag else None

            # Name and additional info
            name_tag = item.select_one('.plp-item-name span')
            name = name_tag.get_text(strip=True) if name_tag else None

            # Extra info (per 500g, per 1000 gram, etc.)
            extra_info_tag = item.select_one('.plp-item-complementary .multiline-truncation-text-1 span.OSFillParent')
            extra_info = extra_info_tag.get_text(strip=True) if extra_info_tag else None

            # Discounted price
            price_integer_tag = item.select_one('.product-header-price-integer span')
            price_decimals_tag = item.select_one('.product-header-price-decimals span')
            if price_integer_tag and price_decimals_tag:
                discounted_price = f"{price_integer_tag.get_text(strip=True)}{price_decimals_tag.get_text(strip=True)}"
            else:
                discounted_price = None

            # Original price
            previous_price_tag = item.select_one('.product-header-price-previous span')
            original_price = previous_price_tag.get_text(strip=True) if previous_price_tag else None
            # Item data structure
            item_data = {
                "name": name,
                "extra_info": extra_info,
                "promotion": promotion,
                "discounted_price": discounted_price,
                "original_price": original_price,
                "href": hrefs[0] if hrefs else None
            }
            all_items.append(item_data)
            #print(f"Name: {name}, Info: {extra_info}, Promotion: {promotion}, Discounted Price: {discounted_price}, Original Price: {original_price}")
    save_offers(all_items,out_file)
    return out_file, all_items


def scrape_ah(url="https://www.ah.nl/bonus", out_dir="data"):
    """
    Scrape AH bonus page and save the items to a JSON file.

    Args:
        url (str, optional): URL to AH bonus page.
        out_dir (str, optional): Directory for storing the day's discounts. Defaults to "data".

    Returns:
        str: Path to the saved JSON file with today's discounts.
        Optional[List[Dict[str, Any]]]: List of scraped items if successful.
    """
    # Make sure output dir exists
    os.makedirs(out_dir, exist_ok=True)

    # Generate today's filename
    today = datetime.now().strftime("%Y-%m-%d")
    out_file = os.path.join(out_dir, f"ah_{today}.json")

    # If today's file already exists, skip scraping
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            all_items = json.load(f)
        print(f"Loaded existing file: {out_file}")
        return out_file, all_items
    
    # If older files exist, delete them
    for fname in os.listdir(out_dir):
        if fname.startswith("ah_") and fname.endswith(".json"):
            os.remove(os.path.join(out_dir, fname))
            print(f"Deleted old file: {fname}")
    
    # Get HTML content
    html= get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    
    categories=soup.select("section.area-lane_root__If70y")
    ct=0
    for item in categories:
        ct+=1
        id=item.get("id")
        if id=="drogisterij":
            break
    categories=categories[:ct-1]
    all_items=[]
    for cat in categories:
        items = cat.select('a[data-testhook="promotion-card"]')
        for card in items:
            name_tag = card.select_one('[data-testhook="promotion-card-title"] span')
            name = name_tag.get_text(strip=True) if name_tag else None

            # Extra info (optional description under the title)
            extra_info_tag = card.select_one('[data-testhook="card-description"] span')
            extra_info = extra_info_tag.get_text(strip=True) if extra_info_tag else None

            # Promotion (e.g. "2 voor 2.99", "€1 korting")
            promo_tag = card.select_one('[data-testhook="promotion-labels"] div[aria-label]')
            promotion = promo_tag["aria-label"] if promo_tag else None

            # Discounted and original price
            price_container = card.select_one('[data-testhook="price"]')
            discounted_price = price_container.get("data-testpricenow") if price_container else None
            original_price = price_container.get("data-testpricewas") if price_container else None

            # Link
            href = card.get("href")

            item_data = {
                "name": name,
                "extra_info": extra_info,
                "promotion": promotion,
                "discounted_price": discounted_price,
                "original_price": original_price,
                "href": href
            }
            all_items.append(item_data)
    save_offers(all_items,out_file)
    return out_file,all_items


def scrape_dm(url="https://www.dekamarkt.nl/aanbiedingen", out_dir="data"):
    """
    Scrape dekamarkt discount page and save the items to a JSON file.

    Args:
        url (str, optional): URL to dekamarkt page.
        out_dir (str, optional): Directory for storing the day's discounts. Defaults to "data".

    Returns:
        str: Path to the saved JSON file with today's discounts.
        Optional[List[Dict[str, Any]]]: List of scraped items if successful.
    """
    # Make sure output dir exists
    os.makedirs(out_dir, exist_ok=True)

    # Generate today's filename
    today = datetime.now().strftime("%Y-%m-%d")
    out_file = os.path.join(out_dir, f"dm_{today}.json")

    # If today's file already exists, skip scraping
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            all_items = json.load(f)
        print(f"Loaded existing file: {out_file}")
        return out_file, all_items
    
    # If older files exist, delete them
    for fname in os.listdir(out_dir):
        if fname.startswith("dm_") and fname.endswith(".json"):
            os.remove(os.path.join(out_dir, fname))
            print(f"Deleted old file: {fname}")
            
    # Get HTML content
    html= get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    
    categories=soup.select("section.offers__department")
    ct=0
    titles=[]
    for cat in categories:
        title=cat.select("h3")[0].get_text(strip=True)
        
        print(title)
        if "Drogisterij" in title:
            break
        titles.append(title)
        ct+=1
        
    all_items=[]
    for cat in categories[:ct]:
        items=cat.select("div.product__card--content")
        for card in items:
            # Name
            name_tag = card.select_one("p.title")
            name = name_tag.get_text(strip=True) if name_tag else None

            # Extra info
            extra_info_tag = card.select_one("span.addition")
            extra_info = extra_info_tag.get_text(strip=True) if extra_info_tag else None

            # Promotion (chip text like "130 GRAM 3,49")
            promo_tag = card.select_one("span.chip")
            promotion = promo_tag.get_text(strip=True) if promo_tag else None

            # Discounted price
            price_offer_int = card.select_one("div.prices__offer span")
            price_offer_dec = card.select_one("div.prices__offer small span")
            if price_offer_int and price_offer_dec:
                discounted_price = f"{price_offer_int.get_text(strip=True)}{price_offer_dec.get_text(strip=True)}"
            else:
                discounted_price = None

            # Original price
            original_price_tag = card.select_one("span.regular.regular-strike")
            original_price = original_price_tag.get_text(strip=True) if original_price_tag else None

            item_data = {
                "name": name,
                "extra_info": extra_info,
                "promotion": promotion,
                "discounted_price": discounted_price,
                "original_price": original_price,
                "href": None  # this format doesn't have an <a> wrapper
            }
            all_items.append(item_data)
    save_offers(all_items,out_file)
    return out_file,all_items