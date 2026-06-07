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
conversation_history = {}

async def call_groq(messages, is_script=False):
    """Call Groq API for chat or script generation"""
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not configured"
    
    if is_script:
        system_prompt = """You are a Lua scripting expert for Roblox. Generate ONLY raw Lua code.
No markdown, no explanations, no comments starting with --, no print statements.
Just the code. Use local variables and game:GetService()."""
    else:
        system_prompt = """You are GrimHub, a helpful AI assistant. Be friendly and concise.
You help with Lua scripting, Roblox, and general questions.
Keep responses under 500 characters unless asked for more."""
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": 0.7,
        "max_tokens": 1500 if is_script else 500
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Error: API returned {resp.status}"
    except Exception as e:
        return f"Error: {str(e)}"

async def generate_lua_script(prompt: str) -> str:
    """Generate Lua script using Groq"""
    messages = [{"role": "user", "content": f"Write a Lua script for Roblox that: {prompt}"}]
    response = await call_groq(messages, is_script=True)
    # Clean up markdown and comments
    response = re.sub(r'```lua\n?', '', response)
    response = re.sub(r'```\n?', '', response)
    response = re.sub(r'^--.*\n?', '', response, flags=re.MULTILINE)
    return response.strip()

async def chat_with_ai(prompt: str, user_id: int) -> str:
    """Chat with AI, maintaining conversation history"""
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({"role": "user", "content": prompt})
    
    # Keep last 10 messages for context
    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]
    
    response = await call_groq(conversation_history[user_id], is_script=False)
    conversation_history[user_id].append({"role": "assistant", "content": response})
    
    return response

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"GrimHub Bot ready - {bot.user}")
    print(f"Groq API Key: {'SET' if GROQ_API_KEY else 'NOT SET'}")
    print("Commands: .makescript, .feed, .history, .commands")
    print("Ping the bot for AI chat!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Handle commands
    if message.content.startswith('.'):
        await bot.process_commands(message)
        return
    
    # Handle bot pings - AI CHAT
    if bot.user in message.mentions:
        prompt = re.sub(r'<@!?\d+>', '', message.content).strip()
        
        if not prompt:
            await message.reply(f"Hello {message.author.name}! Ask me anything about Lua, Roblox, or just chat!")
            return
        
        # Show typing indicator while AI thinks
        async with message.channel.typing():
            response = await chat_with_ai(prompt, message.author.id)
        
        # Split long responses if needed
        if len(response) > 1900:
            for i in range(0, len(response), 1900):
                await message.reply(response[i:i+1900])
        else:
            await message.reply(response)
        return
    
    await bot.process_commands(message)

@bot.command(name='makescript')
async def make_script(ctx, *, prompt):
    """Generate a Lua script"""
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
    
    # Send to webhook
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
        
        learning_data.append({
            'filename': attachment.filename,
            'content': code,
            'uploaded_by': str(ctx.author),
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to webhook with file
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
    """View your script generation history"""
    if ctx.author.id not in user_scripts or not user_scripts[ctx.author.id]:
        await ctx.send("📭 No scripts generated yet. Use `.makescript`")
        return
    
    history = user_scripts[ctx.author.id]
    message = f"**Your Scripts ({len(history)} total)**\n\n"
    for i, script in enumerate(history[-10:], 1):
        message += f"{i}. `{script['filename']}`\n"
    
    await ctx.send(message)

@bot.command(name='clear')
async def clear_history(ctx):
    """Clear your conversation history with the AI"""
    if ctx.author.id in conversation_history:
        conversation_history[ctx.author.id] = []
        await ctx.send("✅ Your conversation history has been cleared!")
    else:
        await ctx.send("📭 You have no conversation history to clear.")

@bot.command(name='commands')
async def list_commands(ctx):
    """Show all commands"""
    embed = discord.Embed(
        title="GrimHub Bot Commands",
        description="AI-powered Lua scripting assistant",
        color=0x00ff00
    )
    embed.add_field(name="**Ping the bot**", value="Just mention @GrimHub and ask anything!", inline=False)
    embed.add_field(name="`.makescript <prompt>`", value="Generate a Lua script", inline=False)
    embed.add_field(name="`.feed` (with .lua file)", value="Feed a script to the AI for learning", inline=False)
    embed.add_field(name="`.history`", value="View your script history", inline=False)
    embed.add_field(name="`.clear`", value="Clear your conversation history", inline=False)
    embed.add_field(name="`.commands`", value="Show this help", inline=False)
    embed.set_footer(text="Powered by Groq AI | Educational purposes only")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
