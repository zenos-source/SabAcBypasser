import discord
from discord.ext import commands
import os
import re
import aiohttp
import io
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

script_library = {}
conversation_history = {}

def is_supported_url(url: str) -> bool:
    """Support all pastebin, pastefy, and raw URLs"""
    url_lower = url.lower()
    return any(x in url_lower for x in [
        'pastebin.com/raw',
        'pastefy.app',
        'raw.githubusercontent.com',
        'gist.githubusercontent.com',
        'raw.',
        'paste.gg'
    ])

def extract_raw_url(url: str) -> str:
    """Convert various URL formats to raw content URL"""
    if '/raw' in url:
        return url
    if 'pastefy.app' in url:
        if not url.endswith('/raw'):
            if url.endswith('/'):
                return url + 'raw'
            return url + '/raw'
    if 'pastebin.com' in url and '/raw' not in url:
        url = url.replace('pastebin.com', 'pastebin.com/raw')
    return url

async def fetch_from_url(url: str) -> tuple:
    """Fetch content from any URL"""
    raw_url = extract_raw_url(url)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(raw_url, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    filename = raw_url.split('/')[-1].split('?')[0]
                    if not filename.endswith(('.lua', '.txt')):
                        filename = "script.lua"
                    return content, filename
    except Exception as e:
        print(f"Fetch error: {e}")
    return None, None

def detect_obfuscation(code: str) -> dict:
    """Detect if script is actually obfuscated - not just large"""
    
    result = {
        "is_obfuscated": False,
        "type": "clean",
        "confidence": 0,
        "details": [],
        "version": None,
        "suggestions": []
    }
    
    # ============================================================
    # 1. FIRST - Check for CLEAN script patterns (readable code)
    # ============================================================
    
    clean_indicators = 0
    
    # Proper Roblox API usage
    if re.search(r'game:GetService\(["\'](TweenService|Players|RunService|ReplicatedStorage)["\']\)', code):
        clean_indicators += 1
    
    # Proper function definitions with readable names
    if re.search(r'function\s+[A-Za-z][A-Za-z0-9_]+\s*\([^)]*\)', code):
        clean_indicators += 1
    
    # Comments (real comments, not obfuscation)
    if re.search(r'--\[\[.*?\]\]|--\s+[A-Za-z]', code, re.DOTALL):
        clean_indicators += 1
    
    # Proper local variable declarations
    if re.search(r'local\s+[A-Za-z][A-Za-z0-9_]+\s*=\s*game:', code):
        clean_indicators += 1
    
    # Multi-line functions with proper structure
    if re.search(r'function\s+[A-Za-z_]+\s*\(\s*\)\s*\n\s+local', code):
        clean_indicators += 1
    
    # Readable variable names (not single letters)
    var_names = re.findall(r'local\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
    if var_names:
        avg_len = sum(len(v) for v in var_names[:50]) / min(len(var_names), 50)
        if avg_len > 3:
            clean_indicators += 1
    
    # If it has 3+ clean indicators, it's clean source code
    if clean_indicators >= 3:
        result["is_obfuscated"] = False
        result["type"] = "clean"
        result["confidence"] = 95
        result["details"].append("Readable source code with proper structure")
        return result
    
    # ============================================================
    # 2. Check for ACTUAL obfuscation (encoded strings, VM patterns)
    # ============================================================
    
    # WeAreDevs: octal strings
    if re.search(r'\\\d{3}', code) and re.search(r'local d = \{\\d{3}', code):
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
    
    # Luraph: loadstring pattern
    if re.search(r'loadstring\(game:HttpGet\(["\'][^"\']+["\']\)\)', code) and 'Luraph' in code:
        result["is_obfuscated"] = True
        result["type"] = "Luraph"
        result["confidence"] = 95
        result["details"].append("Luraph loader pattern")
        return result
    
    # IronBrew: numeric string table (only if small and no readable code)
    if re.search(r'local\s+d\s*=\s*\{[\d,\s]+\}', code) and len(code) < 50000 and clean_indicators < 2:
        result["is_obfuscated"] = True
        result["type"] = "IronBrew"
        result["confidence"] = 85
        result["details"].append("Numeric string table")
        return result
    
    # ============================================================
    # 3. DEFAULT: Assume clean if no obfuscation patterns
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
        "services": list(set(re.findall(r'game:GetService\(["\'](\w+)["\']\)', code))),
    }

async def ai_chat(prompt: str, user_id: int) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY not configured"
    
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({"role": "user", "content": prompt})
    
    if len(conversation_history[user_id]) > 30:
        conversation_history[user_id] = conversation_history[user_id][-30:]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": "You are GrimHub, a helpful AI assistant. Be friendly and concise. You help with Lua scripting, Roblox, and general questions."}
    ] + conversation_history[user_id]
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 500
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    response = result["choices"][0]["message"]["content"]
                    conversation_history[user_id].append({"role": "assistant", "content": response})
                    return response
                else:
                    return f"API error: {resp.status}"
    except Exception as e:
        return f"Error: {str(e)}"

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"✅ GrimHub ready - {bot.user}")
    print(f"AI: {'ENABLED' if GROQ_API_KEY else 'DISABLED'}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # AI Chat when pinged
    if bot.user in message.mentions:
        prompt = re.sub(r'<@!?\d+>', '', message.content).strip()
        if not prompt:
            await message.reply("What's up?")
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
    """Store a script from file, attachment, or URL"""
    
    # Handle URL
    if url:
        if is_supported_url(url):
            await ctx.send(f"📥 Fetching from URL...")
            content, filename = await fetch_from_url(url)
            if content:
                await process_and_store(ctx, content, filename)
            else:
                await ctx.send("❌ Failed to fetch from URL")
            return
        else:
            await ctx.send("❌ Supported: pastebin.com/raw, pastefy.app, raw.githubusercontent.com")
            return
    
    # Handle attachment
    if not ctx.message.attachments:
        await ctx.send("❌ Attach a `.lua` or `.txt` file, or provide a URL")
        return
    
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

async def process_and_store(ctx, code: str, filename: str):
    """Process, detect obfuscation, and store script"""
    
    obf = detect_obfuscation(code)
    stats = analyze_script_stats(code)
    size_kb = stats["size_kb"]
    
    msg = f"**📁 {filename}**\n"
    msg += f"📊 {size_kb:.2f} KB | {stats['lines']} lines | {stats['functions']} functions\n"
    
    if obf["is_obfuscated"]:
        msg += f"⚠️ **{obf['type']}** (confidence: {obf['confidence']}%)\n"
        if obf["details"]:
            msg += f"   Signs: {', '.join(obf['details'][:2])}\n"
    else:
        msg += f"✅ **Clean Script** - Readable source code\n"
        if stats["services"]:
            msg += f"   Services: {', '.join(stats['services'][:5])}\n"
    
    # Store in library
    name = filename.replace('.lua', '').replace('.txt', '')
    script_library[name] = {
        "code": code,
        "stats": stats,
        "obfuscation": obf,
        "filename": filename,
        "timestamp": datetime.now().isoformat()
    }
    
    await ctx.send(msg)

@bot.command(name='get')
async def get_script(ctx, *, name):
    """Retrieve a stored script"""
    if name in script_library:
        data = script_library[name]
        size_kb = data["stats"]["size_kb"]
        await ctx.send(file=discord.File(io.StringIO(data["code"]), filename=data["filename"]))
        await ctx.send(f"✅ {size_kb:.2f} KB")
    else:
        await ctx.send(f"❌ Script '{name}' not found")

@bot.command(name='list')
async def list_scripts(ctx):
    if not script_library:
        await ctx.send("No scripts stored")
        return
    
    msg = f"**Stored Scripts ({len(script_library)} total)**\n\n"
    for name, data in list(script_library.items())[:20]:
        obf = "⚠️" if data["obfuscation"]["is_obfuscated"] else "✅"
        msg += f"{obf} `{name}.lua` - {data['stats']['size_kb']:.2f} KB"
        if data["obfuscation"]["is_obfuscated"]:
            msg += f" [{data['obfuscation']['type']}]"
        msg += "\n"
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
        if obf['is_obfuscated']:
            msg += f" ({obf['type']})"
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

`.feed <file>` - Upload a .lua/.txt file
`.feed <url>` - Fetch from pastebin.com/raw, pastefy.app, or raw URL
`.get <name>` - Retrieve a stored script
`.list` - Show all stored scripts
`.info <name>` - Show script details
`.remove <name>` - Delete a script
`.clear` - Clear AI conversation history

**Just ping me** - Chat with AI
""")

bot.run(TOKEN)
