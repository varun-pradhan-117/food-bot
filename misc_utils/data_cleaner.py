import json
import uuid
import re
import os

# Base project directory (one level up from misc_utils)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FOLDER = os.path.join(BASE_DIR, "recipe_data", "recipes_raw")
OUTPUT_FILE = os.path.join(BASE_DIR, "recipe_data", "cleaned_recipes.json")

# Map filename shorthand to source names
SOURCE_MAP = {
    "ar": "allrecipes",
    "epi": "epicurious",
    "fn": "foodnetwork"
}

def clean_ingredient(ingredient: str) -> str:
    return re.sub(r"\bADVERTISEMENT\b", "", ingredient).strip()

def clean_recipes_folder(input_folder: str, output_file: str):
    cleaned_data = []

    for filename in os.listdir(input_folder):
        if not filename.endswith(".json"):
            continue
        print("Extracting:", filename)
        # Extract source from filename
        # Example: recipe_raw_nosource_ar.json -> ar
        source_key = filename.split("_")[-1].replace(".json", "")
        source = SOURCE_MAP.get(source_key, "unknown")

        filepath = os.path.join(input_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        skips=0
        registered=0
        for _, recipe in raw_data.items():
            try:
                title = recipe.get("title")
                title = title.strip()

                ingredients = recipe.get("ingredients", [])
                instructions = recipe.get("instructions", "")
                if instructions:
                    instructions = instructions.strip()
                picture_link = recipe.get("picture_link", None)

                cleaned_ingredients = [
                    clean_ingredient(i) for i in ingredients if i and "ADVERTISEMENT" not in i
                ]
                cleaned_ingredients = [i for i in cleaned_ingredients if i]  # drop empties

                cleaned_data.append({
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "ingredients": cleaned_ingredients,
                    "instructions": instructions,
                    "picture_link": picture_link,
                    "source": source
                })
                registered+=1

            except Exception as e:
                skips+=1
                continue
        print(f"{filename} | registered = {registered} | skipped = {skips}")


    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Cleaned {len(cleaned_data)} recipes -> {output_file}")


if __name__ == "__main__":
    clean_recipes_folder(INPUT_FOLDER, OUTPUT_FILE)



