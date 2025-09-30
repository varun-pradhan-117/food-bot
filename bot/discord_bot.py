import discord
from discord.ext import commands

from dotenv import load_dotenv
from ollama import AsyncClient

import os
import asyncio
from db.async_utils import get_user, save_user
from misc_utils.google_utils import read_sheet_to_string
from misc_utils.recipe_processing import search_recipes_qdrant
from scrapers import scrape_store, maps
from bot.deepseek_utils import select_recipes

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Discord bot with prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

def split_message(msg: str, limit: int = 2000):
    return [msg[i:i+limit] for i in range(0, len(msg), limit)]

async def handle_registration(user):
    dm = await user.create_dm()
    existing = await get_user(str(user.id))

    if existing:
        await dm.send("You already have a sheet registered. Update it? (yes/no)")
        def check_reply(m): return m.author == user and isinstance(m.channel, discord.DMChannel)
        try:
            reply = await bot.wait_for('message', check=check_reply, timeout=300)
            if reply.content.lower() not in ['yes','y']:
                await dm.send("Registration canceled.")
                return
        except asyncio.TimeoutError:
            await dm.send("Timed out. Try again.")
            return

    # Get Google Sheet
    await dm.send("Send the Google Sheet URL you want to register:")
    def check_sheet(m): return m.author == user and isinstance(m.channel, discord.DMChannel)
    try:
        response = await bot.wait_for('message', check=check_sheet, timeout=300)
        sheet_url = response.content.strip()
    except asyncio.TimeoutError:
        await dm.send("Registration timed out. Please try again.")
        return

    # Get Preferences
    await dm.send("Now, tell me your preferences in this format:\n"
                  "`diet=vegetarian; allergies=peanuts,gluten; dislikes=mushrooms; likes=spicy`\n"
                  "(leave blank if none)")

    def check_prefs(m): return m.author == user and isinstance(m.channel, discord.DMChannel)
    try:
        pref_msg = await bot.wait_for('message', check=check_prefs, timeout=300)
        prefs_text = pref_msg.content.strip()
    except asyncio.TimeoutError:
        prefs_text = ""

    preferences = {}
    if prefs_text:
        for part in prefs_text.split(";"):
            if "=" in part:
                key, val = part.split("=", 1)
                preferences[key.strip()] = [v.strip() for v in val.split(",")] if "," in val else val.strip()

    # After preferences step
    await dm.send("Finally, list your nearby grocery stores (comma separated), e.g.:\n"
                "`plus, ah, dm` (leave blank if none)")

    def check_stores(m): return m.author == user and isinstance(m.channel, discord.DMChannel)
    try:
        store_msg = await bot.wait_for('message', check=check_stores, timeout=300)
        stores_text = store_msg.content.strip()
    except asyncio.TimeoutError:
        stores_text = ""

    grocery_stores = [s.strip() for s in stores_text.split(",")] if stores_text else []

    await save_user(str(user.id), sheet_url=sheet_url, preferences=preferences, grocery_stores=grocery_stores)
    await dm.send("Registration completed successfully!")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='register')
async def register(ctx):
    await handle_registration(ctx.author)
    
    
@bot.command(name='preferences')
async def preferences(ctx):
    user = ctx.author
    dm = await user.create_dm()
    await dm.send("Send me your preferences in this format:\n"
                  "`diet=vegan; allergies=nuts; dislikes=cilantro; likes=spicy`\n")

    def check(m): return m.author == user and isinstance(m.channel, discord.DMChannel)
    try:
        msg = await bot.wait_for('message', check=check, timeout=300)
        prefs_text = msg.content.strip()
    except asyncio.TimeoutError:
        await dm.send("Timed out. Try again.")
        return

    preferences = {}
    if prefs_text:
        for part in prefs_text.split(";"):
            if "=" in part:
                key, val = part.split("=", 1)
                preferences[key.strip()] = [v.strip() for v in val.split(",")] if "," in val else val.strip()

    await save_user(str(user.id), preferences=preferences)
    await dm.send("Preferences updated successfully!")
    
@bot.command(name='stores')
async def stores(ctx):
    user = ctx.author
    dm = await user.create_dm()
    await dm.send("Send me your nearby grocery stores (comma separated), e.g.:\n"
                  "`plus, ah, dm`")

    def check(m): return m.author == user and isinstance(m.channel, discord.DMChannel)
    try:
        msg = await bot.wait_for('message', check=check, timeout=300)
        stores_text = msg.content.strip()
    except asyncio.TimeoutError:
        await dm.send("Timed out. Try again.")
        return

    grocery_stores = [s.strip() for s in stores_text.split(",")] if stores_text else []

    await save_user(str(user.id), grocery_stores=grocery_stores)
    await dm.send("Nearby grocery stores updated successfully!")


@bot.command(name="plan")
async def plan(ctx):
    await ctx.send("Generating your meal plan...")
    
    # 1. Get user sheet if it exists
    print("Checking inventory")
    user_entry = await get_user(str(ctx.author.id))
    
    # Abort if user not registered
    if not user_entry:
        await ctx.send(
            "I don't have your registration info. Please register first with `$register` "
        )
        return
    
    # Pantry
    sheet_url = user_entry.get("sheet_url")
    if sheet_url:
        try:
            pantry_text = await read_sheet_to_string(sheet_url)
        except Exception as e:
            await ctx.send("Failed to read your pantry sheet. Check the sharing settings.")
            print(f"[plan] error reading sheet for user {ctx.author.id}: {e}")
            pantry_text = "- No pantry items available."
    else:
        pantry_text = "- No pantry items available."
    
    grocery_stores = user_entry.get("grocery_stores", []) 
    preferences=user_entry.get("preferences", {})
    diet=preferences.get("diet", None)
    preferences_str = ", ".join(f"{k}: {v}" for k, v in preferences.items())

    if not grocery_stores:
        grocery_stores= list(maps.values())
    
    
    # 2. Fetch discounts (offloaded to threads)
    store_dict = {store: {} for store in grocery_stores}
    all_translated_names = []
    print("Checking discounts")

    for store in grocery_stores:
        try:
            out_file, items = await asyncio.to_thread(scrape_store, store)
            
            if not items:
                print(f"No discounts found for {store}")
                continue
            
            store_dict[store] = items
            all_translated_names.extend(
                item["name_translated"] for item in items if item.get("name_translated")
            )
            print(f"{store}: {len(items)} items scraped")

        except Exception as e:
            print(f"Error fetching {store}: {e}")
        
    
    # 3. Search recipes in Qdrant (offloaded too)
    print("Searching recipes in Qdrant")
    recipes = await asyncio.to_thread(
        search_recipes_qdrant,
        all_translated_names,
        10,
        diet,
        os.getenv("QDRANT_PATH"),
    )

    if not recipes:
        await ctx.send("No suitable recipes found right now.")
        return

    recipes_text = "\n\n".join(
        f"Title: {r['title']}\nIngredients: {', '.join(r['ingredients'])}"
        for r in recipes
    )
    
    # 4. Craft prompt for Ollama
    resp =await asyncio.to_thread(
        select_recipes,
        recipes_text,
        preferences_str
    )
    print(resp)
    return
    
bot.run(TOKEN)