# Food Bot - AI-Powered Meal Planning Discord Bot (WIP)

A Discord bot that helps users plan meals based on their pantry inventory and current store discounts from Albert Heijn. The bot integrates with Google Sheets for inventory management and uses Ollama AI for meal planning suggestions.

## Features

- **Discord Integration**: Built with discord.py for seamless Discord server integration
- **Inventory Management**: Connects to Google Sheets to track pantry items
- **Discount Scraping**: Scrapes current deals from Plus, Albert Heijn, and DekaMarkt
- **AI Meal Planning**: Uses a local DeepSeek model (via Ollama) to suggest meals using your pantry and current discounts
- **MongoDB Storage**: Stores user profile, sheet URL, preferences, and store list
- **Vector Recipe Search (Qdrant)**: Recipes are embedded and stored in a Qdrant vector DB for fast semantic search

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Google Sheets API credentials (optional)
- MongoDB instance (optional, for user data storage)
- Ollama running locally with models: `deepseek-r1:8b` and `nomic-embed-text`
- Qdrant (local persistent path or server/cloud)
- Firefox + Geckodriver in PATH (required for Selenium-based scrapers)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/varun-pradhan-117/food-bot
```

### 2. Download Recipe Dataset

**This is the first essential step!** You need to download the recipe dataset before proceeding.

1. Visit [Eight Portions Recipe Dataset](https://eightportions.com/datasets/Recipes/#fn:1)
2. Download the recipe data (approximately 125,000 recipes from various food websites)
3. Extract the downloaded files to the `recipe_data/recipes_raw/` directory
4. Ensure you have the following files in `recipe_data/recipes_raw/`:
   - `recipes_raw_nosource_ar.json` (AllRecipes)
   - `recipes_raw_nosource_epi.json` (Epicurious)
   - `recipes_raw_nosource_fn.json` (Food Network)

### 3. Clean and Process Recipe Data

**This step is required before running the bot!** The raw recipe data needs to be cleaned and processed.

```bash
# From the project root

# Option A: Clean to file only (for inspection)
python -m misc_utils.recipe_processing --to-file

# Option B: Build the Qdrant vector index (recommended)
python -m misc_utils.recipe_processing --to-qdrant --qdrant-path qdrantdb
```

This will:
- Process all raw recipe JSON files
- Clean ingredients and remove advertisements
- Classify each recipe by diet (vegan/vegetarian/nonveg)
- Optionally embed and upsert recipes into a Qdrant collection (`recipes_vectors`)
- Generate a unified `cleaned_recipes.json` file if `--to-file` is used

**Expected output:**
```
Extracting: recipes_raw_nosource_ar.json
recipes_raw_nosource_ar.json | registered = XXXX | skipped = XX
Extracting: recipes_raw_nosource_epi.json
recipes_raw_nosource_epi.json | registered = XXXX | skipped = XX
Extracting: recipes_raw_nosource_fn.json
recipes_raw_nosource_fn.json | registered = XXXX | skipped = XX
✅ Cleaned XXXXX recipes -> /path/to/cleaned_recipes.json
```

### 4. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** If `requirements.txt` doesn't exist, you'll need to install the required packages manually:

```bash
pip install discord.py google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pymongo
```

### 6. Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Discord Bot Configuration
DISCORD_TOKEN=<your_discord_bot_token_here>

# Google Sheets API (if using)
GOOGLE_SHEETS_CREDENTIALS_FILE=<path to credentials>

# MongoDB Configuration (optional)
MONGO_URI=mongodb://localhost:27017/

# Qdrant local path used by the bot to query recipes
# Must point to the same path used when building the index
QDRANT_PATH=./qdrantdb
```

#### Getting Your Discord Bot Token:

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Copy the token and add it to your `.env` file

#### Setting Up Google Sheets API:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create service account credentials
5. Download the JSON file and place it in the `secrets/` folder
6. Share your Google Sheet with the service account email

### 7. Start the Bot

```bash
# Make sure your virtual environment is activated
python -m bot.discord_bot
```

## Project Structure

