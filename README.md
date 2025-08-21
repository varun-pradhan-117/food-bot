# Food Bot - Discount Retrieving Discord Bot (WIP)

A Discord bot that helps users plan meals based on their pantry inventory and current store discounts from Albert Heijn. The bot integrates with Google Sheets for inventory management and uses Ollama AI for meal planning suggestions.

## Features

- **Discord Integration**: Built with discord.py for seamless Discord server integration
- **Inventory Management**: Connects to Google Sheets to track pantry items
- **Discount Scraping**: Automatically scrapes current deals from Plus
- **AI Meal Planning**: Uses a local deepseek instance (via ollama) to provide recipes based on discounts and current inventory.
- **MongoDB Storage**: Stores sheet URLs

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Google Sheets API credentials
- MongoDB instance (optional, for user data storage)
- Ollama AI instance running locally

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd AHBot
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Discord Bot Configuration
DISCORD_TOKEN=<your_discord_bot_token_here>

# Google Sheets API (if using)
GOOGLE_SHEETS_CREDENTIALS_FILE=<path to credentials>

# MongoDB Configuration (optional)
MONGODB_URI=mongodb://localhost:27017/ahbot

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

### 5. Start the Bot

```bash
# Make sure your virtual environment is activated
python -m bot.discord_bot
```

## Bot Commands

- `$register` - Register your Google Sheet for inventory tracking
- `$plan` - Generate a meal plan based on your pantry and current discounts

## Troubleshooting

### Common Issues:

1. **Discord Bot Not Responding**: Check if the bot token is correct and the bot has proper permissions
2. **Google Sheets Access Error**: Verify the service account has access to your sheet
3. **MongoDB Connection Error**: Check if MongoDB is running and the connection string is correct

### Logs:

The bot will print status messages to the console when starting up and processing commands.
