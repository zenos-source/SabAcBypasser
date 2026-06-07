def generate_script(prompt, username):
    prompt_lower = prompt.lower()
    
    if 'tween' in prompt_lower:
        script = f'''local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local RootPart = Character:WaitForChild("HumanoidRootPart")

local TweenInfo = TweenInfo.new(2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local TargetPosition = Vector3.new(0, 10, 0)
local Tween = TweenService:Create(RootPart, TweenInfo, {{Position = TargetPosition}})
Tween:Play()
Tween.Completed:Wait()'''
        return script
    
    elif 'gui' in prompt_lower or 'button' in prompt_lower:
        script = f'''local Players = game:GetService("Players")
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
        return script
    
    elif 'remote' in prompt_lower or 'net' in prompt_lower:
        script = f'''local ReplicatedStorage = game:GetService("ReplicatedStorage")
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
        return script
    
    elif 'teleport' in prompt_lower or 'move' in prompt_lower:
        script = f'''local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local RootPart = Character:WaitForChild("HumanoidRootPart")
local TargetPosition = Vector3.new(0, 10, 0)

RootPart.CFrame = CFrame.new(TargetPosition)'''
        return script
    
    else:
        script = f'''local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local Humanoid = Character:WaitForChild("Humanoid")

Humanoid.WalkSpeed = 50
Humanoid.JumpPower = 100

task.wait(5)

Humanoid.WalkSpeed = 16
Humanoid.JumpPower = 50'''
        return script
