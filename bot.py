import discord
from discord.ext import commands
import os
import re
import json
import aiohttp
import io
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = "https://discord.com/api/webhooks/1511801491944640582/vWMfF6lT3W__Zsk_gvlbViX_JMjJbeeg3nSTJQK1cVeHmyREhLezXr9ksWo2C6A_hy48"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

# Store user data
user_scripts = {}
user_history = {}

# Load user data from file
def load_user_data():
    global user_scripts, user_history
    try:
        with open('user_data.json', 'r') as f:
            data = json.load(f)
            user_scripts = data.get('scripts', {})
            user_history = data.get('history', {})
    except:
        pass

def save_user_data():
    with open('user_data.json', 'w') as f:
        json.dump({'scripts': user_scripts, 'history': user_history}, f)

def is_dangerous_ping(content):
    """Check if message contains @everyone or @here"""
    return '@everyone' in content or '@here' in content

def extract_script_prompt(content):
    """Extract the actual prompt after removing the bot mention"""
    # Remove the bot mention
    prompt = re.sub(r'<@!?\d+>', '', content).strip()
    return prompt

def generate_lua_script(prompt, username):
    """Generate educational Lua script based on prompt (simplified example)"""
    
    # Educational templates - these are LEARNING examples, not cheats
    templates = {
        'tween': f'''
-- Educational Tween Example for Roblox
-- Created by GrimHub for {username}
-- Learn more: https://create.roblox.com/docs/scripting/animation/tween-service

local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local HumanoidRootPart = Character:WaitForChild("HumanoidRootPart")

-- Create tween information
local tweenInfo = TweenInfo.new(
    2, -- Duration
    Enum.EasingStyle.Quad, -- Easing style
    Enum.EasingDirection.Out -- Easing direction
)

-- Target position (modify as needed)
local targetPosition = Vector3.new(0, 10, 0)

-- Create and play tween
local tween = TweenService:Create(HumanoidRootPart, tweenInfo, {Position = targetPosition})
tween:Play()

-- Wait for completion
tween.Completed:Wait()
print("Tween completed!")
''',
        'magic_carpet': f'''
-- Educational Movement Script Example
-- Created by GrimHub for {username}
-- This demonstrates character movement mechanics

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local Humanoid = Character:WaitForChild("Humanoid")
local HumanoidRootPart = Character:WaitForChild("HumanoidRootPart")

local isMoving = false
local moveSpeed = 50
local moveDirection = Vector3.new(0, 0, 0)

UserInputService.InputBegan:Connect(function(input)
    if input.KeyCode == Enum.KeyCode.E then
        isMoving = not isMoving
        if isMoving then
            print("Magic Carpet activated!")
        else
            print("Magic Carpet deactivated!")
        end
    end
end)

game:GetService("RunService").Heartbeat:Connect(function(deltaTime)
    if isMoving then
        -- Move forward relative to character's facing direction
        local cf = HumanoidRootPart.CFrame
        local forward = cf.LookVector
        local newPosition = HumanoidRootPart.Position + (forward * moveSpeed * deltaTime)
        HumanoidRootPart.CFrame = CFrame.new(newPosition) * cf.Rotation
    end
end)

print("Script loaded! Press 'E' to toggle movement")
''',
        'default': f'''
-- Educational Lua Script Example
-- Created by GrimHub for {username}
-- This is a template for learning Lua basics

print("Script loaded successfully!")

-- Example: Basic function
local function greet(name)
    return "Hello, " .. name .. "!"
end

-- Example: Loop
for i = 1, 5 do
    print("Count: " .. i)
end

-- Add your custom code below
print(greet("{username}"))
'''
    }
    
    # Determine which template to use
    prompt_lower = prompt.lower()
    if 'tween' in prompt_lower:
        return templates['tween']
    elif 'magic carpet' in prompt_lower or 'move' in prompt_lower:
        return templates['magic_carpet']
    else:
        return templates['default']

async def send_webhook(prompt, username, filename):
    """Send educational log to webhook"""
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
        embed = discord.Embed(
            title="📚 Script Generated (Educational)",
            description=f"**User:** {username}\n**Prompt:** {prompt[:500]}\n**File:** {filename}",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="GrimHub Educational Bot - Learning Purpose Only")
        await webhook.send(embed=embed)

@bot.event
async def on_ready():
    load_user_data()
    print(f"✅ GrimHub Educational Bot ready - {bot.user}")
    print(f"📡 Commands: .help, .makescript, .feed")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Check if bot was pinged
    if bot.user in message.mentions:
        if is_dangerous_ping(message.content):
            await message.reply(f"{message.author.mention} no, I won't ping everyone. That's against Discord's Terms of Service.")
            return
        
        # Extract the script request
        prompt = extract_script_prompt(message.content)
        if prompt:
            await message.reply(f"📚 I'll create an educational script for you, {message.author.name}! Check your DMs.")
            
            # Generate script
            script = generate_lua_script(prompt, message.author.name)
            
            # Save to user history
            if message.author.id not in user_scripts:
                user_scripts[message.author.id] = []
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"GrimHub_{message.author.name}_{timestamp}.txt"
            
            user_scripts[message.author.id].append({
                'prompt': prompt,
                'script': script,
                'timestamp': timestamp,
                'filename': filename
            })
            save_user_data()
            
            # Send DM with the script
            try:
                file = discord.File(io.StringIO(script), filename=filename)
                await message.author.send(f"📜 **Your educational script is ready!**\n\n**Prompt:** {prompt}\n\n", file=file)
                
                # Send to webhook
                await send_webhook(prompt, message.author.name, filename)
                
            except discord.Forbidden:
                await message.reply("❌ I can't DM you! Please enable DMs from server members.")
        else:
            await message.reply(f"👋 Hello {message.author.mention}! I'm GrimHub, your educational Lua assistant. Use `.help` to see what I can do!")
    
    await bot.process_commands(message)

