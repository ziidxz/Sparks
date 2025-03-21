"""
Enhanced gacha system for the anime card game.
Players can directly open gacha chests with different tiers and probabilities.
"""

import discord
from discord.ext import commands
import random
import asyncio
from discord import ui, ButtonStyle, Interaction
import time

class GachaSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        
        # Chest tiers with their costs and probabilities
        self.chest_tiers = {
            "common": {
                "cost": 500,
                "probabilities": {
                    "Common": 60, 
                    "Uncommon": 30, 
                    "Rare": 9, 
                    "Epic": 1, 
                    "Legendary": 0
                },
                "description": "Basic chest with mostly common cards",
                "icon": "🎁"
            },
            "rare": {
                "cost": 1500,
                "probabilities": {
                    "Common": 30, 
                    "Uncommon": 40, 
                    "Rare": 25, 
                    "Epic": 4, 
                    "Legendary": 1
                },
                "description": "Better chance for uncommon and rare cards",
                "icon": "🎭"
            },
            "epic": {
                "cost": 5000,
                "probabilities": {
                    "Common": 10, 
                    "Uncommon": 20, 
                    "Rare": 50, 
                    "Epic": 15, 
                    "Legendary": 5
                },
                "description": "High chance for rare and epic cards",
                "icon": "🔮"
            },
            "legendary": {
                "cost": 15000,
                "probabilities": {
                    "Common": 0, 
                    "Uncommon": 10, 
                    "Rare": 40, 
                    "Epic": 40, 
                    "Legendary": 10
                },
                "description": "Best chance for epic and legendary cards",
                "icon": "👑"
            }
        }
        
        # Material drop chances by chest tier
        self.material_drop_chances = {
            "common": 10,  # 10% chance to get a material
            "rare": 25,    # 25% chance to get a material
            "epic": 50,    # 50% chance to get a material
            "legendary": 75  # 75% chance to get a material
        }
    
    def get_player_gold(self, user_id):
        """Get player's current gold amount."""
        self.cursor.execute("SELECT gold FROM api_players WHERE discord_id = ?", (user_id,))
        result = self.cursor.fetchone()
        
        if not result:
            return 0
            
        return result[0]
    
    def deduct_gold(self, user_id, amount):
        """Deduct gold from player."""
        current_gold = self.get_player_gold(user_id)
        
        if current_gold < amount:
            return False
            
        self.cursor.execute("""
            UPDATE api_players
            SET gold = gold - ?
            WHERE discord_id = ?
        """, (amount, user_id))
        
        self.db.conn.commit()
        return True
    
    def get_random_card_by_rarity(self, rarity, series=None):
        """Get a random card of the specified rarity, optionally from a specific series."""
        if series:
            # Get a card from specific series
            self.cursor.execute("""
                SELECT id, name, attack, defense, speed, rarity, element, skill, skill_description,
                       image_url, mp_cost, anime_series
                FROM api_cards
                WHERE rarity = ? AND anime_series = ?
                ORDER BY RANDOM()
                LIMIT 1
            """, (rarity, series))
        else:
            # Get any card of this rarity
            self.cursor.execute("""
                SELECT id, name, attack, defense, speed, rarity, element, skill, skill_description,
                       image_url, mp_cost, anime_series
                FROM api_cards
                WHERE rarity = ?
                ORDER BY RANDOM()
                LIMIT 1
            """, (rarity,))
        
        card = self.cursor.fetchone()
        
        if not card:
            # Fallback to any card if no card of the specified rarity exists
            self.cursor.execute("""
                SELECT id, name, attack, defense, speed, rarity, element, skill, skill_description,
                       image_url, mp_cost, anime_series
                FROM api_cards
                ORDER BY RANDOM()
                LIMIT 1
            """)
            card = self.cursor.fetchone()
        
        if not card:
            return None
            
        # Extract data
        card_id, name, attack, defense, speed, rarity, element, skill, skill_desc, image_url, mp_cost, anime_series = card
        
        return {
            "id": card_id,
            "name": name,
            "attack": attack,
            "defense": defense,
            "speed": speed,
            "rarity": rarity,
            "element": element,
            "skill": skill,
            "skill_description": skill_desc,
            "image_url": image_url,
            "mp_cost": mp_cost,
            "anime_series": anime_series
        }
    
    def get_random_material(self, chest_tier):
        """Get a random material based on chest tier."""
        # Material rarities by chest tier
        material_rarities = {
            "common": ["Common", "Uncommon"],
            "rare": ["Common", "Uncommon", "Rare"],
            "epic": ["Uncommon", "Rare", "Epic"],
            "legendary": ["Rare", "Epic"]
        }
        
        # Get eligible rarities
        rarities = material_rarities.get(chest_tier, ["Common"])
        
        # Get a random material of eligible rarity
        rarity_placeholders = ", ".join(["?"] * len(rarities))
        
        self.cursor.execute(f"""
            SELECT id, name, description, rarity
            FROM materials
            WHERE rarity IN ({rarity_placeholders})
            ORDER BY RANDOM()
            LIMIT 1
        """, rarities)
        
        material = self.cursor.fetchone()
        
        if not material:
            return None
            
        material_id, name, description, rarity = material
        
        # Determine quantity based on rarity
        rarity_quantities = {
            "Common": (2, 5),
            "Uncommon": (1, 3),
            "Rare": (1, 2),
            "Epic": (1, 1)
        }
        
        min_qty, max_qty = rarity_quantities.get(rarity, (1, 1))
        quantity = random.randint(min_qty, max_qty)
        
        return {
            "id": material_id,
            "name": name,
            "description": description,
            "rarity": rarity,
            "quantity": quantity
        }
    
    def add_card_to_player(self, user_id, card_id):
        """Add a card to player's collection."""
        # Get player ID
        self.cursor.execute("SELECT id FROM api_players WHERE discord_id = ?", (user_id,))
        player_result = self.cursor.fetchone()
        
        if not player_result:
            return False
            
        player_id = player_result[0]
        
        # Add card to player's collection
        self.cursor.execute("""
            INSERT INTO api_user_cards (player_id, card_id, level, xp, equipped, evo_stage)
            VALUES (?, ?, 1, 0, 0, 1)
        """, (player_id, card_id))
        
        self.db.conn.commit()
        
        # Get the ID of the newly inserted card
        self.cursor.execute("SELECT last_insert_rowid()")
        user_card_id = self.cursor.fetchone()[0]
        
        return user_card_id
    
    def add_material_to_player(self, user_id, material_id, quantity):
        """Add materials to player's inventory."""
        # Get player ID
        self.cursor.execute("SELECT id FROM api_players WHERE discord_id = ?", (user_id,))
        player_result = self.cursor.fetchone()
        
        if not player_result:
            return False
            
        player_id = player_result[0]
        
        # Check if player already has this material
        self.cursor.execute("""
            SELECT id, quantity FROM user_materials
            WHERE player_id = ? AND material_id = ?
        """, (player_id, material_id))
        
        existing_material = self.cursor.fetchone()
        
        if existing_material:
            # Update quantity
            material_id, current_quantity = existing_material
            new_quantity = current_quantity + quantity
            
            self.cursor.execute("""
                UPDATE user_materials
                SET quantity = ?
                WHERE id = ?
            """, (new_quantity, material_id))
        else:
            # Insert new material
            self.cursor.execute("""
                INSERT INTO user_materials (player_id, material_id, quantity)
                VALUES (?, ?, ?)
            """, (player_id, material_id, quantity))
        
        self.db.conn.commit()
        return True
    
    def open_chest(self, user_id, chest_tier, multi_pull=False):
        """Open a gacha chest and get cards/materials."""
        # Validate chest tier
        if chest_tier not in self.chest_tiers:
            return {"success": False, "message": f"Invalid chest tier: {chest_tier}"}
        
        # Get chest details
        chest = self.chest_tiers[chest_tier]
        
        # Determine cost (discount for multi-pull)
        num_pulls = 10 if multi_pull else 1
        total_cost = chest["cost"] * num_pulls
        if multi_pull:
            # 10% discount for multi-pull
            total_cost = int(total_cost * 0.9)
        
        # Check if player has enough gold
        if not self.deduct_gold(user_id, total_cost):
            return {"success": False, "message": f"Not enough gold! You need {total_cost} gold."}
        
        # Perform pulls
        pulls = []
        materials = []
        
        for _ in range(num_pulls):
            # Determine pull rarity
            rarity = self.determine_pull_rarity(chest_tier)
            
            # Get a random card of this rarity
            card = self.get_random_card_by_rarity(rarity)
            
            if not card:
                continue
                
            # Add card to player
            user_card_id = self.add_card_to_player(user_id, card["id"])
            
            if not user_card_id:
                continue
                
            card["user_card_id"] = user_card_id
            pulls.append(card)
            
            # Check for material drop
            material_chance = self.material_drop_chances.get(chest_tier, 0)
            if random.randint(1, 100) <= material_chance:
                material = self.get_random_material(chest_tier)
                
                if material:
                    self.add_material_to_player(user_id, material["id"], material["quantity"])
                    materials.append(material)
        
        return {
            "success": True,
            "cost": total_cost,
            "pulls": pulls,
            "materials": materials
        }
    
    def determine_pull_rarity(self, chest_tier):
        """Determine the rarity of a pull based on chest tier probabilities."""
        probabilities = self.chest_tiers[chest_tier]["probabilities"]
        
        # Sum probabilities to ensure they add up to 100
        total_prob = sum(probabilities.values())
        
        # Generate a random number between 1 and total_prob
        rand = random.randint(1, total_prob)
        
        # Determine which rarity was rolled
        cumulative = 0
        for rarity, prob in probabilities.items():
            cumulative += prob
            if rand <= cumulative:
                return rarity
        
        # Fallback to common
        return "Common"
    
    @commands.command(name="gacha", aliases=["pull"])
    async def gacha_command(self, ctx, chest_tier: str = None):
        """🎮 Pull a random card from the gacha system"""
        if chest_tier is None:
            # Show available chest tiers
            embed = discord.Embed(
                title="Gacha Chests",
                description="Choose a chest tier to pull from:",
                color=discord.Color.gold()
            )
            
            # Get player's gold
            gold = self.get_player_gold(ctx.author.id)
            
            embed.add_field(
                name="Your Gold",
                value=f"💰 {gold}",
                inline=False
            )
            
            # Add chest tiers
            for tier, details in self.chest_tiers.items():
                # Format probabilities
                probs = "\n".join([f"{rarity}: {prob}%" for rarity, prob in details["probabilities"].items() if prob > 0])
                
                embed.add_field(
                    name=f"{details['icon']} {tier.capitalize()} Chest - {details['cost']} Gold",
                    value=f"{details['description']}\n**Probabilities:**\n{probs}\nUse `!gacha {tier}` to pull",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            return
        
        # Normalize chest tier
        chest_tier = chest_tier.lower()
        
        # Check if valid chest tier
        if chest_tier not in self.chest_tiers:
            valid_tiers = ", ".join(self.chest_tiers.keys())
            await ctx.send(f"{ctx.author.mention}, invalid chest tier! Valid tiers are: {valid_tiers}")
            return
        
        # Create "chest opening" animation
        opening_embed = discord.Embed(
            title="🎮 Opening Chest...",
            description=f"Opening a {chest_tier.capitalize()} chest...",
            color=discord.Color.blue()
        )
        
        message = await ctx.send(embed=opening_embed)
        
        # Simulate opening animation
        await asyncio.sleep(1)
        
        opening_embed.description = f"Opening a {chest_tier.capitalize()} chest...\n⚡ Gathering energy..."
        await message.edit(embed=opening_embed)
        
        await asyncio.sleep(1)
        
        opening_embed.description = f"Opening a {chest_tier.capitalize()} chest...\n⚡ Gathering energy...\n✨ Summoning cards..."
        await message.edit(embed=opening_embed)
        
        await asyncio.sleep(1)
        
        # Open the chest
        result = self.open_chest(ctx.author.id, chest_tier)
        
        if not result["success"]:
            # Failed to open chest
            error_embed = discord.Embed(
                title="❌ Chest Opening Failed",
                description=result["message"],
                color=discord.Color.red()
            )
            
            await message.edit(embed=error_embed)
            return
        
        # Get pulled cards
        pulls = result["pulls"]
        materials = result["materials"]
        
        if not pulls:
            # No cards pulled (shouldn't happen)
            error_embed = discord.Embed(
                title="❌ Something Went Wrong",
                description="No cards were pulled. Please try again.",
                color=discord.Color.red()
            )
            
            await message.edit(embed=error_embed)
            return
        
        # Show results
        result_embed = discord.Embed(
            title="🎮 Gacha Results",
            description=f"You spent **{result['cost']} gold** on a {chest_tier.capitalize()} chest!",
            color=discord.Color.gold()
        )
        
        # Add pulled card
        card = pulls[0]
        
        # Format card details
        card_details = f"**{card['name']}** (ID: {card['user_card_id']})\n"
        card_details += f"Rarity: {card['rarity']}\n"
        card_details += f"ATK: {card['attack']} | DEF: {card['defense']} | SPD: {card['speed']}\n"
        card_details += f"Element: {card['element']} | Series: {card['anime_series']}\n"
        card_details += f"Skill: {card['skill']} (MP: {card['mp_cost']})\n"
        card_details += f"Use `!equip {card['user_card_id']}` to equip this card"
        
        # Add rarity-based emoji
        rarity_emojis = {
            "Common": "⚪",
            "Uncommon": "🟢",
            "Rare": "🔵",
            "Epic": "🟣",
            "Legendary": "🟡"
        }
        emoji = rarity_emojis.get(card["rarity"], "⚪")
        
        result_embed.add_field(
            name=f"{emoji} {card['rarity']} Card",
            value=card_details,
            inline=False
        )
        
        # Add material drops if any
        if materials:
            material_text = ""
            for material in materials:
                material_text += f"**{material['quantity']}x {material['name']}** ({material['rarity']})\n"
                material_text += f"{material['description']}\n"
            
            result_embed.add_field(
                name="🧪 Material Drops",
                value=material_text,
                inline=False
            )
        
        # Set card image if available
        if card["image_url"]:
            result_embed.set_thumbnail(url=card["image_url"])
        
        # Add available commands
        result_embed.add_field(
            name="Available Commands",
            value=f"`!view_card {card['user_card_id']}` - View card details\n"
                  f"`!equip {card['user_card_id']}` - Equip this card\n"
                  f"`!level_up {card['user_card_id']}` - Level up this card",
            inline=False
        )
        
        await message.edit(embed=result_embed)
    
    @commands.command(name="multi_gacha", aliases=["multipull"])
    async def multi_gacha_command(self, ctx, chest_tier: str = None):
        """🎮 Pull 10 random cards from the gacha system with a discount"""
        if chest_tier is None:
            # Show available chest tiers
            embed = discord.Embed(
                title="Multi-Gacha (10 Pulls)",
                description="Choose a chest tier for 10 pulls (10% discount):",
                color=discord.Color.gold()
            )
            
            # Get player's gold
            gold = self.get_player_gold(ctx.author.id)
            
            embed.add_field(
                name="Your Gold",
                value=f"💰 {gold}",
                inline=False
            )
            
            # Add chest tiers
            for tier, details in self.chest_tiers.items():
                # Calculate discounted cost
                discounted_cost = int(details["cost"] * 10 * 0.9)
                
                # Format probabilities
                probs = "\n".join([f"{rarity}: {prob}%" for rarity, prob in details["probabilities"].items() if prob > 0])
                
                embed.add_field(
                    name=f"{details['icon']} {tier.capitalize()} Chest - {discounted_cost} Gold",
                    value=f"{details['description']}\n**Probabilities:**\n{probs}\nUse `!multi_gacha {tier}` to pull",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            return
        
        # Normalize chest tier
        chest_tier = chest_tier.lower()
        
        # Check if valid chest tier
        if chest_tier not in self.chest_tiers:
            valid_tiers = ", ".join(self.chest_tiers.keys())
            await ctx.send(f"{ctx.author.mention}, invalid chest tier! Valid tiers are: {valid_tiers}")
            return
        
        # Calculate cost
        chest_cost = self.chest_tiers[chest_tier]["cost"]
        discounted_cost = int(chest_cost * 10 * 0.9)
        
        # Check if player has enough gold
        current_gold = self.get_player_gold(ctx.author.id)
        if current_gold < discounted_cost:
            await ctx.send(f"{ctx.author.mention}, you don't have enough gold! You need {discounted_cost} gold but only have {current_gold}.")
            return
        
        # Confirm multi-pull
        confirm_embed = discord.Embed(
            title="Multi-Gacha Confirmation",
            description=f"Are you sure you want to spend **{discounted_cost} gold** for 10 pulls from {chest_tier.capitalize()} chest?",
            color=discord.Color.blue()
        )
        
        confirm_embed.add_field(
            name="Your Gold",
            value=f"💰 {current_gold}",
            inline=True
        )
        
        confirm_embed.add_field(
            name="Cost",
            value=f"💰 {discounted_cost} (10% discount)",
            inline=True
        )
        
        # Create confirmation view
        class MultiGachaConfirmView(ui.View):
            def __init__(self, cog):
                super().__init__(timeout=60)
                self.cog = cog
            
            @ui.button(label="Confirm", style=ButtonStyle.success, emoji="✅")
            async def confirm_button(self, interaction: Interaction, button: ui.Button):
                # Check if interaction is from the command author
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("This is not your gacha pull!", ephemeral=True)
                    return
                
                await interaction.response.defer()
                
                # Create "chest opening" animation
                opening_embed = discord.Embed(
                    title="🎮 Opening Multiple Chests...",
                    description=f"Opening 10 {chest_tier.capitalize()} chests...",
                    color=discord.Color.blue()
                )
                
                await interaction.message.edit(embed=opening_embed, view=None)
                
                # Simulate opening animation
                await asyncio.sleep(1)
                
                opening_embed.description = f"Opening 10 {chest_tier.capitalize()} chests...\n⚡ Gathering energy..."
                await interaction.message.edit(embed=opening_embed)
                
                await asyncio.sleep(1)
                
                opening_embed.description = f"Opening 10 {chest_tier.capitalize()} chests...\n⚡ Gathering energy...\n✨ Summoning cards..."
                await interaction.message.edit(embed=opening_embed)
                
                await asyncio.sleep(1)
                
                # Open the chests
                result = self.cog.open_chest(ctx.author.id, chest_tier, multi_pull=True)
                
                if not result["success"]:
                    # Failed to open chest
                    error_embed = discord.Embed(
                        title="❌ Chest Opening Failed",
                        description=result["message"],
                        color=discord.Color.red()
                    )
                    
                    await interaction.message.edit(embed=error_embed)
                    return
                
                # Get pulled cards
                pulls = result["pulls"]
                materials = result["materials"]
                
                if not pulls:
                    # No cards pulled (shouldn't happen)
                    error_embed = discord.Embed(
                        title="❌ Something Went Wrong",
                        description="No cards were pulled. Please try again.",
                        color=discord.Color.red()
                    )
                    
                    await interaction.message.edit(embed=error_embed)
                    return
                
                # Create embeds for each card (maximum 10)
                embeds = []
                
                # Add summary embed
                summary_embed = discord.Embed(
                    title="🎮 Multi-Gacha Results",
                    description=f"You spent **{result['cost']} gold** on 10 {chest_tier.capitalize()} chests!",
                    color=discord.Color.gold()
                )
                
                # Count cards by rarity
                rarity_counts = {}
                for card in pulls:
                    rarity = card["rarity"]
                    if rarity not in rarity_counts:
                        rarity_counts[rarity] = 0
                    rarity_counts[rarity] += 1
                
                # Add rarity summary
                rarity_text = ""
                rarity_order = ["Legendary", "Epic", "Rare", "Uncommon", "Common"]
                
                for rarity in rarity_order:
                    if rarity in rarity_counts:
                        emoji = {
                            "Common": "⚪",
                            "Uncommon": "🟢",
                            "Rare": "🔵",
                            "Epic": "🟣",
                            "Legendary": "🟡"
                        }.get(rarity, "⚪")
                        
                        rarity_text += f"{emoji} **{rarity}**: {rarity_counts[rarity]}\n"
                
                summary_embed.add_field(
                    name="Cards Pulled",
                    value=rarity_text,
                    inline=False
                )
                
                # Add material summary if any
                if materials:
                    material_text = ""
                    material_by_name = {}
                    
                    # Group materials by name
                    for material in materials:
                        name = material["name"]
                        if name not in material_by_name:
                            material_by_name[name] = 0
                        material_by_name[name] += material["quantity"]
                    
                    # Format material text
                    for name, quantity in material_by_name.items():
                        material_text += f"**{name}** x{quantity}\n"
                    
                    summary_embed.add_field(
                        name="🧪 Material Drops",
                        value=material_text,
                        inline=False
                    )
                
                embeds.append(summary_embed)
                
                # Add individual card embeds
                for card in pulls:
                    card_embed = discord.Embed(
                        title=f"{card['rarity']} Card: {card['name']}",
                        description=f"You pulled a **{card['rarity']}** card!",
                        color=discord.Color.blue()
                    )
                    
                    # Format card details
                    card_details = f"**{card['name']}** (ID: {card['user_card_id']})\n"
                    card_details += f"ATK: {card['attack']} | DEF: {card['defense']} | SPD: {card['speed']}\n"
                    card_details += f"Element: {card['element']} | Series: {card['anime_series']}\n"
                    card_details += f"Skill: {card['skill']} (MP: {card['mp_cost']})"
                    
                    card_embed.add_field(
                        name="Card Details",
                        value=card_details,
                        inline=False
                    )
                    
                    # Set card image if available
                    if card["image_url"]:
                        card_embed.set_thumbnail(url=card["image_url"])
                    
                    embeds.append(card_embed)
                
                # Use pagination if available
                pagination_cog = self.cog.bot.get_cog("Pagination")
                if pagination_cog and embeds:
                    await pagination_cog.paginate(ctx, embeds)
                elif embeds:
                    await interaction.message.edit(embed=embeds[0])
            
            @ui.button(label="Cancel", style=ButtonStyle.secondary, emoji="❌")
            async def cancel_button(self, interaction: Interaction, button: ui.Button):
                # Check if interaction is from the command author
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("This is not your gacha pull!", ephemeral=True)
                    return
                
                await interaction.response.defer()
                
                cancel_embed = discord.Embed(
                    title="Gacha Pull Cancelled",
                    description="Multi-gacha pull was cancelled.",
                    color=discord.Color.light_grey()
                )
                
                await interaction.message.edit(embed=cancel_embed, view=None)
        
        # Send confirmation message with buttons
        view = MultiGachaConfirmView(self)
        await ctx.send(embed=confirm_embed, view=view)
    
    @commands.command(name="cardlist")
    async def cardlist_command(self, ctx, anime_series: str = None, rarity: str = None):
        """📋 View all available cards in the database"""
        # Normalize parameters
        if anime_series:
            anime_series = anime_series.title()
        
        if rarity:
            rarity = rarity.capitalize()
        
        # Build query based on filters
        query = """
            SELECT id, name, rarity, element, anime_series
            FROM api_cards
        """
        
        params = []
        where_clauses = []
        
        if anime_series:
            where_clauses.append("anime_series = ?")
            params.append(anime_series)
        
        if rarity:
            where_clauses.append("rarity = ?")
            params.append(rarity)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY anime_series, rarity, name"
        
        self.cursor.execute(query, params)
        cards = self.cursor.fetchall()
        
        if not cards:
            await ctx.send(f"{ctx.author.mention}, no cards found with the specified filters!")
            return
        
        # Group cards by anime series
        cards_by_series = {}
        
        for card_id, name, card_rarity, element, series in cards:
            if series not in cards_by_series:
                cards_by_series[series] = []
                
            cards_by_series[series].append({
                "id": card_id,
                "name": name,
                "rarity": card_rarity,
                "element": element
            })
        
        # Create embeds
        embeds = []
        
        for series, card_list in cards_by_series.items():
            # Group cards in this series by rarity
            cards_by_rarity = {}
            
            for card in card_list:
                if card["rarity"] not in cards_by_rarity:
                    cards_by_rarity[card["rarity"]] = []
                    
                cards_by_rarity[card["rarity"]].append(card)
            
            # Create embed for this series
            embed = discord.Embed(
                title=f"{series} Cards",
                description=f"Available cards from the {series} series:",
                color=discord.Color.blue()
            )
            
            # Add cards grouped by rarity
            rarity_order = ["Legendary", "Epic", "Rare", "Uncommon", "Common"]
            
            for rarity in rarity_order:
                if rarity not in cards_by_rarity:
                    continue
                    
                # Format card list
                card_text = ""
                for card in cards_by_rarity[rarity]:
                    card_text += f"{card['name']} ({card['element']})\n"
                
                embed.add_field(
                    name=f"{rarity} Cards",
                    value=card_text,
                    inline=False
                )
            
            embeds.append(embed)
        
        # Use pagination if available
        pagination_cog = self.bot.get_cog("Pagination")
        if pagination_cog and embeds:
            await pagination_cog.paginate(ctx, embeds)
        elif embeds:
            await ctx.send(embed=embeds[0])
    
    @commands.command(name="chests")
    async def chests_command(self, ctx):
        """🎮 View available gacha chests and their details"""
        embed = discord.Embed(
            title="Gacha Chests",
            description="Choose a chest tier to pull from:",
            color=discord.Color.gold()
        )
        
        # Get player's gold
        gold = self.get_player_gold(ctx.author.id)
        
        embed.add_field(
            name="Your Gold",
            value=f"💰 {gold}",
            inline=False
        )
        
        # Add chest tiers
        for tier, details in self.chest_tiers.items():
            # Format probabilities
            probs = "\n".join([f"{rarity}: {prob}%" for rarity, prob in details["probabilities"].items() if prob > 0])
            
            embed.add_field(
                name=f"{details['icon']} {tier.capitalize()} Chest - {details['cost']} Gold",
                value=f"{details['description']}\n**Probabilities:**\n{probs}\n\n"
                      f"Use `!gacha {tier}` for single pull\n"
                      f"Use `!multi_gacha {tier}` for 10 pulls (10% discount)",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GachaSystem(bot))