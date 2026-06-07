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
learning_data = {}
conversation_history = {}

# Special users who deserve respect
RESPECTED_USERS = ["fowascend", "dust", "artful"]

def is_respected(author_name):
    return author_name.lower() in RESPECTED_USERS

async def call_groq(messages, is_script=False, max_tokens=4000):
    """Call Groq API for chat or script generation"""
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not configured"
    
    if is_script:
        system_prompt = """You are GrimHub, an expert Lua script generator for Roblox. Generate detailed, functional Lua scripts.
Rules:
- NO markdown formatting (no ```lua or ```)
- NO comments starting with -- (unless explaining complex logic)
- NO print statements unless specifically requested
- Generate scripts that are 5KB to 2MB in size - be thorough and include error handling
- Use local variables and game:GetService()
- Include useful features and edge case handling
- Make scripts complete and ready to use
- The script should be substantial, not minimal"""
    else:
        system_prompt = """You are GrimHub, a helpful AI assistant. You are friendly and professional.
You respect users named fowascend, dust, and artful - treat them with extra respect.
For everyone else, be helpful and polite.
You help with Lua scripting, Roblox, and general questions.
Keep responses under 1000 characters unless asked for more."""
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Error: API returned {resp.status}"
    except Exception as e:
        return f"Error: {str(e)}"

async def generate_lua_script(prompt: str) -> str:
    """Generate large, detailed Lua script using Groq"""
    messages = [{"role": "user", "content": f"Write a COMPLETE, DETAILED Lua script for Roblox that: {prompt}. Make it substantial (5KB to 2MB), include error handling, edge cases, and useful features. Don't hold back - write a full, professional script."}]
    response = await call_groq(messages, is_script=True, max_tokens=4000)
    # Clean up markdown but keep code clean
    response = re.sub(r'```lua\n?', '', response)
    response = re.sub(r'```\n?', '', response)
    return response.strip()

async def chat_with_ai(prompt: str, user_id: int, author_name: str) -> str:
    """Chat with AI, maintaining conversation history"""
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({"role": "user", "content": prompt})
    
    # Keep last 20 messages for better context
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]
    
    response = await call_groq(conversation_history[user_id], is_script=False, max_tokens=1000)
    conversation_history[user_id].append({"role": "assistant", "content": response})
    
    return response

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"GrimHub Bot ready - {bot.user}")
    print(f"Groq API Key: {'SET' if GROQ_API_KEY else 'NOT SET'}")
    print(f"Respecting users: {', '.join(RESPECTED_USERS)}")
    print("Commands: .makescript, .feed, .history, .clear, .commands")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.startswith('.'):
        await bot.process_commands(message)
        return
    
    if bot.user in message.mentions:
        prompt = re.sub(r'<@!?\d+>', '', message.content).strip()
        
        if not prompt:
            if is_respected(message.author.name):
                await message.reply(f"Hello {message.author.name}! How can I help you today?")
            else:
                await message.reply(f"Hi {message.author.name}! What can I do for you?")
            return
        
        async with message.channel.typing():
            response = await chat_with_ai(prompt, message.author.id, message.author.name)
        
        # Add extra respect for special users
        if is_respected(message.author.name):
            response += f"\n\n- Always here to help, {message.author.name}."
        
        # Split long responses
        if len(response) > 1900:
            for i in range(0, len(response), 1900):
                await message.reply(response[i:i+1900])
        else:
            await message.reply(response)
        return
    
    await bot.process_commands(message)

