import discord
from discord.ext import commands
import os
import re
import io
import aiohttp
import json
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_URL = "https://discord.com/api/webhooks/1513000656598732893/24xJXBUL8V8lMbQWHvoZkAvhkGfJIjsfO-IU3FTkbdWb0QtLTKlIms50zsAEvUTKpW6B"

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

user_scripts = {}
learning_data = []

async def generate_lua_script(prompt: str) -> str:
    """Use Groq API to generate Lua code"""
    if not GROQ_API_KEY:
        return "-- Error: GROQ_API_KEY not configured"
    
    system_prompt = """You are a Lua scripting expert for Roblox. Generate ONLY raw Lua code.
No markdown, no explanations, no comments starting with --, no print statements.
Just the code. Use local variables and game:GetService()."""
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write a Lua script for Roblox that: {prompt}"}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as resp:
                text = await resp.text()
                print(f"Groq Response Status: {resp.status}")
                
                if resp.status == 200:
                    data = json.loads(text)
                    code = data["choices"][0]["message"]["content"]
                    code = re.sub(r'```lua\n?', '', code)
                    code = re.sub(r'```\n?', '', code)
                    code = re.sub(r'^--.*\n?', '', code, flags=re.MULTILINE)
                    return code.strip()
                else:
                    print(f"Groq Error: {text}")
                    return f"-- Error: API returned {resp.status}\n-- Check your GROQ_API_KEY"
    except Exception as e:
        print(f"Exception: {e}")
        return f"-- Error: {str(e)}"

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"GrimHub Bot ready - {bot.user}")
    print(f"Groq API Key: {'SET' if GROQ_API_KEY else 'NOT SET'}")
    print("Commands: .makescript, .feed, .history, .commands")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.startswith('.'):
        await bot.process_commands(message)
        return
    
    if bot.user in message.mentions:
        await message.reply(f"Hello {message.author.name}! Use `.makescript <prompt>` to generate a script, or `.commands` for help.")
        return
    
    await bot.process_commands(message)

@bot.command(name='makescript')
async def make_script(ctx, *, prompt):
    if not prompt:
        await ctx.send("Usage: `.makescript <description of script>`")
        return
    
    if not GROQ_API_KEY:
        await ctx.send("❌ GROQ_API_KEY not configured. Add to Railway variables.")
        return
    
    await ctx.send(f"🤖 Generating script... Check your DMs!")
    
    script = await generate_lua_script(prompt)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GrimHub_{ctx.author.name}_{timestamp}.lua"
    
    if ctx.author.id not in user_scripts:
        user_scripts[ctx.author.id] = []
    user_scripts[ctx.author.id].append({
        'prompt': prompt,
        'timestamp': timestamp,
        'filename': filename,
        'content': script
    })
    
    # Send to webhook with file
    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            file_obj = discord.File(io.StringIO(script), filename=filename)
            embed = discord.Embed(
                title="📜 Script Generated",
                description=f"**User:** {ctx.author}\n**Prompt:** {prompt[:200]}",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            await webhook.send(embed=embed, file=file_obj)
    except Exception as e:
        print(f"Webhook error: {e}")
    
    # Send to user DM
    try:
        file_obj = discord.File(io.StringIO(script), filename=filename)
        await ctx.author.send(f"**Prompt:** {prompt}\n", file=file_obj)
        await ctx.send(f"✅ Script sent to your DMs!")
    except discord.Forbidden:
        await ctx.send("❌ I cannot DM you! Please enable DMs.")

@bot.command(name='feed')
async def feed_script(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach a `.lua` or `.txt` file!")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(('.lua', '.txt')):
        await ctx.send("❌ Please upload a `.lua` or `.txt` file!")
        return
    
    content = await attachment.read()
    try:
        code = content.decode('utf-8')
        
        learning_data.append({
            'filename': attachment.filename,
            'content': code,
            'uploaded_by': str(ctx.author),
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to webhook with the actual file
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            file_obj = discord.File(io.StringIO(code), filename=attachment.filename)
            embed = discord.Embed(
                title="📖 Script Fed to AI",
                description=f"**User:** {ctx.author}\n**File:** {attachment.filename}\n**Size:** {len(code)} chars",
                color=0x00aaff,
                timestamp=datetime.utcnow()
            )
            await webhook.send(embed=embed, file=file_obj)
        
        await ctx.send(f"✅ Fed `{attachment.filename}` to AI for learning!")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='history')
async def script_history(ctx):
    if ctx.author.id not in user_scripts or not user_scripts[ctx.author.id]:
        await ctx.send("📭 No scripts generated yet. Use `.makescript`")
        return
    
    history = user_scripts[ctx.author.id]
    message = f"**Your Scripts ({len(history)} total)**\n\n"
    for i, script in enumerate(history[-10:], 1):
        message += f"{i}. `{script['filename']}`\n"
    
    await ctx.send(message)

@bot.command(name='commands')
async def list_commands(ctx):
    embed = discord.Embed(
        title="GrimHub Bot Commands",
        description="Lua script generator with AI learning",
        color=0x00ff00
    )
    embed.add_field(name="`.makescript <prompt>`", value="Generate a Lua script", inline=False)
    embed.add_field(name="`.feed` (with .lua file)", value="Feed a script to the AI for learning", inline=False)
    embed.add_field(name="`.history`", value="View your script history", inline=False)
    embed.add_field(name="`.commands`", value="Show this help", inline=False)
    embed.set_footer(text="Scripts are generated using Groq AI")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
