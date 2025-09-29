import json
import uuid
import re
from tqdm import tqdm
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import ollama
from pymongo import MongoClient
from qdrant_client import QdrantClient, models

# Mongo config
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "grocerbot"
RECIPE_COLLECTION = "recipes"

# Qdrant collection
QDRANT_COLLECTION = "recipes_vectors"

# Base project directory (one level up from misc_utils)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FOLDER = os.path.join(BASE_DIR, "recipe_data", "recipes_raw")
OUTPUT_FILE = os.path.join(BASE_DIR, "recipe_data", "cleaned_recipes.json")

# Keywords for diet
NON_VEG_KEYWORDS = [
    "chicken", "beef", "pork", "lamb", "fish", "shrimp", "crab", "bacon", "meat", "turkey", "salmon"
]

DAIRY_EGG_KEYWORDS = [
    "milk", "cheese", "butter", "cream", "egg", "yogurt", "mayonnaise"
]

# Map filename shorthand to source names
SOURCE_MAP = {
    "ar": "allrecipes",
    "epi": "epicurious",
    "fn": "foodnetwork"
}


qclient = None

def init_qdrant(path=None, url=None, api_key=None):
    global qclient
    if path:
        qclient = QdrantClient(path=path)
    elif url and api_key:
        qclient = QdrantClient(url=url, api_key=api_key)
    elif url:
        qclient = QdrantClient(url=url)
    else:
        qclient = QdrantClient(":memory:")
    return qclient

def clean_ingredient(ingredient: str) -> str:
    """Remove unwanted tokens and trim whitespace"""
    return re.sub(r"\bADVERTISEMENT\b", "", ingredient).strip()

def embed_text(text: str):
    """Return embedding from Nomic model via Ollama"""
    resp = ollama.embeddings(model="nomic-embed-text", prompt=text)
    return resp["embedding"]

def make_point(r):
    content = r['title'] + "\n" + "\n".join(r["ingredients"])
    embedding = embed_text(content)  # your embedding function
    return models.PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload=r
    )
    
def classify_diet(ingredients: list[str]) -> str:
    """Classify recipe as vegan / vegetarian / nonveg based on ingredients"""
    ing_text = " ".join(ingredients).lower()

    if any(word in ing_text for word in NON_VEG_KEYWORDS):
        return "nonveg"
    elif any(word in ing_text for word in DAIRY_EGG_KEYWORDS):
        return "vegetarian"
    else:
        return "vegan"
    


def process_recipes(input_folder: str):
    """Clean raw recipes and return list of dicts"""
    cleaned_data = []

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue
        print("Extracting:", filename)

        # Extract source (ar, epi, fn)
        source_key = filename.split("_")[-1].replace(".json", "")
        source = SOURCE_MAP.get(source_key, "unknown")

        filepath = os.path.join(input_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        skips = 0
        registered = 0

        for _, recipe in raw_data.items():
            try:
                title = recipe.get("title", "").strip()
                ingredients = recipe.get("ingredients", [])
                instructions = recipe.get("instructions", "").strip()

                if not title or not ingredients or not instructions:
                    skips += 1
                    continue

                cleaned_ingredients = [clean_ingredient(i) for i in ingredients if i]
                cleaned_ingredients = [i for i in cleaned_ingredients if i]

                if not cleaned_ingredients:
                    skips += 1
                    continue
                diet = classify_diet(cleaned_ingredients)
                cleaned_data.append({
                    "title": title,
                    "ingredients": cleaned_ingredients,
                    "instructions": instructions,
                    "diet": diet,
                    "source": source
                })
                registered += 1

            except Exception:
                skips += 1
                continue

        print(f"{filename} | registered = {registered} | skipped = {skips}")

    return cleaned_data

def save_to_mongo(data, overwrite=False):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[RECIPE_COLLECTION]

    existing_count = collection.count_documents({})
    if existing_count > 0 and not overwrite:
        print(f"Collection '{RECIPE_COLLECTION}' already has {existing_count} recipes. Skipping (use --overwrite or --append).")
        return

    if overwrite:
        collection.delete_many({})
        print(f"Cleared existing recipes in '{RECIPE_COLLECTION}'")

    if data:
        collection.insert_many(data)
        print(f"Inserted {len(data)} recipes into MongoDB collection '{RECIPE_COLLECTION}'")

def save_to_file(data, output_file):
    with open(output_file, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} recipes -> {output_file}")
        
def save_to_qdrant(data, path=None, url=None, api_key=None, overwrite=True):
    if path:
        print(f"Using local Qdrant path: {path}")
        qclient = QdrantClient(path=path)
    elif url and api_key:
        print(f"Using Qdrant cloud URL: {url}")
        qclient= QdrantClient(url=url, api_key=api_key)
    elif url:
        print(f"Using Qdrant server URL: {url}")
        qclient = QdrantClient(url=url)
    else:
        print("Using in-memory Qdrant instance")
        qclient = QdrantClient(":memory:")
        
    if overwrite:
       qclient.delete_collection(collection_name=QDRANT_COLLECTION) 
    if not qclient.collection_exists(QDRANT_COLLECTION):
        qclient.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=768,
                distance=models.Distance.COSINE,
            )
        )
        print(f"Created/Recreated Qdrant collection '{QDRANT_COLLECTION}'")
    print("Embedding recipes")
    points = []
    with ThreadPoolExecutor(max_workers=16) as executor:  # adjust workers based on CPU
        futures = {executor.submit(make_point, r): r for r in data}
        for future in tqdm(as_completed(futures), total=len(data), desc="Embedding recipes"):
            points.append(future.result())
    print("Upserting to Qdrant")
    if points:
        qclient.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points
        )
    print("Upserted", len(points), "points to Qdrant collection", QDRANT_COLLECTION)

