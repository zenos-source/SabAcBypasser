import discord
from discord.ext import commands
import os
import re
import aiohttp
import io
import json
import base64
import zlib
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

# ============================================================
# ADVANCED OBFUSCATION DETECTION (Synthesized from your research)
# ============================================================

def detect_obfuscation(code: str) -> dict:
    """Detect obfuscator type using patterns from De4Lua, LuraphDeobfuscator, and AC analysis"""
    
    result = {
        "is_obfuscated": False,
        "type": "clean",
        "confidence": 0,
        "details": [],
        "version": None,
        "suggestions": []
    }
    
    code_lower = code.lower()
    code_first_5k = code[:5000]
    
    # ============================================================
    # 1. LUARPH / LURAPH (VM-based - hardest)
    # ============================================================
    luraph_patterns = [
        (r'Luraph', "Luraph string present", 100),
        (r'vmp\s*\.\s*luraph', "VMP wrapper", 95),
        (r'Luraph\s*v\d+\.\d+', "Version signature", 100),
        (r'local\s+[a-z_]+\s*=\s*loadstring\(game:HttpGet\(["\'][^"\']+["\']\)\)', "Luraph loader pattern", 90),
        (r'while\s+true\s+do\s+pcall\(function\(\)', "Luraph VM loop", 85),
        (r'getfenv\(\)\.\["[^"]+"\]\s*=\s*function', "Luraph env hook", 85),
    ]
    
    for pattern, desc, conf in luraph_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            result["is_obfuscated"] = True
            result["type"] = "Luraph"
            result["confidence"] = max(result["confidence"], conf)
            result["details"].append(desc)
            # Try to extract version
            version_match = re.search(r'Luraph\s*v(\d+\.\d+\.?\d*)', code, re.IGNORECASE)
            if version_match:
                result["version"] = version_match.group(1)
            break
    
    # ============================================================
    # 2. MOONSEC V3 (VM-based)
    # ============================================================
    moonsec_patterns = [
        (r'local\s+[a-z_]\s*=\s*\{\s*["\'][^"\']*["\']', "String table", 85),
        (r'while\s+[^d]+\s+do\s+.*?d\[[^\]]+\]\s*=\s*d\[[^\]]+\]', "Swap pattern", 90),
        (r'return\s*\(\s*function\s*\([^)]*\)\s*\.\.\.\s*end\s*\)\s*\(\.\.\.\)', "Moonsec wrapper", 95),
        (r'local\s+function\s+[a-z_]+\s*\(\s*\)\s*return\s+function\([^)]*\)', "Moonsec VM loader", 90),
        (r'moonsec', "Moonsec string", 100),
        (r'moon[\s_-]?sec', "Moonsec variant", 95),
        (r'PSU\s*v?\d+', "PSU (Moonsec variant)", 90),
    ]
    
    for pattern, desc, conf in moonsec_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            result["is_obfuscated"] = True
            result["type"] = "MoonSec V3"
            result["confidence"] = max(result["confidence"], conf)
            result["details"].append(desc)
            # Try to extract version
            version_match = re.search(r'Moonsec\s*v?(\d+\.?\d*)', code, re.IGNORECASE)
            if version_match:
                result["version"] = version_match.group(1)
            break
    
    # ============================================================
    # 3. IRONBREW / IRONBREW 2
    # ============================================================
    ironbrew_patterns = [
        (r'ironbrew', "Ironbrew string", 100),
        (r'ib2', "IronBrew 2", 95),
        (r'getfenv\(\)\._G', "IronBrew env", 85),
        (r'local\s+[a-z_]+\s*=\s*\{[\d,\s]+\}', "IronBrew string table", 80),
        (r'syn\.request.*getfenv', "IronBrew HTTP pattern", 85),
        (r'getfenv\(\)\.\["[^"]+"\]\s*=\s*nil', "IronBrew cleanup", 80),
    ]
    
    for pattern, desc, conf in ironbrew_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            result["is_obfuscated"] = True
            result["type"] = "IronBrew"
            result["confidence"] = max(result["confidence"], conf)
            result["details"].append(desc)
            break
    
    # ============================================================
    # 4. PROMETHEUS
    # ============================================================
    prometheus_patterns = [
        (r'prometheus', "Prometheus string", 100),
        (r'prom[-_]?obf', "Prometheus variant", 90),
        (r'deob\.pipeline', "Prometheus deob pipeline", 85),
        (r'ConstantArrayDecode', "Prometheus step", 85),
        (r'UndoVmify', "Prometheus VM step", 85),
    ]
    
    for pattern, desc, conf in prometheus_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            result["is_obfuscated"] = True
            result["type"] = "Prometheus"
            result["confidence"] = max(result["confidence"], conf)
            result["details"].append(desc)
            break
    
    # ============================================================
    # 5. WEAREDEVS
    # ============================================================
    wearedevs_patterns = [
        (r'wearedevs\.net/obfuscator', "WeAreDevs header", 100),
        (r'local d = \{\\d{3}', "Octal string table", 95),
        (r'return\(function\([^)]*\)[^;]*end\)\.\.\.\)', "WeAreDevs wrapper", 90),
    ]
    
    for pattern, desc, conf in wearedevs_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            result["is_obfuscated"] = True
            result["type"] = "WeAreDevs"
            result["confidence"] = max(result["confidence"], conf)
            result["details"].append(desc)
            break
    
    # ============================================================
    # 6. LUARMOR
    # ============================================================
    luarmor_patterns = [
        (r'luarmor', "Luarmor string", 100),
        (r'api\.luarmor\.net', "Luarmor API", 95),
        (r'luarmor\s+premium', "Luarmor premium", 95),
    ]
    
    for pattern, desc, conf in luarmor_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            result["is_obfuscated"] = True
            result["type"] = "Luarmor"
            result["confidence"] = max(result["confidence"], conf)
            result["details"].append(desc)
            break
    
    # ============================================================
    # 7. GENERIC DETECTION (HEURISTICS)
    # ============================================================
    
    # If not detected yet, run heuristics
    if not result["is_obfuscated"]:
        
        # Check for VM pattern (long strings + weird assignments)
        if len(re.findall(r'[a-z_]\s*=\s*[0-9a-f]{16,}', code)) > 5:
            result["is_obfuscated"] = True
            result["type"] = "VM Obfuscator"
            result["confidence"] = 70
            result["details"].append("Long hex/number assignments (VM pattern)")
        
        # Check for excessive line length
        lines = code.split('\n')
        long_lines = sum(1 for l in lines if len(l) > 800)
        if long_lines > 3:
            result["is_obfuscated"] = True
            result["type"] = "VM Obfuscator"
            result["confidence"] = 75
            result["details"].append(f"Very long lines ({long_lines} >800 chars)")
        
        # Check for base64-like strings
        b64_strings = re.findall(r'["\'][A-Za-z0-9+/]{100,}={0,2}["\']', code)
        if len(b64_strings) > 2:
            result["is_obfuscated"] = True
            result["type"] = "Encoded Obfuscator"
            result["confidence"] = 70
            result["details"].append(f"Base64-like strings ({len(b64_strings)})")
        
        # Check for high single-letter variable ratio
        var_names = re.findall(r'local\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        if var_names:
            single_letter = sum(1 for v in var_names if len(v) == 1)
            ratio = single_letter / len(var_names)
            if ratio > 0.6:
                result["is_obfuscated"] = True
                result["type"] = "Variable Rename Obfuscator"
                result["confidence"] = 65
                result["details"].append(f"High single-letter var ratio ({ratio:.0%})")
    
    # Add educational suggestions
    if result["is_obfuscated"]:
        result["suggestions"].append("Use a sandboxed environment for analysis")
        if result["type"] in ["MoonSec V3", "Luraph"]:
            result["suggestions"].append("VM-based - requires devirtualization")
        elif result["type"] in ["WeAreDevs", "IronBrew"]:
            result["suggestions"].append("String table extraction may recover source")
    
    return result

def analyze_script_stats(code: str) -> dict:
    """Extract basic statistics"""
    return {
        "size_kb": len(code) / 1024,
        "lines": code.count('\n'),
        "chars": len(code),
        "functions": len(re.findall(r'function\s+\w+', code)),
        "locals": len(re.findall(r'local\s+\w+', code)),
        "remotes": len(re.findall(r'RemoteEvent|RemoteFunction|FireServer|OnClientEvent', code)),
        "services": list(set(re.findall(r'game:GetService\(["\'](\w+)["\']\)', code))),
    }

async def fetch_from_url(url: str) -> tuple:
    """Fetch content from URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    filename = url.split('/')[-1].split('?')[0]
                    if not filename.endswith(('.lua', '.txt')):
                        filename = "script.lua"
                    return content, filename
    except:
        pass
    return None, None

def is_supported_url(url: str) -> bool:
    return any(x in url for x in ['pastebin.com/raw', 'pastefy.app/raw', 'raw.githubusercontent', 'gist.githubusercontent'])

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"✅ GrimHub ready - {bot.user}")
    print(f"Obfuscation detection loaded - supporting: Luraph, MoonSec, IronBrew, Prometheus, WeAreDevs, Luarmor")

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
            await ctx.send("❌ Supported: pastebin.com/raw, pastefy.app/.../raw, raw.githubusercontent.com")
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
    
    # Detect obfuscation
    obf = detect_obfuscation(code)
    stats = analyze_script_stats(code)
    
    # Build response
    msg = f"**📁 {filename}**\n"
    msg += f"📊 {stats['size_kb']:.2f} KB | {stats['lines']} lines | {stats['functions']} functions\n"
    
    if obf["is_obfuscated"]:
        msg += f"⚠️ **{obf['type']}** (confidence: {obf['confidence']}%)\n"
        if obf["version"]:
            msg += f"   Version: {obf['version']}\n"
        if obf["details"]:
            msg += f"   Signs: {', '.join(obf['details'][:2])}\n"
        if obf["suggestions"]:
            msg += f"   💡 {obf['suggestions'][0]}\n"
    else:
        msg += f"✅ **Clean Script** - No obfuscation detected\n"
        if stats["services"]:
            msg += f"   Services: {', '.join(stats['services'][:5])}\n"
    
    # Store
    name = filename.replace('.lua', '').replace('.txt', '')
    script_library[name] = {
        "code": code,
        "stats": stats,
        "obfuscation": obf,
        "filename": filename,
        "timestamp": datetime.now().isoformat()
    }
    
    await ctx.send(msg)
    
    # Optional: AI analysis for clean scripts
    if not obf["is_obfuscated"] and GROQ_API_KEY and stats["size_kb"] < 50:
        await ctx.send("🤖 Analyzing script purpose...")
        ai_summary = await ai_analyze_script(code, stats)
        if ai_summary:
            await ctx.send(f"📝 {ai_summary[:1500]}")

@bot.command(name='detect')
async def detect_only(ctx, *, name: str):
    """Detect obfuscation type without showing full script"""
    if name in script_library:
        data = script_library[name]
        obf = data["obfuscation"]
        stats = data["stats"]
        
        msg = f"**{name}.lua**\n"
        msg += f"Size: {stats['size_kb']:.2f} KB | Lines: {stats['lines']}\n"
        
        if obf["is_obfuscated"]:
            msg += f"⚠️ **{obf['type']}**\n"
            msg += f"Confidence: {obf['confidence']}%\n"
            if obf["version"]:
                msg += f"Version: {obf['version']}\n"
        else:
            msg += f"✅ No obfuscation detected\n"
        
        await ctx.send(msg)
    else:
        await ctx.send(f"❌ Script '{name}' not found")

@bot.command(name='get')
async def get_script(ctx, *, name):
    """Retrieve a stored script"""
    if name in script_library:
        data = script_library[name]
        await ctx.send(file=discord.File(io.StringIO(data["code"]), filename=data["filename"]))
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
**GrimHub - Universal Obfuscation Detector**

`.feed <file>` - Upload & analyze a script
`.feed <url>` - Fetch from pastebin/pastefy/raw
`.get <name>` - Download a stored script
`.detect <name>` - Show obfuscation type only
`.list` - Show all stored scripts
`.remove <name>` - Delete a script
`.clear` - Clear AI memory

**Detects:**
Luraph | MoonSec V3 | IronBrew | Prometheus | WeAreDevs | Luarmor | VM Obfuscators

Just ping me for AI chat
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
        {"role": "system", "content": "You are GrimHub, a helpful AI assistant specializing in Lua scripting and obfuscation analysis. Be concise."}
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

async def ai_analyze_script(code: str, stats: dict) -> str:
    if not GROQ_API_KEY:
        return None
    
    prompt = f"""Analyze this Lua script. Tell me what it does in 2-3 sentences.

Stats: {stats['size_kb']:.1f}KB, {stats['functions']} functions
First 1500 chars:
{code[:1500]}"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 300
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

bot.run(TOKEN)
