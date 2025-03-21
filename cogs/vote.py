"""
Vote command system for the anime card game.
Players can vote for the bot and receive rewards.
"""

import discord
from discord.ext import commands
import time
import random

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.vote_cooldown = 43200  # 12 hours cooldown in seconds
    
    def get_vote_time_remaining(self, last_vote):
        """Calculate time remaining until next vote."""
        now = int(time.time())
        time_elapsed = now - last_vote
        
        if time_elapsed >= self.vote_cooldown:
            return 0
            
        return self.vote_cooldown - time_elapsed
    
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
    
    @commands.command(name="vote")
    async def vote_command(self, ctx):
        """🗳️ Vote for the bot and earn rewards (every 12 hours)"""
        user_id = ctx.author.id
        
        # Check if player has a profile
        self.cursor.execute("""
            SELECT id, level, gold, stamina, last_vote, vote_streak 
            FROM api_players 
            WHERE discord_id = ?
        """, (user_id,))
        
        player = self.cursor.fetchone()
        
        if not player:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
            
        player_id, level, gold, stamina, last_vote, vote_streak = player
        
        # Default values if NULL
        last_vote = last_vote or 0
        vote_streak = vote_streak or 0
        
        # Check if on cooldown
        time_remaining = self.get_vote_time_remaining(last_vote)
        
        if time_remaining > 0:
            formatted_time = self.format_time(time_remaining)
            
            embed = discord.Embed(
                title="Vote Cooldown",
                description=f"You need to wait **{formatted_time}** before you can vote again!",
                color=discord.Color.red()
            )
            
            # Add vote streak
            embed.add_field(
                name="Current Vote Streak",
                value=f"{vote_streak} votes",
                inline=False
            )
            
            # Add link to vote
            embed.add_field(
                name="Vote Link",
                value="[Click here to vote for the bot](https://top.gg/bot/your-bot-id)",
                inline=False
            )
            
            embed.set_footer(text="Vote every 12 hours to increase your streak and get better rewards!")
            
            await ctx.send(embed=embed)
            return
        
        # Increment vote streak
        now = int(time.time())
        
        # Check if streak should be reset (more than 24 hours since last vote)
        streak_reset = (now - last_vote) > 86400 and last_vote > 0
        
        if streak_reset:
            vote_streak = 1
        else:
            vote_streak += 1
        
        # Calculate rewards based on streak
        base_gold = 100
        base_exp = 20
        base_stamina = 50
        
        # Bonus rewards for streaks
        streak_bonus = min(vote_streak * 0.1, 1.0)  # Max 100% bonus at 10 streak
        
        gold_reward = int(base_gold * (1 + streak_bonus))
        exp_reward = int(base_exp * (1 + streak_bonus))
        stamina_reward = int(base_stamina * (1 + streak_bonus))
        
        # Special bonus every 5 votes
        special_bonus = vote_streak % 5 == 0 and vote_streak > 0
        
        # Update player
        self.cursor.execute("""
            UPDATE api_players 
            SET gold = gold + ?, last_vote = ?, vote_streak = ?, stamina = stamina + ?
            WHERE discord_id = ?
        """, (gold_reward, now, vote_streak, stamina_reward, user_id))
        
        # Add experience
        battle_cog = self.bot.get_cog("BattleSystem")
        if battle_cog:
            player_level_up, new_level = battle_cog.add_player_exp(user_id, exp_reward)
        else:
            player_level_up, new_level = False, None
        
        # Give special bonus if applicable
        bonus_reward = None
        
        if special_bonus:
            # 1 in 4 chance to get a random material
            if random.randint(1, 4) == 1:
                # Get a random material
                self.cursor.execute("SELECT id, name FROM materials ORDER BY RANDOM() LIMIT 1")
                material = self.cursor.fetchone()
                
                if material:
                    material_id, material_name = material
                    material_quantity = random.randint(1, 3)
                    
                    # Add to player's inventory
                    self.cursor.execute("""
                        INSERT INTO user_materials (player_id, material_id, quantity)
                        VALUES (?, ?, ?)
                        ON CONFLICT (player_id, material_id) 
                        DO UPDATE SET quantity = quantity + ?
                    """, (player_id, material_id, material_quantity, material_quantity))
                    
                    bonus_reward = f"{material_quantity}x {material_name}"
            else:
                # Extra gold
                extra_gold = random.randint(100, 500)
                self.cursor.execute("UPDATE api_players SET gold = gold + ? WHERE discord_id = ?", 
                                  (extra_gold, user_id))
                bonus_reward = f"{extra_gold} extra gold"
        
        self.db.conn.commit()
        
        # Create reward embed
        embed = discord.Embed(
            title="Thanks for Voting!",
            description=f"You have voted for the bot and received rewards!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Vote Streak",
            value=f"{vote_streak} votes" + (" (Reset due to expired streak)" if streak_reset else ""),
            inline=False
        )
        
        # Add rewards
        embed.add_field(
            name="Rewards",
            value=f"🪙 **Gold:** {gold_reward}\n"
                  f"✨ **EXP:** {exp_reward}\n"
                  f"⚡ **Stamina:** {stamina_reward}",
            inline=False
        )
        
        # Add level up message
        if player_level_up:
            embed.add_field(
                name="Level Up!",
                value=f"You leveled up to **Level {new_level}**!",
                inline=False
            )
        
        # Add special bonus
        if special_bonus and bonus_reward:
            embed.add_field(
                name="🎁 Special Bonus!",
                value=f"You received a bonus for your {vote_streak}th vote: **{bonus_reward}**!",
                inline=False
            )
        
        # Add next vote time
        embed.add_field(
            name="Next Vote",
            value=f"You can vote again in 12 hours!",
            inline=False
        )
        
        embed.set_footer(text="Vote every 12 hours to increase your streak and get better rewards!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="votestreak", aliases=["vs"])
    async def votestreak_command(self, ctx):
        """🗳️ Check your current vote streak"""
        user_id = ctx.author.id
        
        # Check if player has a profile
        self.cursor.execute("""
            SELECT vote_streak, last_vote 
            FROM api_players 
            WHERE discord_id = ?
        """, (user_id,))
        
        player = self.cursor.fetchone()
        
        if not player:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
            
        vote_streak, last_vote = player
        
        # Default values if NULL
        vote_streak = vote_streak or 0
        last_vote = last_vote or 0
        
        # Calculate time remaining
        time_remaining = self.get_vote_time_remaining(last_vote)
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Vote Streak",
            description=f"You have voted **{vote_streak}** times in a row!",
            color=discord.Color.blue()
        )
        
        # Add next vote information
        if time_remaining > 0:
            formatted_time = self.format_time(time_remaining)
            embed.add_field(
                name="Next Vote",
                value=f"You can vote again in **{formatted_time}**",
                inline=False
            )
        else:
            embed.add_field(
                name="Vote Now",
                value="You can vote right now! Use `!vote` to get rewards!",
                inline=False
            )
        
        # Add streak rewards information
        embed.add_field(
            name="Streak Rewards",
            value="Your rewards increase with your vote streak!\n"
                  "Every 5 votes you get a special bonus reward!",
            inline=False
        )
        
        # Add link to vote
        embed.add_field(
            name="Vote Link",
            value="[Click here to vote for the bot](https://top.gg/bot/your-bot-id)",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Vote(bot))