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

script_library = {}
conversation_history = {}

# ============================================================
# OBFUSCATION DETECTION
# ============================================================

def detect_obfuscation(code: str) -> dict:
    """Detect actual obfuscation - not just entropy"""
    
    result = {
        "is_obfuscated": False,
        "type": "clean",
        "confidence": 0,
        "details": [],
        "version": None,
        "suggestions": []
    }
    
    # ============================================================
    # 1. FIRST - Check for CLEAN script indicators
    # ============================================================
    
    clean_indicators = 0
    
    # Proper Roblox API usage
    if re.search(r'game:GetService\(["\'](TweenService|Players|RunService|ReplicatedStorage)["\']\)', code):
        clean_indicators += 1
    
    # Proper function definitions with readable names
    if re.search(r'function\s+[A-Za-z][A-Za-z0-9_]+\s*\([^)]*\)', code):
        clean_indicators += 1
    
    # Comments explaining code
    if re.search(r'--\[\[.*?\]\]|--\s+[A-Za-z]', code, re.DOTALL):
        clean_indicators += 1
    
    # Proper local variable declarations
    if re.search(r'local\s+[A-Za-z][A-Za-z0-9_]+\s*=\s*game:', code):
        clean_indicators += 1
    
    # Indentation (tabs or spaces)
    if re.search(r'\n\t+local|\n  local', code):
        clean_indicators += 1
    
    # If it has 3+ clean indicators, it's CLEAN source code
    if clean_indicators >= 3:
        result["is_obfuscated"] = False
        result["type"] = "clean"
        result["confidence"] = 95
        result["details"].append("Readable source code")
        return result
    
    # ============================================================
    # 2. Check for ACTUAL obfuscation
    # ============================================================
    
    # WeAreDevs: octal strings in string table
    if re.search(r'local d = \{\\d{3}', code):
        result["is_obfuscated"] = True
        result["type"] = "WeAreDevs"
        result["confidence"] = 95
        result["details"].append("Octal encoded strings")
        return result
    
    # MoonSec V3: VM wrapper pattern
    if re.search(r'return\(\s*function\s*\([^)]*\)\s*local\s+[a-z]+\s*=\s*\{[^}]*\}\s*local\s+function', code, re.DOTALL):
        result["is_obfuscated"] = True
        result["type"] = "MoonSec V3"
        result["confidence"] = 95
        result["details"].append("VM wrapper detected")
        return result
    
    # Luraph: specific loader pattern
    if re.search(r'Luraph.*loadstring\(game:HttpGet', code, re.IGNORECASE):
        result["is_obfuscated"] = True
        result["type"] = "Luraph"
        result["confidence"] = 95
        result["details"].append("Luraph loader pattern")
        return result
    
    # IronBrew: numeric string table (only if no clean indicators)
    if re.search(r'local\s+d\s*=\s*\{[\d,\s]+\}', code) and clean_indicators < 2:
        result["is_obfuscated"] = True
        result["type"] = "IronBrew"
        result["confidence"] = 85
        result["details"].append("Numeric string table")
        return result
    
    # ============================================================
    # 3. DEFAULT: Assume clean
    # ============================================================
    
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
# UNIVERSAL URL HANDLING - Supports ANY raw URL
# ============================================================

def is_valid_url(url: str) -> bool:
    """Check if string looks like a URL"""
    return url.startswith('http://') or url.startswith('https://')

def get_filename_from_url(url: str) -> str:
    """Extract filename from URL or generate one"""
    # Try to get from URL path
    filename = url.split('/')[-1].split('?')[0]
    if filename and (filename.endswith('.lua') or filename.endswith('.txt')):
        return filename
    # Default names for different domains
    if 'paste.rs' in url:
        return "pasters_script.lua"
    if 'polsec' in url or 'api.jnkie.com' in url:
        return "script.lua"
    if 'pastefy.app' in url:
        return "pastefy_script.lua"
    if 'pastebin.com' in url:
        return "pastebin_script.lua"
    # Generic fallback
    return "fetched_script.lua"

