import discord
from discord.ext import commands
import os
import aiohttp
import io
import re
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
learned_patterns = {}

def detect_obfuscation(code: str) -> dict:
    """Detect if script is obfuscated and what type"""
    result = {
        "is_obfuscated": False,
        "type": "clean",
        "confidence": 0,
        "details": []
    }
    
    # Check for common obfuscation patterns
    patterns = {
        "wearedevs": {
            "pattern": r'local d = \{\\d{3}|wearedevs\.net',
            "type": "WeAreDevs",
            "confidence": 95
        },
        "luraph": {
            "pattern": r'Luraph|loadstring\(game:HttpGet',
            "type": "Luraph",
            "confidence": 90
        },
        "moonsec": {
            "pattern": r'local\s+\w+\s*=\s*\{[^}]*["\'][^"\']*["\']',
            "type": "MoonSec",
            "confidence": 85
        },
        "ironbrew": {
            "pattern": r'ironbrew|getfenv.*setfenv|string\.char\(0x',
            "type": "IronBrew",
            "confidence": 90
        },
        "hex_strings": {
            "pattern": r'\\x[0-9a-f]{2}|string\.char\(\d+',
            "type": "Hex/String Obfuscation",
            "confidence": 70
        },
        "long_strings": {
            "pattern": r'["\'][A-Za-z0-9+/]{100,}=*["\']',
            "type": "Base64/Encoded Strings",
            "confidence": 75
        }
    }
    
    for key, p in patterns.items():
        if re.search(p["pattern"], code, re.IGNORECASE):
            result["is_obfuscated"] = True
            result["type"] = p["type"]
            result["confidence"] = p["confidence"]
            result["details"].append(f"Found {key} pattern")
            break
    
    # Check variable name randomness
    var_names = re.findall(r'local\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
    single_letter = sum(1 for v in var_names if len(v) == 1)
    if len(var_names) > 10 and single_letter / len(var_names) > 0.5:
        result["is_obfuscated"] = True
        result["details"].append(f"High single-letter variable ratio: {single_letter}/{len(var_names)}")
    
    # Check line length (obfuscated often has very long lines)
    lines = code.split('\n')
    long_lines = sum(1 for l in lines if len(l) > 500)
    if long_lines > 5:
        result["is_obfuscated"] = True
        result["details"].append(f"Very long lines detected: {long_lines} lines >500 chars")
    
    return result

def analyze_script(code: str) -> dict:
    """Extract useful info from script for learning"""
    analysis = {
        "size_kb": len(code) / 1024,
        "lines": code.count('\n'),
        "functions": len(re.findall(r'function\s+\w+', code)),
        "locals": len(re.findall(r'local\s+\w+', code)),
        "remotes": len(re.findall(r'RemoteEvent|RemoteFunction|FireServer|OnClientEvent', code)),
        "services": re.findall(r'game:GetService\(["\'](\w+)["\']\)', code),
        "gui_elements": len(re.findall(r'Instance\.new\(["\'](Frame|TextButton|ScreenGui|ScrollingFrame)["\']', code)),
        "tween_usage": 'TweenService' in code,
        "http_requests": len(re.findall(r'HttpGet|HttpPost|request\(', code)),
        "unique_services": []
    }
    
    analysis["unique_services"] = list(set(analysis["services"]))
    return analysis

async def ai_analyze(code: str, analysis: dict, obfuscation: dict) -> str:
    """Use AI to provide deeper analysis"""
    if not GROQ_API_KEY:
        return None
    
    prompt = f"""Analyze this Lua script and provide:
1. What it does (main purpose)
2. Key features
3. Complexity level
4. Any concerns or issues

Script info:
- Size: {analysis['size_kb']:.2f} KB
- Lines: {analysis['lines']}
- Functions: {analysis['functions']}
- Services used: {', '.join(analysis['unique_services'][:10])}
- Obfuscated: {obfuscation['is_obfuscated']} ({obfuscation['type'] if obfuscation['is_obfuscated'] else 'clean'})

First 1500 chars:
{code[:1500]}"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 800
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]
    except:
        pass
    return None

async def fetch_from_url(url: str) -> tuple:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    filename = url.split('/')[-1]
                    if not filename.endswith(('.lua', '.txt')):
                        filename = filename.split('?')[0]
                        if not filename.endswith(('.lua', '.txt')):
                            filename = "script.lua"
                    return content, filename
    except:
        pass
    return None, None

def is_supported_url(url: str) -> bool:
    return any(x in url for x in ['pastefy.app/raw', 'pastebin.com/raw', 'raw.'])

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"✅ GrimHub ready - {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.user in message.mentions:
        prompt = re.sub(r'<@!?\d+>', '', message.content).strip()
        if not prompt:
            await message.reply("What's up?")
            return
        
        async with message.channel.typing():
            response = await ai_chat(prompt, message.author.id)
        
        for i in range(0, len(response), 1900):
            await message.reply(response[i:i+1900])
        return
    
    if message.content.startswith('.'):
        await bot.process_commands(message)

@bot.command(name='feed')
async def feed_script(ctx, url: str = None):
    """Store and analyze a script from file or URL"""
    
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
            await ctx.send("❌ Supported: pastebin.com/raw, pastefy.app/.../raw")
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
    """Process, analyze, and store the script"""
    
    # Detect obfuscation
    obfuscation = detect_obfuscation(code)
    analysis = analyze_script(code)
    size_kb = analysis["size_kb"]
    
    # Build response
    msg = f"**Stored: {filename}**\n"
    msg += f"📊 Size: {size_kb:.2f} KB | Lines: {analysis['lines']}\n"
    
    if obfuscation["is_obfuscated"]:
        msg += f"⚠️ **Obfuscation Detected!**\n"
        msg += f"   Type: {obfuscation['type']}\n"
        msg += f"   Confidence: {obfuscation['confidence']}%\n"
        if obfuscation["details"]:
            msg += f"   Signs: {', '.join(obfuscation['details'][:2])}\n"
    else:
        msg += f"✅ **Clean Script** - No obfuscation detected\n"
    
    msg += f"📦 Functions: {analysis['functions']} | Locals: {analysis['locals']}\n"
    msg += f"🔌 Services: {', '.join(analysis['unique_services'][:5])}\n"
    
    if analysis["remotes"] > 0:
        msg += f"📡 Remote events/functions: {analysis['remotes']}\n"
    
    # Store in library
    name = filename.replace('.lua', '').replace('.txt', '')
    script_library[name] = {
        "code": code,
        "analysis": analysis,
        "obfuscation": obfuscation,
        "filename": filename,
        "timestamp": datetime.now().isoformat()
    }
    
    await ctx.send(msg)
    
    # AI Analysis for clean scripts (optional)
    if not obfuscation["is_obfuscated"] and GROQ_API_KEY and size_kb < 100:
        await ctx.send("🤖 Analyzing script content...")
        ai_summary = await ai_analyze(code, analysis, obfuscation)
        if ai_summary:
            await ctx.send(f"📝 **AI Analysis:**\n{ai_summary[:1500]}")

@bot.command(name='get')
async def get_script(ctx, *, name):
    """Retrieve a stored script"""
    if name in script_library:
        data = script_library[name]
        await ctx.send(file=discord.File(io.StringIO(data["code"]), filename=data["filename"]))
        await ctx.send(f"✅ {data['filename']} ({data['analysis']['size_kb']:.2f} KB)")
    else:
        await ctx.send(f"❌ Script '{name}' not found")

@bot.command(name='analyze')
async def analyze_script_cmd(ctx, *, name):
    """Analyze a stored script without retrieving it"""
    if name in script_library:
        data = script_library[name]
        obf = data["obfuscation"]
        analysis = data["analysis"]
        
        msg = f"**Analysis: {data['filename']}**\n"
        msg += f"📊 Size: {analysis['size_kb']:.2f} KB | Lines: {analysis['lines']}\n"
        msg += f"🔍 Obfuscated: {obf['is_obfuscated']}\n"
        if obf['is_obfuscated']:
            msg += f"   Type: {obf['type']} (confidence {obf['confidence']}%)\n"
        msg += f"📦 Functions: {analysis['functions']} | Locals: {analysis['locals']}\n"
        msg += f"🔌 Services: {', '.join(analysis['unique_services'][:8])}\n"
        await ctx.send(msg)
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
        msg += f"{obf} `{name}.lua` - {data['analysis']['size_kb']:.2f} KB\n"
    await ctx.send(msg)

@bot.command(name='remove')
async def remove_script(ctx, *, name):
    if name in script_library:
        del script_library[name]
        await ctx.send(f"Removed '{name}'")
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
`.feed <file>` - Store a .lua/.txt file
`.feed <url>` - Fetch from pastebin.com/raw or pastefy.app/.../raw
`.get <name>` - Retrieve a script
`.analyze <name>` - Analyze script without downloading
`.list` - Show all stored scripts
`.remove <name>` - Delete a script
`.clear` - Clear AI conversation
`.commands` - Show this help

**Just ping me** - Chat with AI
""")

async def ai_chat(prompt: str, user_id: int) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY not configured"
    
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({"role": "user", "content": prompt})
    
    if len(conversation_history[user_id]) > 30:
        conversation_history[user_id] = conversation_history[user_id][-30:]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
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

bot.run(TOKEN)
