import time
import random
import os
import json
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options



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
    

def scrape_aanbiedingen(url="https://www.plus.nl/aanbiedingen", out_dir="data"):
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
    out_file = os.path.join(out_dir, f"aanbiedingen_{today}.json")

    # If today's file already exists, skip scraping
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            all_items = json.load(f)
        print(f"Loaded existing file: {out_file}")
        return out_file, all_items
    
    # If older files exist, delete them
    for fname in os.listdir(out_dir):
        if fname.startswith("aanbiedingen_") and fname.endswith(".json"):
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
    # Save as JSON
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_items)} items to {out_file}")
    return out_file, all_items