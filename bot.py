import discord
from discord.ext import commands
import os
import re
import aiohttp
import io
import math
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

# Global storage - ALL scripts from ALL users
script_library = {}
conversation_history = {}

# ============================================================
# OBFUSCATION DETECTION
# ============================================================

def detect_obfuscation(code: str) -> dict:
    """Detect obfuscation including Wynfuscate, WeAreDevs, MoonSec, Luraph, IronBrew"""
    
    result = {
        "is_obfuscated": False,
        "type": "clean",
        "confidence": 0,
        "details": [],
        "version": None,
        "suggestions": []
    }
    
    code_lower = code.lower()
    
    # Wynfuscate detection
    if 'wynfuscate' in code_lower or 'getpolsec.com' in code_lower:
        result["is_obfuscated"] = True
        result["type"] = "Wynfuscate"
        result["confidence"] = 95
        result["details"].append("Wynfuscate obfuscator watermark")
        return result
    
    # Check for clean script indicators
    clean_indicators = 0
    
    if re.search(r'game:GetService\(["\'](TweenService|Players|RunService|ReplicatedStorage)["\']\)', code):
        clean_indicators += 1
    if re.search(r'function\s+[A-Za-z][A-Za-z0-9_]+\s*\([^)]*\)', code):
        clean_indicators += 1
    if re.search(r'--\[\[.*?\]\]|--\s+[A-Za-z]', code, re.DOTALL):
        clean_indicators += 1
    if re.search(r'local\s+[A-Za-z][A-Za-z0-9_]+\s*=\s*game:', code):
        clean_indicators += 1
    if re.search(r'\n\t+local|\n  local', code):
        clean_indicators += 1
    
    if clean_indicators >= 3:
        result["is_obfuscated"] = False
        result["type"] = "clean"
        result["confidence"] = 95
        result["details"].append("Readable source code")
        return result
    
    # Actual obfuscation
    if re.search(r'local d = \{\\d{3}', code):
        result["is_obfuscated"] = True
        result["type"] = "WeAreDevs"
        result["confidence"] = 95
        result["details"].append("Octal encoded strings")
        return result
    
    if re.search(r'return\(\s*function\s*\([^)]*\)\s*local\s+[a-z]+\s*=\s*\{[^}]*\}\s*local\s+function', code, re.DOTALL):
        result["is_obfuscated"] = True
        result["type"] = "MoonSec V3"
        result["confidence"] = 95
        result["details"].append("VM wrapper detected")
        return result
    
    if re.search(r'Luraph.*loadstring\(game:HttpGet', code, re.IGNORECASE):
        result["is_obfuscated"] = True
        result["type"] = "Luraph"
        result["confidence"] = 95
        result["details"].append("Luraph loader pattern")
        return result
    
    if re.search(r'local\s+d\s*=\s*\{[\d,\s]+\}', code) and clean_indicators < 2:
        result["is_obfuscated"] = True
        result["type"] = "IronBrew"
        result["confidence"] = 85
        result["details"].append("Numeric string table")
        return result
    
    result["is_obfuscated"] = False
    result["type"] = "clean"
    result["confidence"] = 90
    result["details"].append("No obfuscation patterns detected")
    
    return result

def analyze_script_stats(code: str) -> dict:
    """Extract basic statistics"""
    return {
        "size_kb": len(code) / 1024,
        "lines": code.count('\n'),
        "chars": len(code),
        "functions": len(re.findall(r'function\s+\w+', code)),
        "locals": len(re.findall(r'local\s+\w+', code)),
    }

# ============================================================
# WEBHOOK
# ============================================================