def search_recipes_qdrant(
    item_list: list[str],
    top_k: int = 5,
    diet: str = None,
    path: str = None,
    url: str = None,
    api_key: str = None,
):
    """Search Qdrant for recipes matching the given list of items."""
    # optional diet filter
    qfilter = None
    if diet:
        qfilter = models.Filter(
            must=[models.FieldCondition(key="diet", match=models.MatchValue(value=diet))]
        )
    if not qclient:
        init_qdrant(path=path, url=url, api_key=api_key)
    # Embed all items together
    query_text = "\n".join(item_list)
    vector = embed_text(query_text)  # your embedding function

    # Search Qdrant
    hits = qclient.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=vector,
        query_filter=qfilter,
        limit=top_k * 2,  # fetch extra for deduplication
    )

    # Deduplicate by title
    seen_titles = set()
    results = []
    for hit in hits:
        title = hit.payload.get("title")
        if title and title not in seen_titles:
            seen_titles.add(title)
            results.append({
                "score": hit.score,
                "title": title,
                "ingredients": hit.payload.get("ingredients"),
                "instructions": hit.payload.get("instructions"),
                "diet": hit.payload.get("diet"),
                "source": hit.payload.get("source"),
            })
        if len(results) >= top_k:
            break

    return results
    



def main():
    parser = argparse.ArgumentParser(description="Process and store recipes")
    parser.add_argument("--to-file", action="store_true", help="Save cleaned recipes to JSON file")
    parser.add_argument("--to-mongo", action="store_true", help="Save cleaned recipes to MongoDB")
    parser.add_argument("--to-qdrant", action="store_true", help="Save recipes to Qdrant")
    parser.add_argument("--append", action="store_true", help="Append to existing data")
    parser.add_argument("--qdrant-path", type=str, help="Local Qdrant path for persistence")
    parser.add_argument("--qdrant-url", type=str, help="Qdrant server URL")
    parser.add_argument("--qdrant-key", type=str, help="Qdrant API key (for cloud)")
    
    args=parser.parse_args()
    data=process_recipes(INPUT_FOLDER)
    
    if args.to_file:
        save_to_file(data, OUTPUT_FILE)
    if args.to_mongo:
        save_to_mongo(data, overwrite=not args.append)
        
    if args.to_qdrant:
        os.makedirs('qdrantdb', exist_ok=True)
        save_to_qdrant(data, path=args.qdrant_path, url=args.qdrant_url, api_key=args.qdrant_key, overwrite=not args.append)


if __name__ == "__main__":
    main()


