import discord
from discord.ext import commands

from dotenv import load_dotenv
import ollama
from ollama import AsyncClient

import os
import asyncio
from db.async_utils import get_user, save_user
from misc_utils.google_utils import read_sheet_to_string
from misc_utils.utils import discounts_to_string
from scrapers import scrape_store, maps

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
    print("Checking inventory...")
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
    
    if not grocery_stores:
        grocery_stores= list(maps.values())
    
    
    # 2. Fetching discounts
    store_dict = {store: {} for store in grocery_stores}
    all_translated_names = []
    print("Checking discounts...")
    for store in grocery_stores:
        try:
            out_file, items = scrape_store(store)
            
            if not items:
                print(f"No discounts found for {store}")
                continue
            
            # full details, store by store
            store_dict[store] = items
            
            # only the translated names, for vector search
            all_translated_names.extend(
                item["name_translated"] for item in items if item.get("name_translated")
            )
            
            print(f"{store}: {len(items)} items scraped")
        
        except Exception as e:
            print(f"Error fetching {store}: {e}")
        
        
    # 3. Craft prompt for Ollama
    prompt = f"""
        You are a helpful chef AI. Using the pantry items below and the current store discounts, suggest a couple of recipes for breakfast and lunch+dinner(same or different) each.
        Try to keep the recipers simple and concise, using simple ingredients.
        Don't go overboard with the number of recipes or explanations.
        Don't explain the recipes in depth, just give the main ingredients and a short description.
        Don't give a massive list or anything like "IDEA" or what to stock up on.
        Stick to a handful of recipes.
        Pantry items:
        {pantry_text}

        Current discounts:
        {discounts_text}

        Give concise recipe suggestions, combining pantry and discounted items if possible.
        """
        
    # 4. Call Ollama
    print("Calling Ollama...")
    client = AsyncClient()
    message = {'role': 'user', 'content': prompt}
    response = await client.chat(model="deepseek-r1:8b", messages=[message])

    # 5. Extract and send LLM output
    try:
        print(response)
        answer = response.message.content
        # Strip everything before </think>
        if "</think>" in answer:
            answer = answer.split("</think>", 1)[1].strip()
        for chunk in split_message(answer):
            await ctx.send(chunk)
    except Exception as e:
        print("Error extracting response from LLM: ",e)
        await ctx.send("Could not get a response from the LLM.")
    
bot.run(TOKEN)