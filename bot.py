import discord
from discord.ext import commands
import os
import re
import io
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

user_scripts = {}

def is_dangerous_ping(content):
    return '@everyone' in content or '@here' in content

def is_script_request(content):
    content_lower = content.lower()
    keywords = ['make', 'create', 'generate', 'script', 'code', 'write', 'tween', 'gui', 'remote', 'button', 'frame', 'teleport', 'move']
    return any(keyword in content_lower for keyword in keywords)

def extract_prompt(content):
    return re.sub(r'<@!?\d+>', '', content).strip()

def generate_script(prompt, username):
    prompt_lower = prompt.lower()
    
    if 'tween' in prompt_lower:
        return f'''local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local RootPart = Character:WaitForChild("HumanoidRootPart")

local TweenInfo = TweenInfo.new(2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local TargetPosition = Vector3.new(0, 10, 0)
local Tween = TweenService:Create(RootPart, TweenInfo, {{Position = TargetPosition}})
Tween:Play()
Tween.Completed:Wait()'''
    
    elif 'gui' in prompt_lower or 'button' in prompt_lower:
        return f'''local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local ScreenGui = Instance.new("ScreenGui")
ScreenGui.Name = "GrimHubGUI"
ScreenGui.Parent = LocalPlayer:WaitForChild("PlayerGui")

local Frame = Instance.new("Frame")
Frame.Size = UDim2.new(0, 300, 0, 200)
Frame.Position = UDim2.new(0.5, -150, 0.5, -100)
Frame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
Frame.Parent = ScreenGui

local Button = Instance.new("TextButton")
Button.Size = UDim2.new(0, 100, 0, 40)
Button.Position = UDim2.new(0.5, -50, 0.5, -20)
Button.Text = "Click"
Button.Parent = Frame

Button.MouseButton1Click:Connect(function()
    Frame.BackgroundColor3 = Color3.fromRGB(86, 196, 128)
end)'''
    
    elif 'remote' in prompt_lower or 'net' in prompt_lower:
        return f'''local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer

local Remote = Instance.new("RemoteEvent")
Remote.Name = "ExampleRemote"
Remote.Parent = ReplicatedStorage

Remote.OnClientEvent:Connect(function(Data)
    LocalPlayer.Character.HumanoidRootPart.Position = Data.Position
end)

local function SendData()
    Remote:FireServer({{
        Position = LocalPlayer.Character.HumanoidRootPart.Position,
        Player = LocalPlayer.Name
    }})
end

SendData()'''
    
    elif 'teleport' in prompt_lower or 'move' in prompt_lower:
        return f'''local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local RootPart = Character:WaitForChild("HumanoidRootPart")
local TargetPosition = Vector3.new(0, 10, 0)

RootPart.CFrame = CFrame.new(TargetPosition)'''
    
    else:
        return f'''local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local Humanoid = Character:WaitForChild("Humanoid")

Humanoid.WalkSpeed = 50
Humanoid.JumpPower = 100

task.wait(5)

Humanoid.WalkSpeed = 16
Humanoid.JumpPower = 50'''

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"GrimHub Bot ready - {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.user in message.mentions:
        if is_dangerous_ping(message.content):
            await message.reply(f"{message.author.mention} No, I will not ping everyone.")
            return
        
        if is_script_request(message.content):
            prompt = extract_prompt(message.content)
            await message.reply(f"Creating script for {message.author.name}! Check your DMs.")
            
            script = generate_script(prompt, message.author.name)
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
                file_obj = discord.File(io.StringIO(script), filename=filename)
                await message.author.send(f"Your script is ready!\n\nPrompt: {prompt}\n", file=file_obj)
                await message.reply("Script sent to your DMs!")
            except discord.Forbidden:
                await message.reply("I cannot DM you! Please enable DMs.")
        else:
            await message.reply(f"Hello {message.author.mention}! Mention me with 'make', 'create', or 'script' to generate code.")
    
    await bot.process_commands(message)

@bot.command(name='makescript')
async def make_script(ctx, *, prompt):
    if not prompt:
        await ctx.send("Example: `.makescript create a tween script`")
        return
    
    await ctx.send(f"Generating script... Check your DMs!")
    
    script = generate_script(prompt, ctx.author.name)
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
        file_obj = discord.File(io.StringIO(script), filename=filename)
        await ctx.author.send(f"Your script is ready!\n\nPrompt: {prompt}\n", file=file_obj)
        await ctx.send(f"Script sent to your DMs!")
    except discord.Forbidden:
        await ctx.send("I cannot DM you! Please enable DMs.")

@bot.command(name='history')
async def script_history(ctx):
    if ctx.author.id not in user_scripts or not user_scripts[ctx.author.id]:
        await ctx.send("No scripts yet!")
        return
    
    history = user_scripts[ctx.author.id]
    message = f"Script History ({len(history)})\n\n"
    for i, script in enumerate(history[-5:], 1):
        message += f"{i}. {script['filename']}\n"
    
    await ctx.send(message)

@bot.command(name='bothelp')
async def bot_help(ctx):
    embed = discord.Embed(title="GrimHub Bot", description="Lua scripting assistant", color=0x00ff00)
    embed.add_field(name=".makescript <prompt>", value="Generate a Lua script", inline=False)
    embed.add_field(name=".history", value="View script history", inline=False)
    embed.add_field(name=".bothelp", value="Show this help", inline=False)
    embed.add_field(name="Mention me", value="Use 'make', 'create', or 'script' keywords", inline=False)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)
