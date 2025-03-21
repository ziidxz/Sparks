import discord
from discord.ext import commands
import math

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.items_per_page = 5  # Number of items to display per page
    
    @commands.command(name="shop")
    async def shop_command(self, ctx, category: str = None, page: int = 1):
        """Browse the shop for items and card packs"""
        if category and category.lower() not in ["all", "potions", "boosts", "packs", "materials"]:
            await ctx.send(f"{ctx.author.mention}, valid categories are: `all`, `potions`, `boosts`, `packs`, `materials`")
            return
        
        # If no category specified, show all items
        if not category:
            category = "all"
        else:
            category = category.lower()
            
        # Get player's gold for reference
        self.cursor.execute("SELECT gold FROM players WHERE user_id = ?", (ctx.author.id,))
        result = self.cursor.fetchone()
        player_gold = result[0] if result else 0
        
        # Construct category filter for SQL
        if category == "all":
            category_filter = ""
        elif category == "potions":
            category_filter = "WHERE type = 'potion'"
        elif category == "boosts":
            category_filter = "WHERE type = 'boost'"
        elif category == "packs":
            category_filter = "WHERE type = 'pack'"
        elif category == "materials":
            category_filter = "WHERE type = 'material'"
        
        # Get total count of items in this category
        self.cursor.execute(f"SELECT COUNT(*) FROM items {category_filter}")
        total_items = self.cursor.fetchone()[0]
        
        if total_items == 0:
            await ctx.send(f"{ctx.author.mention}, there are no items available in this category!")
            return
        
        # Calculate total pages
        total_pages = math.ceil(total_items / self.items_per_page)
        
        # Generate all page embeds
        embeds = []
        for current_page in range(1, total_pages + 1):
            # Calculate offset
            offset = (current_page - 1) * self.items_per_page
            
            # Get items for the current page
            self.cursor.execute(f"""
                SELECT id, name, description, type, effect, cost, image_url
                FROM items
                {category_filter}
                ORDER BY cost ASC, name ASC
                LIMIT ? OFFSET ?
            """, (self.items_per_page, offset))
            
            items = self.cursor.fetchall()
            
            # Create shop embed for this page
            embed = discord.Embed(
                title="🛒 Card Battle Shop",
                description=f"Your Gold: 💰 **{player_gold}**",
                color=discord.Color.gold()
            )
            
            # Add category information
            categories = "`all` `potions` `boosts` `packs` `materials`"
            embed.add_field(
                name="Categories",
                value=f"Currently viewing: **{category}**\nAvailable: {categories}",
                inline=False
            )
            
            # Add items to the embed
            for item_id, name, description, item_type, effect, cost, image_url in items:
                # Format cost with emoji and determine if player can afford
                can_afford = player_gold >= cost
                cost_display = f"💰 **{cost}**" if can_afford else f"💰 ~~{cost}~~"
                
                # Add type-specific emojis
                if item_type == "potion":
                    emoji = "⚡" if effect == "stamina" else "🔷" if effect == "mp" else "🧪"
                elif item_type == "boost":
                    emoji = "✨" if effect == "exp" else "💰" if effect == "gold" else "🔆"
                elif item_type == "pack":
                    emoji = "🎁" if effect == "basic" else "🎭" if effect == "premium" else "👑"
                elif item_type == "material":
                    emoji = "🔮"
                else:
                    emoji = "📦"
                
                embed.add_field(
                    name=f"{emoji} {name}",
                    value=f"{description}\n{cost_display}\nBuy with `!buy {name}`",
                    inline=False
                )
            
            embed.set_footer(text=f"Use the buttons below to browse items")
            embeds.append(embed)
        
        # Use the pagination system
        pagination_cog = self.bot.get_cog("Pagination")
        if pagination_cog:
            await pagination_cog.paginate(ctx, embeds)
        else:
            # Fallback if pagination cog isn't loaded
            if embeds:
                await ctx.send(embed=embeds[0])
    
    @commands.command(name="market")
    async def market_command(self, ctx):
        """View the daily special offers in the market"""
        # This is a simplified version that could be expanded with daily rotating items
        import time
        import random
        
        # Get player's gold for reference
        self.cursor.execute("SELECT gold FROM players WHERE user_id = ?", (ctx.author.id,))
        result = self.cursor.fetchone()
        player_gold = result[0] if result else 0
        
        # Get current day (changes at midnight UTC)
        current_day = int(time.time() // 86400)
        
        # Seed the RNG with the current day for consistent daily offers
        random.seed(current_day)
        
        # Get all available items
        self.cursor.execute("SELECT id, name, description, type, effect, cost FROM items")
        all_items = self.cursor.fetchall()
        
        if not all_items:
            await ctx.send(f"{ctx.author.mention}, there are no items available in the market!")
            return
        
        # Select 3 random items for the daily special
        daily_items = random.sample(all_items, min(3, len(all_items)))
        
        # Apply a random discount between 10% and 30%
        discounted_items = []
        for item in daily_items:
            item_id, name, description, item_type, effect, cost = item
            discount = random.randint(10, 30) / 100
            discounted_cost = int(cost * (1 - discount))
            discounted_items.append((item_id, name, description, item_type, effect, cost, discounted_cost, int(discount * 100)))
        
        # Create market embed
        embed = discord.Embed(
            title="🏪 Daily Market Specials",
            description=f"Your Gold: 💰 **{player_gold}**\nSpecial offers for today:",
            color=discord.Color.teal()
        )
        
        # Add each discounted item
        for item_id, name, description, item_type, effect, original_cost, discounted_cost, discount_percent in discounted_items:
            # Determine if player can afford
            can_afford = player_gold >= discounted_cost
            cost_display = f"💰 **{discounted_cost}** (~~{original_cost}~~)" if can_afford else f"💰 ~~{discounted_cost}~~ (~~{original_cost}~~)"
            
            # Add type-specific emojis
            if item_type == "potion":
                emoji = "⚡" if effect == "stamina" else "🔷" if effect == "mp" else "🧪"
            elif item_type == "boost":
                emoji = "✨" if effect == "exp" else "💰" if effect == "gold" else "🔆"
            elif item_type == "pack":
                emoji = "🎁" if effect == "basic" else "🎭" if effect == "premium" else "👑"
            else:
                emoji = "📦"
            
            embed.add_field(
                name=f"{emoji} {name} (-{discount_percent}%)",
                value=f"{description}\n{cost_display}\nBuy with `!buy {name}`",
                inline=False
            )
        
        # Add timer for next refresh
        import datetime
        now = datetime.datetime.utcnow()
        midnight = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time())
        seconds_to_midnight = (midnight - now).total_seconds()
        hours = int(seconds_to_midnight // 3600)
        minutes = int((seconds_to_midnight % 3600) // 60)
        
        embed.set_footer(text=f"Market refreshes in {hours}h {minutes}m")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Shop(bot))
