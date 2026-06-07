@bot.command(name='createrole')
@commands.is_owner()
async def create_role(ctx, role_name: str, color: str = None, position: int = None):
    """Create a new role (owner only). 
    Usage: .createrole <name> [color] [position]
    Color: #FF0000 or red/blue/green
    Position: lower number = higher up"""
    try:
        # Get the bot's highest role
        bot_member = ctx.guild.get_member(bot.user.id)
        bot_highest_role = bot_member.top_role
        
        color_obj = None
        if color:
            if color.startswith('#'):
                color_obj = discord.Color(int(color[1:], 16))
            else:
                color_map = {
                    'red': discord.Color.red(),
                    'blue': discord.Color.blue(),
                    'green': discord.Color.green(),
                    'yellow': discord.Color.yellow(),
                    'purple': discord.Color.purple(),
                    'orange': discord.Color.orange(),
                    'pink': discord.Color.magenta(),
                    'black': discord.Color.dark_grey(),
                    'white': discord.Color.light_grey(),
                    'cyan': discord.Color.teal(),
                    'gold': discord.Color.gold(),
                }
                if color.lower() in color_map:
                    color_obj = color_map[color.lower()]
                else:
                    color_obj = discord.Color.default()
        else:
            color_obj = discord.Color.default()
        
        # Create the role
        role = await ctx.guild.create_role(name=role_name, color=color_obj)
        
        # Move to specified position if provided
        if position is not None:
            # Ensure position is not higher than bot's highest role
            max_position = bot_highest_role.position - 1
            if position > max_position:
                position = max_position
                await ctx.send(f"⚠️ Role position adjusted to {position} (bot's role limit)")
            await role.edit(position=position)
        
        await ctx.send(f"✅ Created role: {role.mention} at position {role.position}")
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to create roles. Make sure my role is high enough in the hierarchy.")
    except discord.HTTPException as e:
        await ctx.send(f"❌ Discord error: {e}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='createroleabove')
@commands.is_owner()
async def create_role_above(ctx, role_name: str, target_role: discord.Role, color: str = None):
    """Create a new role directly above an existing role (owner only)"""
    try:
        bot_member = ctx.guild.get_member(bot.user.id)
        bot_highest_role = bot_member.top_role
        
        # Check if bot can manage the target role
        if target_role.position >= bot_highest_role.position:
            await ctx.send(f"❌ Cannot create role above {target_role.mention} - my role is too low.")
            return
        
        color_obj = None
        if color:
            if color.startswith('#'):
                color_obj = discord.Color(int(color[1:], 16))
            else:
                color_map = {
                    'red': discord.Color.red(),
                    'blue': discord.Color.blue(),
                    'green': discord.Color.green(),
                    'yellow': discord.Color.yellow(),
                    'purple': discord.Color.purple(),
                    'orange': discord.Color.orange(),
                    'pink': discord.Color.magenta(),
                    'black': discord.Color.dark_grey(),
                    'white': discord.Color.light_grey(),
                }
                if color.lower() in color_map:
                    color_obj = color_map[color.lower()]
                else:
                    color_obj = discord.Color.default()
        else:
            color_obj = discord.Color.default()
        
        # Create role at target position + 1 (above target)
        role = await ctx.guild.create_role(name=role_name, color=color_obj)
        await role.edit(position=target_role.position + 1)
        
        await ctx.send(f"✅ Created role: {role.mention} above {target_role.mention}")
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to create roles. Make sure my role is high enough.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='createrolebelow')
@commands.is_owner()
async def create_role_below(ctx, role_name: str, target_role: discord.Role, color: str = None):
    """Create a new role directly below an existing role (owner only)"""
    try:
        color_obj = None
        if color:
            if color.startswith('#'):
                color_obj = discord.Color(int(color[1:], 16))
            else:
                color_map = {
                    'red': discord.Color.red(),
                    'blue': discord.Color.blue(),
                    'green': discord.Color.green(),
                    'yellow': discord.Color.yellow(),
                    'purple': discord.Color.purple(),
                    'orange': discord.Color.orange(),
                    'pink': discord.Color.magenta(),
                    'black': discord.Color.dark_grey(),
                    'white': discord.Color.light_grey(),
                }
                if color.lower() in color_map:
                    color_obj = color_map[color.lower()]
                else:
                    color_obj = discord.Color.default()
        else:
            color_obj = discord.Color.default()
        
        role = await ctx.guild.create_role(name=role_name, color=color_obj)
        await role.edit(position=target_role.position)
        
        await ctx.send(f"✅ Created role: {role.mention} below {target_role.mention}")
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to create roles.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='showroles')
@commands.is_owner()
async def show_roles(ctx):
    """Show all roles and their positions (owner only)"""
    try:
        roles = sorted(ctx.guild.roles, key=lambda x: x.position, reverse=True)
        msg = "**📋 Role Hierarchy (highest to lowest):**\n"
        for role in roles[:20]:  # Show top 20
            msg += f"{role.position}: {role.mention}\n"
        if len(roles) > 20:
            msg += f"\n*... and {len(roles) - 20} more roles*"
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
