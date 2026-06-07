import discord
from discord.ext import commands
import os
import aiohttp
import io
import re
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

script_library = {}

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"✅ GrimHub ready - {bot.user}")
    print(f"⚠️ This bot will NEVER ping anyone")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Only respond to commands with prefix
    if message.content.startswith('.'):
        await bot.process_commands(message)

@bot.command(name='feed')
async def feed_script(ctx):
    """Store a Lua script (any size)"""
    if not ctx.message.attachments:
        await ctx.send("Attach a .lua file")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith('.lua'):
        await ctx.send("Upload a .lua file")
        return
    
    content = await attachment.read()
    try:
        code = content.decode('utf-8')
        size_kb = len(code) / 1024
        
        name = attachment.filename.replace('.lua', '')
        script_library[name] = code
        
        await ctx.send(f"Stored {attachment.filename} ({size_kb:.2f} KB)")
        
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name='get')
async def get_script(ctx, *, name):
    """Retrieve a stored script"""
    if name in script_library:
        code = script_library[name]
        size_kb = len(code) / 1024
        filename = f"{name}.lua"
        
        await ctx.send(file=discord.File(io.StringIO(code), filename=filename))
        await ctx.send(f"{size_kb:.2f} KB")
    else:
        await ctx.send(f"Script '{name}' not found")

@bot.command(name='list')
async def list_scripts(ctx):
    """List all stored scripts"""
    if not script_library:
        await ctx.send("No scripts stored. Use .feed")
        return
    
    msg = f"**Stored Scripts ({len(script_library)} total)**\n\n"
    for name, code in list(script_library.items())[:20]:
        size_kb = len(code) / 1024
        msg += f"`{name}.lua` - {size_kb:.2f} KB\n"
    
    await ctx.send(msg)

@bot.command(name='remove')
async def remove_script(ctx, *, name):
    """Remove a stored script"""
    if name in script_library:
        del script_library[name]
        await ctx.send(f"Removed '{name}'")
    else:
        await ctx.send(f"Script '{name}' not found")

@bot.command(name='info')
async def script_info(ctx, *, name):
    """Get script info"""
    if name in script_library:
        code = script_library[name]
        size_kb = len(code) / 1024
        lines = code.count('\n')
        await ctx.send(f"**{name}.lua**\nSize: {size_kb:.2f} KB\nLines: {lines}\nChars: {len(code):,}")
    else:
        await ctx.send(f"Script '{name}' not found")

@bot.command(name='commands')
async def list_commands(ctx):
    await ctx.send("""
**GrimHub Commands**
`.feed` - Upload a .lua file to store
`.get <name>` - Retrieve a stored script
`.list` - List all stored scripts
`.info <name>` - Get script info
`.remove <name>` - Remove a script

⚠️ This bot NEVER pings anyone
""")

bot.run(TOKEN)