@bot.command(name='makescript')
async def make_script(ctx, *, prompt):
    """Generate an educational Lua script from a prompt"""
    if not prompt:
        await ctx.send("❌ Please provide a prompt! Example: `.makescript Make a tween script`")
        return
    
    await ctx.send(f"📚 Generating educational script for **{prompt[:100]}**... Check your DMs!")
    
    script = generate_lua_script(prompt, ctx.author.name)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GrimHub_{ctx.author.name}_{timestamp}.txt"
    
    if ctx.author.id not in user_scripts:
        user_scripts[ctx.author.id] = []
    
    user_scripts[ctx.author.id].append({
        'prompt': prompt,
        'script': script,
        'timestamp': timestamp,
        'filename': filename
    })
    save_user_data()
    
    try:
        file = discord.File(io.StringIO(script), filename=filename)
        await ctx.author.send(f"📜 **Your educational script is ready!**\n\n**Prompt:** {prompt}\n\n", file=file)
        await send_webhook(prompt, ctx.author.name, filename)
        await ctx.send(f"✅ Script sent to your DMs, {ctx.author.name}!")
    except discord.Forbidden:
        await ctx.send("❌ I can't DM you! Please enable DMs from server members.")

@bot.command(name='feed')
async def feed_bot(ctx):
    """Upload a Lua file for the bot to learn from (educational)"""
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach a `.lua` or `.txt` file!")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(('.lua', '.txt')):
        await ctx.send("❌ Please upload a `.lua` or `.txt` file!")
        return
    
    content = await attachment.read()
    try:
        code = content.decode('utf-8')
        
        # Store for learning (educational purposes)
        if 'learning_data' not in user_scripts:
            user_scripts['learning_data'] = []
        
        user_scripts['learning_data'].append({
            'filename': attachment.filename,
            'content': code[:5000],  # Store first 5000 chars
            'uploaded_by': str(ctx.author),
            'timestamp': datetime.now().isoformat()
        })
        save_user_data()
        
        await ctx.send(f"✅ Thanks, {ctx.author.name}! I've learned from `{attachment.filename}` (educational purposes only)")
        
        # Log to webhook
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            embed = discord.Embed(
                title="📚 Script Uploaded for Learning",
                description=f"**User:** {ctx.author}\n**File:** {attachment.filename}\n**Size:** {len(code)} chars",
                color=0x00aaff
            )
            await webhook.send(embed=embed)
            
    except Exception as e:
        await ctx.send(f"❌ Error reading file: {e}")

@bot.command(name='history')
async def script_history(ctx):
    """View your script history"""
    if ctx.author.id not in user_scripts or not user_scripts[ctx.author.id]:
        await ctx.send("📭 You haven't generated any scripts yet!")
        return
    
    history_list = user_scripts[ctx.author.id]
    history_text = f"**Your Script History ({len(history_list)} scripts)**\n\n"
    for i, script in enumerate(history_list[-5:], 1):
        history_text += f"{i}. `{script['filename']}` - {script['prompt'][:50]}...\n"
    
    if len(history_list) > 5:
        history_text += f"\n*And {len(history_list) - 5} more...*"
    
    await ctx.send(history_text)

@bot.command(name='help')
async def help_command(ctx):
    """Show help message"""
    embed = discord.Embed(
        title="🤖 GrimHub Educational Bot",
        description="Your educational Lua scripting assistant!",
        color=0x00ff00
    )
    embed.add_field(name="`.makescript <prompt>`", value="Generate an educational Lua script", inline=False)
    embed.add_field(name="`.feed` (with attachment)", value="Share a Lua file for learning", inline=False)
    embed.add_field(name="`.history`", value="View your script history", inline=False)
    embed.add_field(name="`.help`", value="Show this message", inline=False)
    embed.add_field(name="**Ping the bot**", value="Just mention @GrimHub with your request!", inline=False)
    embed.set_footer(text="Educational purposes only. All scripts are learning examples.")
    
    await ctx.send(embed=embed)

@bot.command(name='webhook_test')
@commands.has_permissions(administrator=True)
async def test_webhook(ctx):
    """Test the webhook connection (admin only)"""
    try:
        await send_webhook("Test message", "System", "test.txt")
        await ctx.send("✅ Webhook test sent!")
    except Exception as e:
        await ctx.send(f"❌ Webhook error: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)
