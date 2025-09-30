import time
import random
import os
import json
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from transformers import MarianMTModel, MarianTokenizer

# Load translation model once
model_name = "Helsinki-NLP/opus-mt-nl-en"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

maps={
    "plus":"plus",
    "albert heijn":"ah",
    "dekamarkt":"dm"
}

url_maps = {
    "plus": "https://www.plus.nl/aanbiedingen",
    "ah": "https://www.ah.nl/bonus",
    "dm": "https://www.dekamarkt.nl/aanbiedingen",
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
    

def translate_name(name: str) -> str:
    """Translate a single product name from NL -> EN"""
    if not name:
        return None
    inputs = tokenizer([name], return_tensors="pt", padding=True, truncation=True)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

# ---------------------
# Store-specific parsers
# ---------------------

def parse_plus(soup: BeautifulSoup):
    all_items = []
    main_list = soup.select("div.list.list-group.promotions-category-list")
    if not main_list:
        return all_items
    containers = main_list[0].select("div[data-container].plp-results-wrapper")[1:-3]
    for container in containers:
        links = container.select("a[data-link]")
        hrefs = [link["href"] for link in links]
        items = container.select("div[data-container].list-item-content-center")
        for item in items:
            name_tag = item.select_one('.plp-item-name span')
            name = name_tag.get_text(strip=True) if name_tag else None
            translated = translate_name(name)
            extra_info_tag = item.select_one('.plp-item-complementary .multiline-truncation-text-1 span.OSFillParent')
            extra_info = extra_info_tag.get_text(strip=True) if extra_info_tag else None
            promo_tag = item.select_one('.promo-offer-label span')
            promotion = promo_tag.get_text(strip=True) if promo_tag else None
            price_int = item.select_one('.product-header-price-integer span')
            price_dec = item.select_one('.product-header-price-decimals span')
            discounted = f"{price_int.get_text(strip=True)}{price_dec.get_text(strip=True)}" if price_int and price_dec else None
            original_price_tag = item.select_one('.product-header-price-previous span')
            original = original_price_tag.get_text(strip=True) if original_price_tag else None
            all_items.append({
                "name": name,
                "name_translated": translated,
                "extra_info": extra_info,
                "promotion": promotion,
                "discounted_price": discounted,
                "original_price": original,
                "href": hrefs[0] if hrefs else None
            })
    return all_items

def parse_ah(soup: BeautifulSoup):
    all_items = []
    categories = soup.select("section.area-lane_root__If70y")
    cutoff = next((i for i, c in enumerate(categories) if c.get("id") == "drogisterij"), len(categories))
    for cat in categories[:cutoff]:
        for card in cat.select('a[data-testhook="promotion-card"]'):
            name_tag = card.select_one('[data-testhook="promotion-card-title"] span')
            name = name_tag.get_text(strip=True) if name_tag else None
            translated = translate_name(name)
            extra_info_tag = card.select_one('[data-testhook="card-description"] span')
            extra_info = extra_info_tag.get_text(strip=True) if extra_info_tag else None
            promo_tag = card.select_one('[data-testhook="promotion-labels"] div[aria-label]')
            promotion = promo_tag["aria-label"] if promo_tag else None
            price_container = card.select_one('[data-testhook="price"]')
            discounted = price_container.get("data-testpricenow") if price_container else None
            original = price_container.get("data-testpricewas") if price_container else None
            href = card.get("href")
            all_items.append({
                "name": name,
                "name_translated": translated,
                "extra_info": extra_info,
                "promotion": promotion,
                "discounted_price": discounted,
                "original_price": original,
                "href": href
            })
    return all_items

def parse_dm(soup: BeautifulSoup):
    all_items = []
    categories = soup.select("section.offers__department")
    cutoff = next((i for i, c in enumerate(categories) if "Snoep" in c.get_text()), len(categories))
    for cat in categories[:cutoff]:
        if "Dranken" in cat.get_text():
            continue
        for card in cat.select("div.product__card--content"):
            name_tag = card.select_one("p.title")
            name = name_tag.get_text(strip=True) if name_tag else None
            translated = translate_name(name)
            if '/' in translated:
                translated = translated.split('/')[0].strip()
            extra_info_tag = card.select_one("span.addition")
            extra_info = extra_info_tag.get_text(strip=True) if extra_info_tag else None
            promo_tag = card.select_one("span.chip")
            promotion = promo_tag.get_text(strip=True) if promo_tag else None
            price_int = card.select_one("div.prices__offer span")
            price_dec = card.select_one("div.prices__offer small span")
            discounted = f"{price_int.get_text(strip=True)}{price_dec.get_text(strip=True)}" if price_int and price_dec else None
            original_price_tag = card.select_one("span.regular.regular-strike")
            original = original_price_tag.get_text(strip=True) if original_price_tag else None
            all_items.append({
                "name": name,
                "name_translated": translated,
                "extra_info": extra_info,
                "promotion": promotion,
                "discounted_price": discounted,
                "original_price": original,
                "href": None
            })
    return all_items

parsers = {
    "plus": parse_plus,
    "ah": parse_ah,
    "dm": parse_dm,
}

def scrape_store(store:str, out_dir="data"):
    if store not in url_maps:
        print(f"Store '{store}' not recognized. Available stores: {list(url_maps.keys())}")
        return None, None, None
    
    # Make sure output dir exists
    os.makedirs(out_dir, exist_ok=True)

    # Generate today's filename
    today = datetime.now().strftime("%Y-%m-%d")
    out_file = os.path.join(out_dir, f"{store}_{today}.json")
    
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            items = json.load(f)
        print(f"Loaded existing file: {out_file}")
        return out_file, items
    
    for fname in os.listdir(out_dir):
        if fname.startswith(f"{store}_") and fname.endswith(".json"):
            os.remove(os.path.join(out_dir, fname))
            print(f"Deleted old file: {fname}")
    
    html = get_html(url_maps[store])
    soup = BeautifulSoup(html, "html.parser")
    items = parsers[store](soup)
    save_offers(items, out_file)
    return out_file, items
    
    