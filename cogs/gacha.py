import discord
from discord.ext import commands
import random
import time
import asyncio
from cogs.colorembed import ColorEmbed
from utils.probability import calculate_gacha_rarity

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
    
    def check_pack_ownership(self, user_id, pack_type):
        """Checks if the user owns the specified pack type."""
        self.cursor.execute("""
            SELECT ui.quantity 
            FROM user_items ui
            JOIN items i ON ui.item_id = i.id
            WHERE ui.user_id = ? AND i.effect = ? AND i.type = 'pack'
        """, (user_id, pack_type))
        
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def reduce_pack_quantity(self, user_id, pack_type):
        """Reduces the quantity of a specific pack by 1."""
        self.cursor.execute("""
            UPDATE user_items 
            SET quantity = quantity - 1
            WHERE user_id = ? AND item_id IN (
                SELECT id FROM items WHERE effect = ? AND type = 'pack'
            )
        """, (user_id, pack_type))
        
        # Clean up if quantity reaches 0
        self.cursor.execute("""
            DELETE FROM user_items
            WHERE user_id = ? AND quantity <= 0
        """, (user_id,))
        
        self.db.conn.commit()
    
    def get_card_pool(self, rarity=None):
        """Returns a list of cards filtered by rarity if specified."""
        if rarity:
            self.cursor.execute("SELECT * FROM cards WHERE rarity = ?", (rarity,))
        else:
            self.cursor.execute("SELECT * FROM cards")
        
        return self.cursor.fetchall()
    
    def create_user_card(self, user_id, card_id):
        """Creates a new card for the user based on a base card template."""
        # Get the base card data
        self.cursor.execute("""
            SELECT name, rarity, attack, defense, speed, element, skill, 
                   skill_description, skill_mp_cost, skill_cooldown, 
                   critical_rate, dodge_rate, lore, image_url
            FROM cards
            WHERE id = ?
        """, (card_id,))
        
        card_data = self.cursor.fetchone()
        
        if not card_data:
            return None
            
        # Unpack card data
        name, rarity, attack, defense, speed, element, skill, skill_desc, skill_mp, skill_cd, crit_rate, dodge_rate, lore, image_url = card_data
        
        # Insert the new card for the user
        self.cursor.execute("""
            INSERT INTO usercards (
                user_id, base_card_id, name, rarity, attack, defense, speed,
                element, skill, skill_description, skill_mp_cost, skill_cooldown,
                critical_rate, dodge_rate, level, xp, equipped, evolution_stage, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0, 0, ?)
        """, (user_id, card_id, name, rarity, attack, defense, speed, element, skill, 
              skill_desc, skill_mp, skill_cd, crit_rate, dodge_rate, image_url))
        
        self.db.conn.commit()
        
        # Return the ID of the newly created card
        return self.cursor.lastrowid
    
    @commands.command(name="gacha")
    async def gacha_command(self, ctx, pack_type: str = None):
        """Pull a random card from a gacha pack"""
        if not pack_type:
            await ctx.send(f"{ctx.author.mention}, please specify a pack type: `basic`, `premium`, or `legendary`.")
            return
        
        pack_type = pack_type.lower()
        valid_packs = ["basic", "premium", "legendary"]
        
        if pack_type not in valid_packs:
            await ctx.send(f"{ctx.author.mention}, invalid pack type! Valid options are: `basic`, `premium`, or `legendary`.")
            return
        
        user_id = ctx.author.id
        
        # Check if the user has the pack
        packs_owned = self.check_pack_ownership(user_id, pack_type)
        
        if packs_owned <= 0:
            # Check if they can buy it with gold
            self.cursor.execute("""
                SELECT cost FROM items 
                WHERE type = 'pack' AND effect = ?
                LIMIT 1
            """, (pack_type,))
            
            cost_result = self.cursor.fetchone()
            
            if not cost_result:
                await ctx.send(f"{ctx.author.mention}, that pack type is not available in the shop!")
                return
            
            cost = cost_result[0]
            
            # Check if user has enough gold
            self.cursor.execute("SELECT gold FROM players WHERE user_id = ?", (user_id,))
            gold_result = self.cursor.fetchone()
            
            if not gold_result or gold_result[0] < cost:
                await ctx.send(f"{ctx.author.mention}, you don't own any {pack_type} packs and don't have enough gold to buy one! Use `!shop` to see prices.")
                return
            
            # Deduct gold instead
            self.cursor.execute("UPDATE players SET gold = gold - ? WHERE user_id = ?", (cost, user_id))
            self.db.conn.commit()
            
            await ctx.send(f"{ctx.author.mention} spent {cost} gold on a {pack_type.capitalize()} Pack!")
        else:
            # Use an existing pack
            self.reduce_pack_quantity(user_id, pack_type)
        
        # Loading message with animation
        loading_msg = await ctx.send("🎴 **Opening pack**...")
        
        # Simulated opening animation
        for i in range(3):
            await loading_msg.edit(content=f"🎴 **Opening pack{'.'*(i+1)}**")
            await asyncio.sleep(1)
        
        # Determine card rarity based on pack type
        rarity = calculate_gacha_rarity(pack_type)
        
        # Get pool of cards with this rarity
        card_pool = self.get_card_pool(rarity)
        
        if not card_pool:
            await loading_msg.edit(content=f"❌ Error: No cards of {rarity} rarity found in the database!")
            return
        
        # Select a random card
        pulled_card = random.choice(card_pool)
        card_id = pulled_card[0]  # First column is ID
        
        # Create the card for the user
        new_card_id = self.create_user_card(user_id, card_id)
        
        if not new_card_id:
            await loading_msg.edit(content="❌ Error creating your card! Please contact an admin.")
            return
        
        # Get the user's new card data
        self.cursor.execute("""
            SELECT name, rarity, attack, defense, speed, element, skill, image_url
            FROM usercards
            WHERE id = ?
        """, (new_card_id,))
        
        user_card = self.cursor.fetchone()
        name, card_rarity, attack, defense, speed, element, skill, image_url = user_card
        
        # Create the reveal embed
        embed = discord.Embed(
            title=f"🎉 {ctx.author.display_name} pulled a new card!",
            description=f"**{name}**",
            color=ColorEmbed.get_color(card_rarity)
        )
        
        embed.add_field(name="Rarity", value=card_rarity, inline=True)
        embed.add_field(name="Element", value=element, inline=True)
        embed.add_field(name="Card ID", value=f"`{new_card_id}`", inline=True)
        
        embed.add_field(name="Attack", value=str(attack), inline=True)
        embed.add_field(name="Defense", value=str(defense), inline=True)
        embed.add_field(name="Speed", value=str(speed), inline=True)
        
        embed.add_field(name=f"Skill: {skill}", value="Use `!view {new_card_id}` to see skill details", inline=False)
        
        # Add rarity-specific flavor text
        if card_rarity == "Legendary":
            embed.set_footer(text="✨ LEGENDARY! What incredible luck! ✨")
        elif card_rarity == "Epic":
            embed.set_footer(text="🔥 EPIC! An amazing pull! 🔥")
        elif card_rarity == "Rare":
            embed.set_footer(text="💫 RARE! A great find! 💫")
        
        # Set card image if available
        if image_url:
            embed.set_image(url=image_url)
        
        await loading_msg.edit(content=None, embed=embed)
    
    @commands.command(name="multidraw", aliases=["multi"])
    async def multi_draw_command(self, ctx, pack_type: str = None, amount: int = 10):
        """Draw multiple cards at once (up to 10)"""
        if not pack_type:
            await ctx.send(f"{ctx.author.mention}, please specify a pack type: `basic`, `premium`, or `legendary`.")
            return
        
        pack_type = pack_type.lower()
        valid_packs = ["basic", "premium", "legendary"]
        
        if pack_type not in valid_packs:
            await ctx.send(f"{ctx.author.mention}, invalid pack type! Valid options are: `basic`, `premium`, or `legendary`.")
            return
        
        # Cap the amount at 10
        if amount > 10:
            amount = 10
            await ctx.send(f"{ctx.author.mention}, maximum multi-draw is 10 cards. Setting to 10.")
        elif amount < 1:
            amount = 1
        
        user_id = ctx.author.id
        
        # Check how many packs the user has
        packs_owned = self.check_pack_ownership(user_id, pack_type)
        
        # Check if user can afford with gold if they don't have enough packs
        self.cursor.execute("""
            SELECT cost FROM items 
            WHERE type = 'pack' AND effect = ?
            LIMIT 1
        """, (pack_type,))
        
        cost_result = self.cursor.fetchone()
        if not cost_result:
            await ctx.send(f"{ctx.author.mention}, that pack type is not available in the shop!")
            return
        
        pack_cost = cost_result[0]
        total_cost = pack_cost * amount
        
        # Check if user has enough gold
        self.cursor.execute("SELECT gold FROM players WHERE user_id = ?", (user_id,))
        gold_result = self.cursor.fetchone()
        
        if not gold_result:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
        
        current_gold = gold_result[0]
        
        # Calculate how many packs to use and how much gold to spend
        packs_to_use = min(packs_owned, amount)
        packs_to_buy = amount - packs_to_use
        gold_needed = packs_to_buy * pack_cost
        
        if current_gold < gold_needed:
            affordable = packs_to_use + (current_gold // pack_cost)
            if affordable == 0:
                await ctx.send(f"{ctx.author.mention}, you don't have enough packs or gold for this draw!")
                return
            else:
                await ctx.send(f"{ctx.author.mention}, you can only afford {affordable} draws. Proceeding with {affordable} draws.")
                amount = affordable
                packs_to_use = min(packs_owned, amount)
                packs_to_buy = amount - packs_to_use
                gold_needed = packs_to_buy * pack_cost
        
        # Deduct packs and gold
        if packs_to_use > 0:
            for _ in range(packs_to_use):
                self.reduce_pack_quantity(user_id, pack_type)
        
        if gold_needed > 0:
            self.cursor.execute("UPDATE players SET gold = gold - ? WHERE user_id = ?", (gold_needed, user_id))
            self.db.conn.commit()
        
        # Loading message
        loading_msg = await ctx.send(f"🎴 **Opening {amount} {pack_type.capitalize()} Packs**...")
        
        # Draw the cards
        cards_drawn = []
        rarities_count = {"Common": 0, "Uncommon": 0, "Rare": 0, "Epic": 0, "Legendary": 0}
        
        for _ in range(amount):
            # Determine card rarity
            rarity = calculate_gacha_rarity(pack_type)
            rarities_count[rarity] += 1
            
            # Get pool of cards with this rarity
            card_pool = self.get_card_pool(rarity)
            
            if not card_pool:
                continue
            
            # Select a random card
            pulled_card = random.choice(card_pool)
            card_id = pulled_card[0]
            
            # Create the card for the user
            new_card_id = self.create_user_card(user_id, card_id)
            
            if new_card_id:
                # Get the user's new card data
                self.cursor.execute("""
                    SELECT id, name, rarity
                    FROM usercards
                    WHERE id = ?
                """, (new_card_id,))
                
                user_card = self.cursor.fetchone()
                cards_drawn.append(user_card)
        
        # Create summary embed
        embed = discord.Embed(
            title=f"🎉 {ctx.author.display_name}'s {amount}-Card Draw Results",
            description=f"**Pack Type:** {pack_type.capitalize()}",
            color=discord.Color.gold()
        )
        
        # Add rarity summary
        rarity_summary = "\n".join([f"**{rarity}:** {count}" for rarity, count in rarities_count.items() if count > 0])
        embed.add_field(name="Rarity Summary", value=rarity_summary, inline=False)
        
        # Add card list
        card_list = ""
        for card_id, name, rarity in cards_drawn:
            rarity_emoji = "✨" if rarity == "Legendary" else "🔥" if rarity == "Epic" else "💫" if rarity == "Rare" else "⭐"
            card_list += f"{rarity_emoji} **{name}** ({rarity}) - ID: `{card_id}`\n"
        
        embed.add_field(name="Cards Obtained", value=card_list if card_list else "No cards drawn", inline=False)
        
        # Resource summary
        if packs_to_use > 0 and gold_needed > 0:
            resource_text = f"Used {packs_to_use} owned packs and {gold_needed} gold"
        elif packs_to_use > 0:
            resource_text = f"Used {packs_to_use} owned packs"
        else:
            resource_text = f"Spent {gold_needed} gold"
        
        embed.add_field(name="Resources Used", value=resource_text, inline=False)
        
        embed.set_footer(text="Use !view [card_id] to see card details")
        
        await loading_msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(Gacha(bot))