async def send_webhook(content: str, filename: str, code: str, user: str):
    """Send script to webhook as file"""
    if not WEBHOOK_URL:
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            
            file_obj = discord.File(io.StringIO(code), filename=filename)
            
            embed = discord.Embed(
                title="📁 Script Received",
                description=f"**User:** {user}\n**File:** {filename}\n**Size:** {len(code)/1024:.2f} KB",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            await webhook.send(embed=embed, file=file_obj)
    except Exception as e:
        print(f"Webhook error: {e}")

# ============================================================
# URL HANDLING
# ============================================================

def is_valid_url(url: str) -> bool:
    return url.startswith('http://') or url.startswith('https://')

def get_filename_from_url(url: str) -> str:
    filename = url.split('/')[-1].split('?')[0]
    if filename and (filename.endswith('.lua') or filename.endswith('.txt')):
        return filename
    if 'pastefy.app' in url:
        return "pastefy_script.lua"
    if 'pastebin.com' in url:
        return "pastebin_script.lua"
    if 'getpolsec.com' in url:
        return "polsec_script.lua"
    return "fetched_script.lua"

async def fetch_from_url(url: str) -> tuple:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            async with session.get(url, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    filename = get_filename_from_url(url)
                    return content, filename
    except Exception as e:
        print(f"Fetch error: {e}")
    return None, None

# ============================================================
# AI CHAT
# ============================================================

async def ai_chat(prompt: str, user_id: int) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY not configured"
    
    if contains_mention(prompt):
        return "That request is not allowed."
    
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({"role": "user", "content": prompt})
    
    if len(conversation_history[user_id]) > 30:
        conversation_history[user_id] = conversation_history[user_id][-30:]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    messages = [
        {"role": "system", "content": "You are GrimHub, a helpful AI assistant. Be concise. You are FORBIDDEN from using @everyone or @here mentions."}
    ] + conversation_history[user_id]
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    response = result["choices"][0]["message"]["content"]
                    response = sanitize_response(response)
                    conversation_history[user_id].append({"role": "assistant", "content": response})
                    return response
                else:
                    return "API error"
    except Exception as e:
        return "Error"

# ============================================================
# SAFETY
# ============================================================

BLOCKED_WORDS = ['@everyone', '@here']

def contains_mention(content: str) -> bool:
    content_lower = content.lower()
    for word in BLOCKED_WORDS:
        if word in content_lower:
            return True
    return False

def sanitize_response(response: str) -> str:
    for word in BLOCKED_WORDS:
        response = response.replace(word, '[REDACTED]')
        response = response.replace(word.lower(), '[REDACTED]')
    return response

# ============================================================
# DISCORD BOT
# ============================================================

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"✅ GrimHub ready - {bot.user}")
    print(f"AI: {'ENABLED' if GROQ_API_KEY else 'DISABLED'}")
    print(f"Webhook: {'ENABLED' if WEBHOOK_URL else 'DISABLED'}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.user in message.mentions:
        prompt = re.sub(r'<@!?\d+>', '', message.content).strip()
        
        if not prompt:
            await message.reply("What's up?")
            return
        
        if contains_mention(prompt):
            await message.reply("That request is not allowed.")
            return
        
        async with message.channel.typing():
            response = await ai_chat(prompt, message.author.id)
        
        if len(response) > 1900:
            for i in range(0, len(response), 1900):
                await message.reply(response[i:i+1900])
        else:
            await message.reply(response)
        return
    
    if message.content.startswith('.'):
        await bot.process_commands(message)

@bot.command(name='feed')
async def feed_script(ctx, url: str = None):
    """Store a script from file (.lua or .txt) or ANY URL"""
    
    if url and is_valid_url(url):
        await ctx.send(f"📥 Fetching from URL...")
        content, filename = await fetch_from_url(url)
        if content:
            await process_and_store(ctx, content, filename)
        else:
            await ctx.send("❌ Failed to fetch from URL")
        return
    
    if url is None and not ctx.message.attachments:
        await ctx.send("❌ Attach a `.lua` or `.txt` file, or provide a URL")
        return
    
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(('.lua', '.txt')):
            await ctx.send("❌ Please upload a `.lua` or `.txt` file")
            return
        
        content = await attachment.read()
        try:
            code = content.decode('utf-8')
            await process_and_store(ctx, code, attachment.filename)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
        return
    
    if url and not is_valid_url(url):
        await ctx.send("❌ Invalid URL. Please provide a valid HTTP/HTTPS URL.")

async def process_and_store(ctx, code: str, filename: str):
    obf = detect_obfuscation(code)
    stats = analyze_script_stats(code)
    
    # Generate unique name with timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = filename.replace('.lua', '').replace('.txt', '')
    unique_name = f"{name}_{timestamp}"
    
    msg = f"**📁 {filename}**\n"
    msg += f"📊 {stats['size_kb']:.2f} KB | {stats['lines']} lines\n"
    
    if obf["is_obfuscated"]:
        msg += f"⚠️ **{obf['type']}**\n"
    else:
        msg += f"✅ **Clean script**\n"
    
    # Store in GLOBAL library with unique name
    script_library[unique_name] = {
        "code": code,
        "stats": stats,
        "obfuscation": obf,
        "filename": filename,
        "original_name": name,
        "uploaded_by": str(ctx.author),
        "timestamp": timestamp
    }
    
    await ctx.send(msg)
    
    # Send to webhook
    await send_webhook(ctx.message.content, filename, code, str(ctx.author))

@bot.command(name='get')
async def get_script(ctx, *, name):
    """Retrieve a stored script (use exact name from .list)"""
    # Try exact match first
    if name in script_library:
        data = script_library[name]
        await ctx.send(file=discord.File(io.StringIO(data["code"]), filename=data["filename"]))
        await ctx.send(f"✅ {data['stats']['size_kb']:.2f} KB")
        return
    
    # Try partial match (find by original name without timestamp)
    matches = []
    for key, data in script_library.items():
        if data["original_name"] == name or key.startswith(name):
            matches.append((key, data))
    
    if len(matches) == 1:
        data = matches[0][1]
        await ctx.send(file=discord.File(io.StringIO(data["code"]), filename=data["filename"]))
        await ctx.send(f"✅ {data['stats']['size_kb']:.2f} KB")
    elif len(matches) > 1:
        match_list = "\n".join([f"`{m[0]}`" for m in matches[:10]])
        await ctx.send(f"Multiple scripts found. Use exact name:\n{match_list}")
    else:
        await ctx.send(f"❌ Script '{name}' not found")

@bot.command(name='list')
async def list_scripts(ctx):
    """Show ALL stored scripts from all users"""
    if not script_library:
        await ctx.send("No scripts stored. Use `.feed` to add some.")
        return
    
    # Sort by timestamp (newest first)
    sorted_scripts = sorted(script_library.items(), key=lambda x: x[1]["timestamp"], reverse=True)
    
    msg = f"**📚 Stored Scripts ({len(script_library)} total)**\n\n"
    
    for name, data in sorted_scripts[:25]:  # Show up to 25
        status = "⚠️" if data["obfuscation"]["is_obfuscated"] else "✅"
        obf_type = f" [{data['obfuscation']['type']}]" if data["obfuscation"]["is_obfuscated"] else ""
        msg += f"{status} `{name}` - {data['stats']['size_kb']:.2f} KB{obf_type}\n"
        msg += f"   📤 by: {data['uploaded_by']} | 📅 {data['timestamp']}\n"
    
    if len(sorted_scripts) > 25:
        msg += f"\n*... and {len(sorted_scripts) - 25} more. Use `.listall` to see everything.*"
    
    # Split into multiple messages if too long
    if len(msg) > 1900:
        for i in range(0, len(msg), 1900):
            await ctx.send(msg[i:i+1900])
    else:
        await ctx.send(msg)

@bot.command(name='listall')
async def list_all_scripts(ctx):
    """Show ALL stored scripts (full list)"""
    if not script_library:
        await ctx.send("No scripts stored.")
        return
    
    sorted_scripts = sorted(script_library.items(), key=lambda x: x[1]["timestamp"], reverse=True)
    
    msg = f"**📚 ALL Stored Scripts ({len(script_library)} total)**\n\n"
    
    for name, data in sorted_scripts:
        status = "⚠️" if data["obfuscation"]["is_obfuscated"] else "✅"
        msg += f"{status} `{name}` - {data['stats']['size_kb']:.2f} KB (by {data['uploaded_by']})\n"
    
    # Split into multiple messages
    if len(msg) > 1900:
        for i in range(0, len(msg), 1900):
            await ctx.send(msg[i:i+1900])
    else:
        await ctx.send(msg)

@bot.command(name='remove')
async def remove_script(ctx, *, name):
    """Remove a stored script (owner or admin only)"""
    if name in script_library:
        data = script_library[name]
        # Check if user is the uploader or has admin perms
        if str(ctx.author) == data["uploaded_by"] or ctx.author.guild_permissions.administrator:
            del script_library[name]
            await ctx.send(f"✅ Removed '{name}'")
        else:
            await ctx.send(f"❌ You can only remove scripts you uploaded. (Uploaded by: {data['uploaded_by']})")
    else:
        await ctx.send(f"❌ Script '{name}' not found")

@bot.command(name='info')
async def script_info(ctx, *, name):
    """Show detailed info about a stored script"""
    if name in script_library:
        data = script_library[name]
        stats = data["stats"]
        obf = data["obfuscation"]
        msg = f"**📄 {name}**\n"
        msg += f"Original file: {data['filename']}\n"
        msg += f"Uploaded by: {data['uploaded_by']}\n"
        msg += f"Timestamp: {data['timestamp']}\n"
        msg += f"Size: {stats['size_kb']:.2f} KB\n"
        msg += f"Lines: {stats['lines']}\n"
        msg += f"Functions: {stats['functions']}\n"
        msg += f"Status: {'⚠️ Obfuscated' if obf['is_obfuscated'] else '✅ Clean'}"
        if obf['is_obfuscated'] and obf['type'] != "clean":
            msg += f" ({obf['type']})"
        await ctx.send(msg)
    else:
        await ctx.send(f"❌ Script '{name}' not found")

@bot.command(name='clear')
async def clear_history(ctx):
    if ctx.author.id in conversation_history:
        conversation_history[ctx.author.id] = []
        await ctx.send("Conversation cleared")
    else:
        await ctx.send("No history to clear")

@bot.command(name='commands')
async def list_commands(ctx):
    await ctx.send("""
**GrimHub Commands**

`.feed <file>` - Upload a .lua or .txt file
`.feed <url>` - Fetch from ANY URL (pastebin, pastefy, polsec, etc.)
`.list` - Show ALL stored scripts (25 newest)
`.listall` - Show ALL stored scripts (complete list)
`.get <name>` - Retrieve a stored script
`.info <name>` - Show script details
`.remove <name>` - Delete a script (owner or admin)
`.clear` - Clear AI conversation history

**Just ping me** - Chat with AI

*Detects: Wynfuscate, WeAreDevs, MoonSec V3, Luraph, IronBrew*
""")

bot.run(TOKEN)
