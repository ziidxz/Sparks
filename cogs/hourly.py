"""
Hourly command module for the anime card game.
Allows players to gain stamina hourly for dungeon exploration.
"""

import discord
from discord.ext import commands
import time
import random

class Hourly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.cooldown = 3600  # 1 hour cooldown in seconds
    
    def get_time_remaining(self, last_hourly):
        """Calculate time remaining until next hourly reward."""
        now = int(time.time())
        time_elapsed = now - last_hourly
        
        if time_elapsed >= self.cooldown:
            return 0
            
        return self.cooldown - time_elapsed
    
    def format_time(self, seconds):
        """Format time in seconds to hours, minutes, seconds."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    @commands.command(name="hourly")
    async def hourly_command(self, ctx):
        """⏱️ Claim hourly stamina reward (30 stamina every hour)"""
        user_id = ctx.author.id
        
        # Check if player has a profile
        self.cursor.execute("SELECT id, stamina, max_stamina, last_hourly FROM api_players WHERE discord_id = ?", (user_id,))
        player = self.cursor.fetchone()
        
        if not player:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
            
        player_id, stamina, max_stamina, last_hourly = player
        
        # Default last_hourly to 0 if NULL
        last_hourly = last_hourly or 0
        
        # Check if on cooldown
        time_remaining = self.get_time_remaining(last_hourly)
        
        if time_remaining > 0:
            formatted_time = self.format_time(time_remaining)
            
            embed = discord.Embed(
                title="Hourly Cooldown",
                description=f"You need to wait **{formatted_time}** to claim your hourly reward!",
                color=discord.Color.red()
            )
            
            # Add current stamina
            embed.add_field(
                name="Current Stamina",
                value=f"{stamina}/{max_stamina}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
        
        # Give reward (30 stamina)
        reward_stamina = 30
        
        # Make sure not to exceed max stamina
        new_stamina = min(max_stamina, stamina + reward_stamina)
        wasted_stamina = (stamina + reward_stamina) - new_stamina if stamina + reward_stamina > max_stamina else 0
        
        # Update stamina and last_hourly
        now = int(time.time())
        self.cursor.execute(
            "UPDATE api_players SET stamina = ?, last_hourly = ? WHERE discord_id = ?",
            (new_stamina, now, user_id)
        )
        self.db.conn.commit()
        
        # Create reward embed
        embed = discord.Embed(
            title="Hourly Reward Claimed!",
            description=f"You gained **{reward_stamina}** stamina!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Stamina",
            value=f"{new_stamina}/{max_stamina}",
            inline=True
        )
        
        if wasted_stamina > 0:
            embed.add_field(
                name="Warning",
                value=f"You wasted {wasted_stamina} stamina because you reached your stamina cap!",
                inline=False
            )
        
        embed.add_field(
            name="Next Reward",
            value=f"Next hourly reward available in 1 hour",
            inline=False
        )
        
        embed.set_footer(text="Use !hourly every hour to maximize your stamina income!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Hourly(bot))