```
AHBot/
├── bot/                     # Discord bot implementation
├── data/                    # Scraped discount JSONs by store/date
├── db/                      # Async Mongo helpers
├── misc_utils/              # Data processing and utilities
│   ├── recipe_processing.py # Clean, embed, and index recipes (Qdrant/Mongo/JSON)
│   ├── google_utils.py      # Google Sheets integration
│   └── utils.py             # General utilities
├── qdrantdb/                # Local Qdrant persistent store (if using --qdrant-path)
├── recipe_data/             # Recipe datasets
│   ├── recipes_raw/         # Raw downloaded recipe data
│   └── cleaned_recipes.json # Processed and cleaned recipes (optional)
├── scrapers/                # Web scraping utilities (Plus, AH, DekaMarkt)
└── watchdog/                # Monitoring utilities
```

## Bot Commands

- `$register` - Register your Google Sheet URL, preferences, and nearby stores via DM
- `$preferences` - Update dietary preferences and likes/dislikes via DM
- `$stores` - Update the list of nearby grocery stores (`plus`, `ah`, `dm`) via DM
- `$plan` - Generate a meal plan based on your pantry, discounts, and retrieved recipes

Notes:
- If you haven't set stores, the bot defaults to all supported stores.
- The `$plan` command searches the Qdrant vector DB for relevant recipes using discounted items and your diet.

## Scraper Options (Stores)

Supported store keys (case-insensitive):
- `plus` → PLUS aanbiedingen (`https://www.plus.nl/aanbiedingen`)
- `ah` → Albert Heijn Bonus (`https://www.ah.nl/bonus`)
- `dm` → DekaMarkt aanbiedingen (`https://www.dekamarkt.nl/aanbiedingen`)

How it works:
- During `$register` or `$stores`, provide a comma-separated list like `plus, ah, dm`.
- The bot scrapes current promotions per store and aggregates translated item names.
- These names are used to query the Qdrant recipe index for relevant meals.

## Troubleshooting

### Common Issues:

1. **Recipe Data Not Found**: Ensure you've downloaded and extracted the recipe dataset to `recipe_data/recipes_raw/`
2. **Data Cleaning Failed**: Check that all raw recipe files are present and have the correct naming convention
3. **Discord Bot Not Responding**: Check if the bot token is correct and the bot has proper permissions
4. **Google Sheets Access Error**: Verify the service account has access to your sheet
5. **MongoDB Connection Error**: Check if MongoDB is running and `MONGO_URI` is correct
6. **Qdrant Not Queried**: Ensure you've built the index with `--to-qdrant` and `QDRANT_PATH` points to the same directory
7. **Scraper Fails to Launch**: Install Firefox and ensure drivers are included in PATH

### Data Cleaning Issues:

If the data cleaning process fails or produces unexpected results:

1. Verify all raw recipe files are present in `recipe_data/recipes_raw/`
2. Check file permissions and ensure Python can read the JSON files
3. Review the console output for specific error messages
4. Ensure the `recipe_data/` directory structure is correct

### Logs:

The bot will print status messages to the console when starting up and processing commands. The data cleaner also provides detailed progress information during the cleaning process.

## Dataset Information

The [recipe dataset](https://github.com/rtlee9/recipe-box/tree/master/src) contains approximately 125,000 recipes from:
- **AllRecipes** (`ar`): Popular home cooking recipes
- **Epicurious** (`epi`): Gourmet and fine dining recipes  
- **Food Network** (`fn`): Celebrity chef and TV show recipes

Each recipe includes:
- Title
- Ingredients list with measurements
- Step-by-step instructions
- Source attribution
- Picture links (where available)

### Vector Database Details

- Embeddings: `nomic-embed-text` via Ollama
- Vector store: Qdrant collection `recipes_vectors` (cosine distance, 768-dim)
- Query: Discount item names are embedded and used to search relevant recipes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the data cleaning process
5. Submit a pull request

## License

This project uses the Eight Portions recipe dataset. Please refer to the LICENSE file in `recipe_data/recipes_raw/` for dataset usage terms.