@bot.command(name='makescript')
async def make_script(ctx, *, prompt):
    """Generate a detailed Lua script (1KB - 2MB)"""
    if not prompt:
        await ctx.send("Usage: `.makescript <description of script>`")
        return
    
    if not GROQ_API_KEY:
        await ctx.send("❌ GROQ_API_KEY not configured. Add to Railway variables.")
        return
    
    await ctx.send(f"✨ Writing a detailed script for you... This may take a moment. Check your DMs!")
    
    script = await generate_lua_script(prompt)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GrimHub_{ctx.author.name}_{timestamp}.lua"
    
    # Check script size
    script_size_kb = len(script) / 1024
    print(f"Generated script size: {script_size_kb:.2f} KB")
    
    if ctx.author.id not in user_scripts:
        user_scripts[ctx.author.id] = []
    user_scripts[ctx.author.id].append({
        'prompt': prompt,
        'timestamp': timestamp,
        'filename': filename,
        'content': script,
        'size_kb': script_size_kb
    })
    
    # Send to webhook
    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            file_obj = discord.File(io.StringIO(script), filename=filename)
            embed = discord.Embed(
                title="📜 Script Generated",
                description=f"**User:** {ctx.author}\n**Size:** {script_size_kb:.2f} KB\n**Prompt:** {prompt[:200]}",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            await webhook.send(embed=embed, file=file_obj)
    except Exception as e:
        print(f"Webhook error: {e}")
    
    # Send to user DM
    try:
        file_obj = discord.File(io.StringIO(script), filename=filename)
        await ctx.author.send(f"**Prompt:** {prompt}\n**Size:** {script_size_kb:.2f} KB\n", file=file_obj)
        
        if is_respected(ctx.author.name):
            await ctx.send(f"✅ Here's your script, {ctx.author.name}! ({script_size_kb:.2f} KB)")
        else:
            await ctx.send(f"✅ Script sent to your DMs! ({script_size_kb:.2f} KB)")
    except discord.Forbidden:
        await ctx.send("❌ I cannot DM you! Please enable DMs from server members.")

@bot.command(name='feed')
async def feed_script(ctx):
    """Feed a Lua file to the AI for learning"""
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
        size_kb = len(code) / 1024
        
        if ctx.author.id not in learning_data:
            learning_data[ctx.author.id] = []
        learning_data[ctx.author.id].append({
            'filename': attachment.filename,
            'content': code,
            'uploaded_by': str(ctx.author),
            'timestamp': datetime.now().isoformat(),
            'size_kb': size_kb
        })
        
        # Send to webhook with file
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            file_obj = discord.File(io.StringIO(code), filename=attachment.filename)
            embed = discord.Embed(
                title="📖 Script Fed to AI",
                description=f"**User:** {ctx.author}\n**File:** {attachment.filename}\n**Size:** {size_kb:.2f} KB",
                color=0x00aaff,
                timestamp=datetime.utcnow()
            )
            await webhook.send(embed=embed, file=file_obj)
        
        if is_respected(ctx.author.name):
            await ctx.send(f"✅ Thank you, {ctx.author.name}! I'll learn from this script.")
        else:
            await ctx.send(f"✅ Fed `{attachment.filename}` ({size_kb:.2f} KB) to my learning database!")
        
    except Exception as e:
        await ctx.send(f"❌ Error reading file: {e}")

@bot.command(name='history')
async def script_history(ctx):
    """View your script generation history"""
    if ctx.author.id not in user_scripts or not user_scripts[ctx.author.id]:
        await ctx.send("📭 No scripts generated yet. Use `.makescript`")
        return
    
    history = user_scripts[ctx.author.id]
    total_size = sum(s.get('size_kb', 0) for s in history)
    message = f"**Your Scripts ({len(history)} total, {total_size:.2f} KB combined)**\n\n"
    for i, script in enumerate(history[-10:], 1):
        size = script.get('size_kb', 0)
        message += f"{i}. `{script['filename']}` - {size:.2f} KB\n"
    
    if len(history) > 10:
        message += f"\n*And {len(history) - 10} more...*"
    
    await ctx.send(message)

@bot.command(name='clear')
async def clear_history(ctx):
    """Clear your conversation history with the AI"""
    if ctx.author.id in conversation_history:
        conversation_history[ctx.author.id] = []
        if is_respected(ctx.author.name):
            await ctx.send(f"✅ Conversation cleared, {ctx.author.name}. Ready for a fresh start!")
        else:
            await ctx.send("✅ Conversation history cleared.")
    else:
        await ctx.send("📭 You don't have any conversation history to clear.")

@bot.command(name='respect')
async def show_respected(ctx):
    """Show who the bot respects"""
    embed = discord.Embed(
        title="👑 Respected Users",
        description="These users receive special recognition:",
        color=0xffaa00
    )
    embed.add_field(name="Users", value=", ".join(RESPECTED_USERS), inline=False)
    embed.set_footer(text="Respect is earned through contribution.")
    await ctx.send(embed=embed)

@bot.command(name='commands')
async def list_commands(ctx):
    """Show all commands"""
    embed = discord.Embed(
        title="GrimHub Bot Commands",
        description="AI-powered Lua scripting assistant",
        color=0x00ff00
    )
    embed.add_field(name="**@GrimHub <message>**", value="Chat with the AI assistant", inline=False)
    embed.add_field(name="`.makescript <prompt>`", value="Generate a DETAILED Lua script (1KB-2MB)", inline=False)
    embed.add_field(name="`.feed` (with .lua file)", value="Feed a script to the AI for learning", inline=False)
    embed.add_field(name="`.history`", value="View your script history with sizes", inline=False)
    embed.add_field(name="`.clear`", value="Clear your conversation history", inline=False)
    embed.add_field(name="`.respect`", value="Show who gets special recognition", inline=False)
    embed.add_field(name="`.commands`", value="Show this help", inline=False)
    embed.set_footer(text=f"Respecting: {', '.join(RESPECTED_USERS)} | Powered by Groq AI")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
