import discord
from discord.ext import commands
import time

class Buy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.active_boosts = {}  # {user_id: {boost_type: expiry_timestamp}}

    @commands.command(name="buy")
    async def buy_command(self, ctx, *, item_name: str):
        """Purchase an item from the shop"""
        user_id = ctx.author.id

        # Normalize input: remove spaces & make lowercase
        item_name_normalized = "".join(item_name.lower().split())

        # Get all items from database
        self.cursor.execute("SELECT id, name, description, type, effect, cost FROM items")
        items = self.cursor.fetchall()
        
        if not items:
            await ctx.send(f"{ctx.author.mention}, the shop is currently empty. Please try again later.")
            return

        # Find the best match for the requested item
        matched_item = None
        for item_id, name, desc, item_type, effect, cost in items:
            normalized_name = "".join(name.lower().split())
            if item_name_normalized in normalized_name or normalized_name in item_name_normalized:
                matched_item = (item_id, name, desc, item_type, effect, cost)
                break

        if not matched_item:
            await ctx.send(f"{ctx.author.mention}, that item doesn't exist! Use `!shop` to see available items.")
            return

        item_id, name, desc, item_type, effect, cost = matched_item

        # Check player's balance
        self.cursor.execute("SELECT gold FROM players WHERE user_id = ?", (user_id,))
        player = self.cursor.fetchone()

        if not player:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return

        gold = player[0]
        if gold < cost:
            await ctx.send(f"{ctx.author.mention}, you don't have enough gold! 💰 `{cost}` needed.")
            return

        # Deduct gold
        self.cursor.execute("UPDATE players SET gold = gold - ? WHERE user_id = ?", (cost, user_id))

        # Handle different item types
        if item_type == "potion":
            if effect == "stamina":
                self.cursor.execute("UPDATE players SET stamina = stamina + 5 WHERE user_id = ?", (user_id,))
                await ctx.send(f"{ctx.author.mention}, you bought a **{name}**! ⚡ (+5 Stamina)")
            
            elif effect == "mp":
                self.cursor.execute("UPDATE players SET mp = mp + 50 WHERE user_id = ?", (user_id,))
                await ctx.send(f"{ctx.author.mention}, you bought a **{name}**! 🔷 (+50 MP)")
            
            else:
                await ctx.send(f"{ctx.author.mention}, you bought a **{name}**!")

        elif item_type == "boost":
            # Set boost duration (1 hour)
            boost_duration = 3600
            expiry = int(time.time()) + boost_duration
            
            # Store the boost in memory
            if user_id not in self.active_boosts:
                self.active_boosts[user_id] = {}
            
            self.active_boosts[user_id][effect] = expiry
            
            # Add to user items
            self.cursor.execute("SELECT id FROM user_items WHERE user_id = ? AND item_id = ?", 
                              (user_id, item_id))
            existing_item = self.cursor.fetchone()
            
            if existing_item:
                self.cursor.execute("UPDATE user_items SET quantity = quantity + 1 WHERE user_id = ? AND item_id = ?", 
                                  (user_id, item_id))
            else:
                self.cursor.execute("INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, ?, 1)", 
                                  (user_id, item_id))
            
            # Hours and minutes formatting
            hours = boost_duration // 3600
            minutes = (boost_duration % 3600) // 60
            time_str = f"{hours}h {minutes}m"
            
            await ctx.send(f"{ctx.author.mention}, you bought a **{name}**! ⏱️ (Active for {time_str})")

        elif item_type == "pack":
            # Add to user items
            self.cursor.execute("SELECT id FROM user_items WHERE user_id = ? AND item_id = ?", 
                              (user_id, item_id))
            existing_item = self.cursor.fetchone()
            
            if existing_item:
                self.cursor.execute("UPDATE user_items SET quantity = quantity + 1 WHERE user_id = ? AND item_id = ?", 
                                  (user_id, item_id))
            else:
                self.cursor.execute("INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, ?, 1)", 
                                  (user_id, item_id))
            
            await ctx.send(f"{ctx.author.mention}, you bought a **{name}**! 🎴 Use `!gacha {effect}` to pull your card!")

        else:
            # Generic item, add to user inventory
            self.cursor.execute("SELECT id FROM user_items WHERE user_id = ? AND item_id = ?", 
                              (user_id, item_id))
            existing_item = self.cursor.fetchone()
            
            if existing_item:
                self.cursor.execute("UPDATE user_items SET quantity = quantity + 1 WHERE user_id = ? AND item_id = ?", 
                                  (user_id, item_id))
            else:
                self.cursor.execute("INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, ?, 1)", 
                                  (user_id, item_id))
            
            await ctx.send(f"{ctx.author.mention}, you bought a **{name}**!")

        self.db.conn.commit()

    @commands.command(name="use")
    async def use_command(self, ctx, *, item_name: str):
        """Use an item from your inventory"""
        user_id = ctx.author.id

        # Normalize input: remove spaces & make lowercase
        item_name_normalized = "".join(item_name.lower().split())

        # Get user's items
        self.cursor.execute("""
            SELECT i.id, i.name, i.description, i.type, i.effect, ui.quantity
            FROM items i
            JOIN user_items ui ON i.id = ui.item_id
            WHERE ui.user_id = ?
        """, (user_id,))
        
        user_items = self.cursor.fetchall()
        
        if not user_items:
            await ctx.send(f"{ctx.author.mention}, you don't have any items in your inventory!")
            return

        # Find the best match for the requested item
        matched_item = None
        for item_id, name, desc, item_type, effect, quantity in user_items:
            normalized_name = "".join(name.lower().split())
            if item_name_normalized in normalized_name or normalized_name in item_name_normalized:
                if quantity > 0:  # Make sure user has at least one
                    matched_item = (item_id, name, desc, item_type, effect, quantity)
                    break

        if not matched_item:
            await ctx.send(f"{ctx.author.mention}, you don't have that item in your inventory!")
            return

        item_id, name, desc, item_type, effect, quantity = matched_item

        # Decrease quantity
        self.cursor.execute("UPDATE user_items SET quantity = quantity - 1 WHERE user_id = ? AND item_id = ?", 
                          (user_id, item_id))
        
        # If quantity becomes 0, remove the entry
        self.cursor.execute("DELETE FROM user_items WHERE user_id = ? AND item_id = ? AND quantity <= 0", 
                          (user_id, item_id))

        # Handle different item types
        if item_type == "potion":
            if effect == "stamina":
                self.cursor.execute("UPDATE players SET stamina = min(stamina + 5, max_stamina) WHERE user_id = ?", (user_id,))
                
                # Get new stamina value
                self.cursor.execute("SELECT stamina, max_stamina FROM players WHERE user_id = ?", (user_id,))
                stamina, max_stamina = self.cursor.fetchone()
                
                await ctx.send(f"{ctx.author.mention}, you used a **{name}**! ⚡ Your stamina is now `{stamina}/{max_stamina}`")
            
            elif effect == "mp":
                self.cursor.execute("UPDATE players SET mp = min(mp + 50, max_mp) WHERE user_id = ?", (user_id,))
                
                # Get new MP value
                self.cursor.execute("SELECT mp, max_mp FROM players WHERE user_id = ?", (user_id,))
                mp, max_mp = self.cursor.fetchone()
                
                await ctx.send(f"{ctx.author.mention}, you used a **{name}**! 🔷 Your MP is now `{mp}/{max_mp}`")
            
            else:
                await ctx.send(f"{ctx.author.mention}, you used a **{name}**!")

        elif item_type == "boost":
            # Set boost duration (1 hour)
            boost_duration = 3600
            expiry = int(time.time()) + boost_duration
            
            # Store the boost in memory
            if user_id not in self.active_boosts:
                self.active_boosts[user_id] = {}
            
            self.active_boosts[user_id][effect] = expiry
            
            # Hours and minutes formatting
            hours = boost_duration // 3600
            minutes = (boost_duration % 3600) // 60
            time_str = f"{hours}h {minutes}m"
            
            await ctx.send(f"{ctx.author.mention}, you activated a **{name}**! ⏱️ (Active for {time_str})")

        elif item_type == "pack":
            # Return the item since it should be opened with gacha command
            self.cursor.execute("UPDATE user_items SET quantity = quantity + 1 WHERE user_id = ? AND item_id = ?", 
                              (user_id, item_id))
            
            await ctx.send(f"{ctx.author.mention}, card packs can only be opened with the `!gacha {effect}` command!")

        else:
            await ctx.send(f"{ctx.author.mention}, you used a **{name}**!")

        self.db.conn.commit()

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory_command(self, ctx):
        """View your item inventory"""
        user_id = ctx.author.id

        # Get user's items
        self.cursor.execute("""
            SELECT i.id, i.name, i.description, i.type, ui.quantity
            FROM items i
            JOIN user_items ui ON i.id = ui.item_id
            WHERE ui.user_id = ? AND ui.quantity > 0
        """, (user_id,))
        
        user_items = self.cursor.fetchall()
        
        if not user_items:
            await ctx.send(f"{ctx.author.mention}, you don't have any items in your inventory!")
            return

        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Item Inventory",
            color=discord.Color.blue()
        )
        
        # Group items by type
        item_types = {}
        for item_id, name, desc, item_type, quantity in user_items:
            if item_type not in item_types:
                item_types[item_type] = []
            
            item_types[item_type].append((item_id, name, desc, quantity))
        
        # Add fields for each item type
        for item_type, items in item_types.items():
            field_value = ""
            for item_id, name, desc, quantity in items:
                field_value += f"**{name}** (x{quantity})\n{desc}\n\n"
            
            embed.add_field(
                name=f"{item_type.capitalize()}s",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text="Use !use [item name] to use an item")
        
        await ctx.send(embed=embed)

    def is_boost_active(self, user_id, boost_type):
        """Check if a user has an active boost"""
        if user_id in self.active_boosts and boost_type in self.active_boosts[user_id]:
            expiry = self.active_boosts[user_id][boost_type]
            current_time = int(time.time())
            
            if current_time < expiry:
                return True, expiry - current_time
            else:
                # Clean up expired boost
                del self.active_boosts[user_id][boost_type]
                if not self.active_boosts[user_id]:
                    del self.active_boosts[user_id]
        
        return False, 0

    @commands.command(name="boosts")
    async def boosts_command(self, ctx):
        """View your active boosts"""
        user_id = ctx.author.id
        
        if user_id not in self.active_boosts or not self.active_boosts[user_id]:
            await ctx.send(f"{ctx.author.mention}, you don't have any active boosts!")
            return
        
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Active Boosts",
            color=discord.Color.gold()
        )
        
        current_time = int(time.time())
        
        for boost_type, expiry in list(self.active_boosts[user_id].items()):
            if current_time < expiry:
                time_left = expiry - current_time
                hours = time_left // 3600
                minutes = (time_left % 3600) // 60
                seconds = time_left % 60
                
                boost_name = boost_type.capitalize()
                if boost_type == "exp":
                    boost_name = "EXP"
                
                embed.add_field(
                    name=f"{boost_name} Boost",
                    value=f"Time remaining: {hours}h {minutes}m {seconds}s",
                    inline=False
                )
            else:
                # Clean up expired boost
                del self.active_boosts[user_id][boost_type]
        
        if not self.active_boosts[user_id]:
            del self.active_boosts[user_id]
            await ctx.send(f"{ctx.author.mention}, you don't have any active boosts!")
            return
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Buy(bot))
