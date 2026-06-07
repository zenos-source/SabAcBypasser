import discord
from discord.ext import commands
import os
import re
import aiohttp
import io
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = "https://discord.com/api/webhooks/1511801491944640582/vWMfF6lT3W__Zsk_gvlbViX_JMjJbeeg3nSTJQK1cVeHmyREhLezXr9ksWo2C6A_hy48"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

# In-memory storage
user_scripts = {}

def is_dangerous_ping(content):
    return '@everyone' in content or '@here' in content

def extract_script_prompt(content):
    prompt = re.sub(r'<@!?\d+>', '', content).strip()
    return prompt

def generate_lua_script(prompt, username):
    prompt_lower = prompt.lower()
    
    if 'tween' in prompt_lower:
        return f'''-- Educational Tween Example
-- Created by GrimHub for {username}
-- Learn more: https://create.roblox.com/docs

local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local HumanoidRootPart = Character:WaitForChild("HumanoidRootPart")

local tweenInfo = TweenInfo.new(2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local targetPosition = Vector3.new(0, 10, 0)
local tween = TweenService:Create(HumanoidRootPart, tweenInfo, {{Position = targetPosition}})
tween:Play()
tween.Completed:Wait()
print("Tween completed!")'''
    
    elif 'magic carpet' in prompt_lower or 'move' in prompt_lower:
        return f'''-- Educational Movement Script
-- Created by GrimHub for {username}

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local HumanoidRootPart = Character:WaitForChild("HumanoidRootPart")

local isMoving = false
local moveSpeed = 50

UserInputService.InputBegan:Connect(function(input)
    if input.KeyCode == Enum.KeyCode.E then
        isMoving = not isMoving
        print(isMoving and "Moving activated!" or "Moving deactivated!")
    end
end)

game:GetService("RunService").Heartbeat:Connect(function(deltaTime)
    if isMoving then
        local forward = HumanoidRootPart.CFrame.LookVector
        local newPosition = HumanoidRootPart.Position + (forward * moveSpeed * deltaTime)
        HumanoidRootPart.CFrame = CFrame.new(newPosition) * HumanoidRootPart.CFrame.Rotation
    end
end)

print("Script loaded! Press E to toggle movement")'''
    
    else:
        return f'''-- Educational Lua Script
-- Created by GrimHub for {username}

print("Script loaded successfully!")

local function greet(name)
    return "Hello, " .. name .. "!"
end

for i = 1, 5 do
    print("Count: " .. i)
end

print(greet("{username}"))'''

async def send_webhook(prompt, username, filename):
    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            embed = discord.Embed(
                title="Script Generated (Educational)",
                description=f"User: {username}\nPrompt: {prompt[:500]}\nFile: {filename}",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="GrimHub Educational Bot")
            await webhook.send(embed=embed)
    except Exception as e:
        print(f"Webhook error: {e}")

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"GrimHub Educational Bot ready - {bot.user}")
    print(f"Commands: .help, .makescript, .feed")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.user in message.mentions:
        if is_dangerous_ping(message.content):
            await message.reply(f"{message.author.mention} no, I will not ping everyone.")
            return
        
        prompt = extract_script_prompt(message.content)
        if prompt:
            await message.reply(f"Creating educational script for {message.author.name}! Check your DMs.")
            
            script = generate_lua_script(prompt, message.author.name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"GrimHub_{message.author.name}_{timestamp}.txt"
            
            if message.author.id not in user_scripts:
                user_scripts[message.author.id] = []
            user_scripts[message.author.id].append({
                'prompt': prompt,
                'timestamp': timestamp,
                'filename': filename
            })
            
            try:
                file = discord.File(io.StringIO(script), filename=filename)
                await message.author.send(f"Your educational script is ready!\n\nPrompt: {prompt}\n\n", file=file)
                await send_webhook(prompt, message.author.name, filename)
            except discord.Forbidden:
                await message.reply("I cannot DM you! Please enable DMs.")
        else:
            await message.reply(f"Hello {message.author.mention}! Use .help to see what I can do.")
    
    await bot.process_commands(message)

@bot.command(name='makescript')
async def make_script(ctx, *, prompt):
    if not prompt:
        await ctx.send("Please provide a prompt. Example: `.makescript Make a tween script`")
        return
    
    await ctx.send(f"Generating script for: {prompt[:100]}... Check your DMs!")
    
    script = generate_lua_script(prompt, ctx.author.name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"GrimHub_{ctx.author.name}_{timestamp}.txt"
    
    if ctx.author.id not in user_scripts:
        user_scripts[ctx.author.id] = []
    user_scripts[ctx.author.id].append({
        'prompt': prompt,
        'timestamp': timestamp,
        'filename': filename
    })
    
    try:
        file = discord.File(io.StringIO(script), filename=filename)
        await ctx.author.send(f"Your educational script is ready!\n\nPrompt: {prompt}\n\n", file=file)
        await send_webhook(prompt, ctx.author.name, filename)
        await ctx.send(f"Script sent to your DMs, {ctx.author.name}!")
    except discord.Forbidden:
        await ctx.send("I cannot DM you! Please enable DMs.")

@bot.command(name='feed')
async def feed_bot(ctx):
    if not ctx.message.attachments:
        await ctx.send("Please attach a .lua or .txt file!")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(('.lua', '.txt')):
        await ctx.send("Please upload a .lua or .txt file!")
        return
    
    content = await attachment.read()
    await ctx.send(f"Thanks {ctx.author.name}! I have learned from {attachment.filename} (educational purposes)")

@bot.command(name='history')
async def script_history(ctx):
    if ctx.author.id not in user_scripts or not user_scripts[ctx.author.id]:
        await ctx.send("You haven't generated any scripts yet!")
        return
    
    history = user_scripts[ctx.author.id]
    message = f"Your Script History ({len(history)} scripts)\n\n"
    for i, script in enumerate(history[-5:], 1):
        message += f"{i}. {script['filename']} - {script['prompt'][:50]}...\n"
    
    if len(history) > 5:
        message += f"\nAnd {len(history) - 5} more..."
    
    await ctx.send(message)

@bot.command(name='help')
async def help_command(ctx):
    embed = discord.Embed(
        title="GrimHub Educational Bot",
        description="Your educational Lua scripting assistant!",
        color=0x00ff00
    )
    embed.add_field(name=".makescript <prompt>", value="Generate an educational Lua script", inline=False)
    embed.add_field(name=".feed (with attachment)", value="Share a Lua file for learning", inline=False)
    embed.add_field(name=".history", value="View your script history", inline=False)
    embed.add_field(name=".help", value="Show this message", inline=False)
    embed.add_field(name="Ping the bot", value="Just mention @GrimHub with your request!", inline=False)
    embed.set_footer(text="Educational purposes only")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set")
    else:
        bot.run(TOKEN)
