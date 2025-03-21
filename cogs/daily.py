import discord
from discord.ext import commands
import time
import random

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
    
    @commands.command(name="daily")
    async def daily_command(self, ctx):
        """Collect your daily rewards"""
        user_id = ctx.author.id
        
        # Check if user has a profile
        self.cursor.execute("SELECT last_daily FROM players WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        
        if not result:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` to create a profile first!")
            return
        
        last_daily = result[0]
        current_time = int(time.time())
        
        # Check if daily reset is available (24 hours = 86400 seconds)
        if last_daily > 0 and current_time - last_daily < 86400:
            # Calculate time remaining
            time_remaining = 86400 - (current_time - last_daily)
            hours = time_remaining // 3600
            minutes = (time_remaining % 3600) // 60
            
            await ctx.send(f"{ctx.author.mention}, you've already claimed your daily rewards! Check back in **{hours}h {minutes}m**.")
            return
        
        # Get streak info
        self.cursor.execute("SELECT daily_streak FROM players WHERE user_id = ?", (user_id,))
        streak_result = self.cursor.fetchone()
        
        streak = 0
        if streak_result and streak_result[0] is not None:
            streak = streak_result[0]
        
        # Check if streak should be reset (more than 48 hours since last daily)
        if last_daily > 0 and current_time - last_daily >= 172800:  # 48 hours
            streak = 0
        
        # Increment streak
        streak += 1
        
        # Calculate rewards based on streak
        base_gold = 100
        gold_per_streak = 50
        gold_reward = base_gold + (gold_per_streak * min(streak, 7))  # Cap at 7 days for gold bonus
        
        # Stamina refill
        self.cursor.execute("SELECT stamina, max_stamina FROM players WHERE user_id = ?", (user_id,))
        stamina_data = self.cursor.fetchone()
        current_stamina, max_stamina = stamina_data
        
        # Additional rewards based on streak
        bonus_rewards = []
        material_reward = None
        pack_reward = None
        
        if streak % 7 == 0:  # Every 7 days (weekly bonus)
            # Give a premium pack
            self.cursor.execute("""
                SELECT id FROM items 
                WHERE type = 'pack' AND effect = 'premium'
                LIMIT 1
            """)
            pack_item = self.cursor.fetchone()
            
            if pack_item:
                pack_id = pack_item[0]
                # Check if user already has this item
                self.cursor.execute("""
                    SELECT id, quantity FROM user_items
                    WHERE user_id = ? AND item_id = ?
                """, (user_id, pack_id))
                
                existing_item = self.cursor.fetchone()
                
                if existing_item:
                    # Update quantity
                    self.cursor.execute("""
                        UPDATE user_items
                        SET quantity = quantity + 1
                        WHERE id = ?
                    """, (existing_item[0],))
                else:
                    # Add new item
                    self.cursor.execute("""
                        INSERT INTO user_items (user_id, item_id, quantity)
                        VALUES (?, ?, 1)
                    """, (user_id, pack_id))
                
                pack_reward = "Premium Card Pack"
                bonus_rewards.append("🎁 1x Premium Card Pack")
        
        elif streak % 3 == 0:  # Every 3 days
            # Give a random material
            self.cursor.execute("SELECT id, name FROM materials ORDER BY RANDOM() LIMIT 1")
            material_data = self.cursor.fetchone()
            
            if material_data:
                material_id, material_name = material_data
                
                # Check if user already has this material
                self.cursor.execute("""
                    SELECT id, quantity FROM user_materials
                    WHERE user_id = ? AND material_id = ?
                """, (user_id, material_id))
                
                existing_material = self.cursor.fetchone()
                
                if existing_material:
                    # Update quantity
                    self.cursor.execute("""
                        UPDATE user_materials
                        SET quantity = quantity + 2
                        WHERE id = ?
                    """, (existing_material[0],))
                else:
                    # Add new material
                    self.cursor.execute("""
                        INSERT INTO user_materials (user_id, material_id, quantity)
                        VALUES (?, ?, 2)
                    """, (user_id, material_id))
                
                material_reward = material_name
                bonus_rewards.append(f"🔮 2x {material_name}")
        
        # Update daily streak and timestamp
        self.cursor.execute("""
            UPDATE players
            SET last_daily = ?, daily_streak = ?,
                gold = gold + ?, stamina = ?
            WHERE user_id = ?
        """, (current_time, streak, gold_reward, max_stamina, user_id))
        
        self.db.conn.commit()
        
        # Create reward embed
        embed = discord.Embed(
            title="🎁 Daily Rewards Claimed!",
            description=f"You've claimed your daily rewards, {ctx.author.display_name}!",
            color=discord.Color.gold()
        )
        
        # Main rewards
        embed.add_field(
            name="Daily Rewards",
            value=f"💰 {gold_reward} Gold\n"
                  f"⚡ Stamina refilled to {max_stamina}/{max_stamina}",
            inline=False
        )
        
        # Streak info
        if streak > 1:
            embed.add_field(
                name="Login Streak",
                value=f"🔥 {streak} day{'s' if streak != 1 else ''} streak!",
                inline=True
            )
        
        # Bonus rewards
        if bonus_rewards:
            embed.add_field(
                name="Bonus Rewards",
                value="\n".join(bonus_rewards),
                inline=True
            )
        
        # Next milestone
        if streak % 7 == 0:
            next_milestone = "You've reached a weekly milestone! Keep it up!"
        else:
            days_to_weekly = 7 - (streak % 7)
            next_milestone = f"Weekly bonus in {days_to_weekly} day{'s' if days_to_weekly != 1 else ''}!"
            
            if streak % 3 == 0:
                next_3day = f"You've reached a 3-day milestone!"
            else:
                days_to_3day = 3 - (streak % 3)
                next_milestone += f"\nMaterial bonus in {days_to_3day} day{'s' if days_to_3day != 1 else ''}!"
        
        embed.add_field(
            name="Next Milestone",
            value=next_milestone,
            inline=False
        )
        
        # Random tip
        tips = [
            "Battle bosses for rare materials!",
            "Evolve your cards to make them stronger!",
            "Don't forget to equip your strongest card!",
            "Trade with other players to complete your collection!",
            "Check the market daily for special offers!",
            "PvP battles give more gold than regular battles!",
            "Save your diamonds for legendary card packs!"
        ]
        
        embed.set_footer(text=f"💡 Tip: {random.choice(tips)} • Come back tomorrow for more rewards!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="streak")
    async def streak_command(self, ctx):
        """View your current daily streak and upcoming rewards"""
        user_id = ctx.author.id
        
        # Check if user has a profile
        self.cursor.execute("""
            SELECT last_daily, daily_streak
            FROM players
            WHERE user_id = ?
        """, (user_id,))
        
        result = self.cursor.fetchone()
        
        if not result:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` to create a profile first!")
            return
        
        last_daily, streak = result
        
        if streak is None:
            streak = 0
        
        # Check if streak is active
        current_time = int(time.time())
        time_since_last = current_time - last_daily if last_daily else float('inf')
        
        streak_active = time_since_last < 172800  # 48 hours
        can_claim_today = time_since_last >= 86400  # 24 hours
        
        # Calculate time until next daily
        if not can_claim_today and last_daily:
            time_remaining = 86400 - time_since_last
            hours = time_remaining // 3600
            minutes = (time_remaining % 3600) // 60
            time_text = f"{hours}h {minutes}m"
        else:
            time_text = "Available now!"
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Daily Streak",
            description=f"Current Streak: 🔥 **{streak} day{'s' if streak != 1 else ''}**",
            color=discord.Color.gold() if streak_active else discord.Color.light_grey()
        )
        
        # Streak status
        status_text = "✅ Active" if streak_active else "❌ Broken"
        if not streak_active and streak > 0:
            status_text += " (streak will reset on next claim)"
        
        embed.add_field(
            name="Streak Status",
            value=status_text,
            inline=True
        )
        
        # Next daily claim
        embed.add_field(
            name="Next Daily Claim",
            value=time_text,
            inline=True
        )
        
        # Upcoming rewards
        days_to_3day = 3 - (streak % 3) if streak_active else 3
        days_to_weekly = 7 - (streak % 7) if streak_active else 7
        
        embed.add_field(
            name="Upcoming Rewards",
            value=f"Material bonus: {days_to_3day} day{'s' if days_to_3day != 1 else ''}\n"
                  f"Premium pack: {days_to_weekly} day{'s' if days_to_weekly != 1 else ''}",
            inline=False
        )
        
        # Daily rewards explanation
        embed.add_field(
            name="Daily Rewards",
            value=f"• Base Gold: 100 + (50 × streak) up to 450\n"
                  f"• Full stamina refill\n"
                  f"• Every 3 days: Bonus materials\n"
                  f"• Every 7 days: Premium card pack",
            inline=False
        )
        
        embed.set_footer(text="Use !daily to claim your rewards • Streak resets if you miss 2 days")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Daily(bot))
