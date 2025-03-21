import discord
from discord.ext import commands
import random

class CardExp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()

    def get_required_xp(self, level, rarity="Common"):
        """
        XP required for the next card level (scales per rarity).
        Rarer cards require more XP to level up.
        """
        rarity_multipliers = {
            "Common": 1.0,
            "Uncommon": 1.1,
            "Rare": 1.2,
            "Epic": 1.3,
            "Legendary": 1.5
        }
        
        multiplier = rarity_multipliers.get(rarity, 1.0)
        return int(50 * (1.3 ** (level - 1)) * multiplier)

    def add_card_xp(self, user_id, card_id, amount):
        """Adds XP to a card and checks for level-up."""
        self.cursor.execute(
            "SELECT level, xp, rarity, attack, defense, speed FROM usercards WHERE user_id = ? AND id = ?", 
            (user_id, card_id)
        )
        card = self.cursor.fetchone()

        if not card:
            return False, None  # Card does not exist

        level, xp, rarity, attack, defense, speed = card
        new_xp = xp + amount
        next_xp = self.get_required_xp(level, rarity)

        leveled_up = False  # Track if level increased
        orig_level = level  # Store original level

        # Level-up check
        while new_xp >= next_xp:
            new_xp -= next_xp
            level += 1
            next_xp = self.get_required_xp(level, rarity)
            leveled_up = True

        if leveled_up:
            # Calculate stat increases based on rarity
            rarity_multipliers = {
                "Common": 1.0,
                "Uncommon": 1.2,
                "Rare": 1.4,
                "Epic": 1.6,
                "Legendary": 2.0
            }
            multiplier = rarity_multipliers.get(rarity, 1.0)
            
            levels_gained = level - orig_level
            
            # Calculate stat increases
            attack_increase = int(random.randint(2, 5) * multiplier * levels_gained)
            defense_increase = int(random.randint(1, 4) * multiplier * levels_gained)
            speed_increase = int(random.randint(1, 3) * multiplier * levels_gained)
            
            # Update card stats
            self.cursor.execute("""
                UPDATE usercards 
                SET level = ?, xp = ?, 
                    attack = attack + ?, 
                    defense = defense + ?,
                    speed = speed + ?
                WHERE user_id = ? AND id = ?
            """, (level, new_xp, attack_increase, defense_increase, speed_increase, user_id, card_id))
        else:
            # Just update XP if no level up
            self.cursor.execute("UPDATE usercards SET xp = ? WHERE user_id = ? AND id = ?", 
                              (new_xp, user_id, card_id))
        
        self.db.conn.commit()
        return leveled_up, level

    @commands.command(name="cardexp")
    async def card_exp_command(self, ctx, card_id: int = None):
        """View a card's experience and level progress"""
        user_id = ctx.author.id
        
        if card_id is None:
            # If no card specified, try to get the equipped one
            self.cursor.execute("""
                SELECT id FROM usercards WHERE user_id = ? AND equipped = 1
            """, (user_id,))
            result = self.cursor.fetchone()
            
            if result:
                card_id = result[0]
            else:
                await ctx.send(f"{ctx.author.mention}, please specify a card ID or equip a card first!")
                return
        
        # Get card details
        self.cursor.execute("""
            SELECT name, level, xp, rarity, attack, defense, speed, image_url 
            FROM usercards 
            WHERE user_id = ? AND id = ?
        """, (user_id, card_id))
        
        card = self.cursor.fetchone()
        if not card:
            await ctx.send(f"{ctx.author.mention}, you don't own a card with ID `{card_id}`!")
            return
        
        name, level, xp, rarity, attack, defense, speed, image_url = card
        
        # Calculate XP needed for next level
        xp_needed = self.get_required_xp(level, rarity)
        
        # Create progress bar
        progress = min(1.0, xp / xp_needed)
        bar_length = 10
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Create embed
        from cogs.colorembed import ColorEmbed
        embed = discord.Embed(
            title=f"{name} - Level {level}",
            description=f"**Rarity:** {rarity}",
            color=ColorEmbed.get_color(rarity)
        )
        
        embed.add_field(
            name="Experience", 
            value=f"**`{bar}`** {xp}/{xp_needed}", 
            inline=False
        )
        
        embed.add_field(name="Attack", value=f"{attack}", inline=True)
        embed.add_field(name="Defense", value=f"{defense}", inline=True)
        embed.add_field(name="Speed", value=f"{speed}", inline=True)
        
        # Add stat projections for next level
        rarity_multipliers = {
            "Common": 1.0,
            "Uncommon": 1.2,
            "Rare": 1.4,
            "Epic": 1.6,
            "Legendary": 2.0
        }
        multiplier = rarity_multipliers.get(rarity, 1.0)
        
        avg_attack_inc = int(3.5 * multiplier)
        avg_defense_inc = int(2.5 * multiplier)
        avg_speed_inc = int(2 * multiplier)
        
        embed.add_field(
            name="Next Level Stats (Estimated)",
            value=f"Attack: ~{attack + avg_attack_inc}\n"
                  f"Defense: ~{defense + avg_defense_inc}\n"
                  f"Speed: ~{speed + avg_speed_inc}",
            inline=False
        )
        
        if image_url:
            embed.set_thumbnail(url=image_url)
        
        embed.set_footer(text=f"Card ID: {card_id} | Gain EXP through battles")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CardExp(bot))