async def fetch_from_url(url: str) -> tuple:
    """Fetch content from ANY URL"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            async with session.get(url, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    filename = get_filename_from_url(url)
                    return content, filename
                else:
                    print(f"HTTP {resp.status} from {url}")
    except Exception as e:
        print(f"Fetch error from {url}: {e}")
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
    print(f"URL Support: ANY raw URL (paste.rs, polsec, junkie, pastebin, pastefy, etc.)")

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
    """Store a script from file (.lua/.txt) or ANY URL"""
    
    # Handle URL - ANY valid HTTP/HTTPS URL
    if url and is_valid_url(url):
        await ctx.send(f"📥 Fetching from URL...")
        content, filename = await fetch_from_url(url)
        if content:
            await process_and_store(ctx, content, filename)
        else:
            await ctx.send("❌ Failed to fetch from URL. Make sure it's a valid raw content URL.")
        return
    
    # Handle attachment
    if url is None and not ctx.message.attachments:
        await ctx.send("❌ Attach a `.lua` or `.txt` file, or provide a URL (paste.rs, polsec, junkie, pastebin, etc.)")
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
    
    # If we got here, user provided a URL but it wasn't valid
    if url and not is_valid_url(url):
        await ctx.send("❌ Invalid URL. Please provide a valid HTTP/HTTPS URL.")

async def process_and_store(ctx, code: str, filename: str):
    obf = detect_obfuscation(code)
    stats = analyze_script_stats(code)
    
    msg = f"**📁 {filename}**\n"
    msg += f"📊 {stats['size_kb']:.2f} KB | {stats['lines']} lines\n"
    
    if obf["is_obfuscated"]:
        msg += f"⚠️ **Obfuscated**\n"
    else:
        msg += f"✅ **Clean script**\n"
    
    name = filename.replace('.lua', '').replace('.txt', '')
    script_library[name] = {
        "code": code,
        "stats": stats,
        "obfuscation": obf,
        "filename": filename
    }
    
    await ctx.send(msg)
    
    # Send to webhook
    await send_webhook(ctx.message.content, filename, code, str(ctx.author))

@bot.command(name='get')
async def get_script(ctx, *, name):
    """Retrieve a stored script"""
    if name in script_library:
        data = script_library[name]
        await ctx.send(file=discord.File(io.StringIO(data["code"]), filename=data["filename"]))
        await ctx.send(f"✅ {data['stats']['size_kb']:.2f} KB")
    else:
        await ctx.send(f"❌ Script '{name}' not found")

@bot.command(name='list')
async def list_scripts(ctx):
    if not script_library:
        await ctx.send("No scripts stored")
        return
    
    msg = f"**Stored Scripts ({len(script_library)} total)**\n\n"
    for name, data in list(script_library.items())[:20]:
        status = "⚠️" if data["obfuscation"]["is_obfuscated"] else "✅"
        msg += f"{status} `{name}.lua` - {data['stats']['size_kb']:.2f} KB\n"
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
        data = script_library[name]
        stats = data["stats"]
        obf = data["obfuscation"]
        msg = f"**{name}.lua**\n"
        msg += f"Size: {stats['size_kb']:.2f} KB\n"
        msg += f"Lines: {stats['lines']}\n"
        msg += f"Functions: {stats['functions']}\n"
        msg += f"Status: {'⚠️ Obfuscated' if obf['is_obfuscated'] else '✅ Clean'}"
        await ctx.send(msg)
    else:
        await ctx.send(f"Script '{name}' not found")

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
`.feed <url>` - Fetch from ANY URL (paste.rs, polsec, junkie, pastebin, pastefy, raw)
`.get <name>` - Retrieve a stored script
`.list` - Show all stored scripts
`.info <name>` - Show script details
`.remove <name>` - Delete a script
`.clear` - Clear AI conversation history

**Just ping me** - Chat with AI

*Supports any HTTP/HTTPS raw content URL*
""")

bot.run(TOKEN)
