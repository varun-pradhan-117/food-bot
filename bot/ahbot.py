import discord
from discord.ext import commands
import asyncio
from db.mongo_utils import get_user_sheet, save_user_sheet
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Discord bot with prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

async def handle_registration(user):
    dm = await user.create_dm()
    existing = await get_user_sheet(str(user.id))

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

    await dm.send("Send the Google Sheet URL you want to register:")

    def check_sheet(m): return m.author == user and isinstance(m.channel, discord.DMChannel)
    try:
        response = await bot.wait_for('message', check=check_sheet, timeout=300)
        sheet_url = response.content.strip()
        await save_user_sheet(str(user.id), sheet_url)
        await dm.send("Sheet registered successfully!")
    except asyncio.TimeoutError:
        await dm.send("Registration timed out. Please try again.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='register')
async def register(ctx):
    await handle_registration(ctx.author)
    
@bot.command(name="plan")
async def plan(ctx):
    pass    
    
bot.run(TOKEN)