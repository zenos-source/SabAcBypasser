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

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Handle pings
    if bot.user in message.mentions:
        content = re.sub(r'<@!?\d+>', '', message.content).strip()
        
        if not content:
            await message.reply("Use `.commands`")
        elif content.lower() in ['hi', 'hello', 'hey', 'sup']:
            await message.reply(f"Hey {message.author.name}")
        else:
            await message.reply("Use `.commands`")
        return
    
    if message.content.startswith('.'):
        await bot.process_commands(message)

@bot.command(name='feed')
async def feed_script(ctx):
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
    if name in script_library:
        code = script_library[name]
        size_kb = len(code) / 1024
        await ctx.send(file=discord.File(io.StringIO(code), filename=f"{name}.lua"))
        await ctx.send(f"{size_kb:.2f} KB")
    else:
        await ctx.send(f"Script '{name}' not found")

@bot.command(name='list')
async def list_scripts(ctx):
    if not script_library:
        await ctx.send("No scripts stored")
        return
    
    msg = f"**Stored Scripts ({len(script_library)} total)**\n\n"
    for name, code in list(script_library.items())[:20]:
        size_kb = len(code) / 1024
        msg += f"`{name}.lua` - {size_kb:.2f} KB\n"
    await ctx.send(msg)

@bot.command(name='remove')
async def remove_script(ctx, *, name):
    if name in script_library:
        del script_library[name]
        await ctx.send(f"Removed '{name}'")
    else:
        await ctx.send(f"Script '{name}' not found")

@bot.command(name='info')
async def script_info(ctx, *, name):
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
`.feed` - Upload a .lua file
`.get <name>` - Retrieve a script
`.list` - List all scripts
`.info <name>` - Script details
`.remove <name>` - Delete a script
""")

bot.run(TOKEN)
