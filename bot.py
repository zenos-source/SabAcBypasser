import discord
from discord.ext import commands
import os
import re
import io
import aiohttp
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

user_scripts = {}

async def generate_lua_script(prompt: str) -> str:
    """Use Groq API to generate actual Lua code"""
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY not configured"
    
    system_prompt = """You are a Lua scripting expert for Roblox. Generate ONLY raw Lua code.
    No explanations, no markdown, no comments starting with --, no print statements unless specifically requested.
    Just the code. Focus on functional, working scripts.
    Use local variables, proper syntax, and common Roblox services (game:GetService)."""
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write a Lua script for Roblox that: {prompt}"}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    code = result["choices"][0]["message"]["content"]
                    # Clean up markdown code blocks if present
                    code = re.sub(r'```lua\n?', '', code)
                    code = re.sub(r'```\n?', '', code)
                    return code.strip()
                else:
                    return f"Error: API returned {resp.status}"
    except Exception as e:
        return f"Error: {str(e)}"

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"GrimHub Bot ready - {bot.user}")
    if GROQ_API_KEY:
        print("Groq AI is ENABLED - real script generation active")
    else:
        print("WARNING: Groq AI not configured - add GROQ_API_KEY")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.user in message.mentions:
        prompt = re.sub(r'<@!?\d+>', '', message.content).strip()
        if prompt:
            await message.reply(f"Generating script for {message.author.name}... Check your DMs!")
            
            script = await generate_lua_script(prompt)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"GrimHub_{message.author.name}_{timestamp}.lua"
            
            try:
                file_obj = discord.File(io.StringIO(script), filename=filename)
                await message.author.send(f"**Prompt:** {prompt}\n", file=file_obj)
                await message.reply("Script sent to your DMs!")
            except discord.Forbidden:
                await message.reply("I cannot DM you! Please enable DMs.")
        else:
            await message.reply(f"Hello {message.author.mention}! Mention me with what script you want.")
    
    await bot.process_commands(message)

@bot.command(name='makescript')
async def make_script(ctx, *, prompt):
    if not prompt:
        await ctx.send("Example: `.makescript A script that makes the player move faster when holding shift`")
        return
    
    if not GROQ_API_KEY:
        await ctx.send("ERROR: GROQ_API_KEY not configured. Add it to Railway variables.")
        return
    
    await ctx.send(f"Generating script using AI... Check your DMs!")
    
    script = await generate_lua_script(prompt)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GrimHub_{ctx.author.name}_{timestamp}.lua"
    
    try:
        file_obj = discord.File(io.StringIO(script), filename=filename)
        await ctx.author.send(f"**Prompt:** {prompt}\n", file=file_obj)
        await ctx.send(f"Script sent to your DMs!")
    except discord.Forbidden:
        await ctx.send("I cannot DM you! Please enable DMs.")

@bot.command(name='bothelp')
async def bot_help(ctx):
    embed = discord.Embed(title="GrimHub Bot", color=0x00ff00)
    embed.add_field(name=".makescript <prompt>", value="Generate a Lua script using AI", inline=False)
    embed.add_field(name="Mention @GrimHub", value="Say what script you want", inline=False)
    embed.set_footer(text="Requires GROQ_API_KEY for real AI generation")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
