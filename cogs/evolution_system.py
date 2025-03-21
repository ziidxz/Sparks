"""
Evolution system module for the anime card game.
Allows players to evolve their cards to increase their power and unlock more levels.
"""

import discord
from discord.ext import commands
import random
from discord import ui, ButtonStyle, Interaction

class EvolutionSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
    
    def get_user_card(self, user_id, card_id):
        """Get detailed information about a user's card."""
        self.cursor.execute("""
            SELECT uc.id, c.id AS base_card_id, c.name, uc.level, c.rarity,
                   c.attack, c.defense, c.speed, c.element, c.skill, c.skill_description,
                   c.image_url, c.mp_cost, uc.evo_stage, c.max_evo, c.anime_series,
                   uc.xp, uc.equipped
            FROM api_user_cards uc
            JOIN api_cards c ON uc.card_id = c.id
            WHERE uc.player_id = (SELECT id FROM api_players WHERE discord_id = ?)
            AND uc.id = ?
        """, (user_id, card_id))
        
        card_data = self.cursor.fetchone()
        if not card_data:
            return None
        
        # Extract card details
        card_id, base_card_id, name, level, rarity, attack, defense, speed, element, skill, skill_desc, \
        image_url, mp_cost, evo_stage, max_evo, anime_series, xp, equipped = card_data
        
        # Calculate stats based on level and rarity
        rarity_multiplier = {"Common": 1.0, "Uncommon": 1.2, "Rare": 1.5, "Epic": 2.0, "Legendary": 2.5}
        multiplier = rarity_multiplier.get(rarity, 1.0)
        
        # Stats increase with level and evolution
        level_bonus = (level - 1) * 0.1 * multiplier
        evo_bonus = (evo_stage - 1) * 0.2
        
        attack = int(attack * (1 + level_bonus + evo_bonus))
        defense = int(defense * (1 + level_bonus + evo_bonus))
        speed = int(speed * (1 + level_bonus + evo_bonus))
        
        # Determine max level based on evolution stage
        max_level = evo_stage * 20  # Each evolution allows 20 more levels
        
        return {
            "id": card_id,
            "base_card_id": base_card_id,
            "name": name,
            "level": level,
            "rarity": rarity,
            "attack": attack,
            "defense": defense,
            "speed": speed,
            "element": element,
            "skill": skill,
            "skill_description": skill_desc,
            "image_url": image_url,
            "mp_cost": mp_cost,
            "evo_stage": evo_stage,
            "max_evo": max_evo,
            "max_level": max_level,
            "anime_series": anime_series,
            "xp": xp,
            "equipped": equipped == 1
        }
    
    def get_player_materials(self, user_id):
        """Get all materials owned by a player."""
        self.cursor.execute("""
            SELECT m.id, m.name, m.description, m.rarity, um.quantity
            FROM user_materials um
            JOIN materials m ON um.material_id = m.id
            WHERE um.player_id = (SELECT id FROM api_players WHERE discord_id = ?)
        """, (user_id,))
        
        materials = self.cursor.fetchall()
        
        # Format materials
        material_list = []
        for material_id, name, description, rarity, quantity in materials:
            material_list.append({
                "id": material_id,
                "name": name,
                "description": description,
                "rarity": rarity,
                "quantity": quantity
            })
        
        return material_list
    
    def get_evolution_requirements(self, card_id, current_evo_stage):
        """Get evolution requirements for a card."""
        # First check if there are specific requirements in the database
        self.cursor.execute("""
            SELECT er.id, er.gold_cost, er.result_card_id
            FROM evolution_requirements er
            WHERE er.base_card_id = ? AND er.evo_stage = ?
        """, (card_id, current_evo_stage + 1))
        
        specific_req = self.cursor.fetchone()
        
        # If specific requirements exist, get the materials
        if specific_req:
            evolution_id, gold_cost, result_card_id = specific_req
            
            # Get required materials
            self.cursor.execute("""
                SELECT m.id, m.name, m.rarity, em.quantity
                FROM evolution_materials em
                JOIN materials m ON em.material_id = m.id
                WHERE em.evolution_id = ?
            """, (evolution_id,))
            
            materials = self.cursor.fetchall()
            
            # Format materials
            material_list = []
            for material_id, name, rarity, quantity in materials:
                material_list.append({
                    "id": material_id,
                    "name": name,
                    "rarity": rarity,
                    "quantity": quantity
                })
            
            return {
                "evolution_id": evolution_id,
                "gold_cost": gold_cost,
                "materials": material_list,
                "result_card_id": result_card_id
            }
        
        # Generate generic requirements based on card rarity and evolution stage
        else:
            # Get card details
            self.cursor.execute("""
                SELECT name, rarity, element, anime_series
                FROM api_cards
                WHERE id = ?
            """, (card_id,))
            
            card_data = self.cursor.fetchone()
            if not card_data:
                return None
            
            name, rarity, element, anime_series = card_data
            
            # Base gold cost by rarity
            rarity_gold = {
                "Common": 1000,
                "Uncommon": 2000,
                "Rare": 5000,
                "Epic": 10000,
                "Legendary": 20000
            }
            
            # Gold scales with evolution stage
            base_gold = rarity_gold.get(rarity, 1000)
            gold_cost = base_gold * (current_evo_stage + 1)
            
            # Materials based on card properties
            material_list = []
            
            # Evolution core (always required)
            material_list.append({
                "id": 15,  # Evolution Core
                "name": "Evolution Core",
                "rarity": "Rare",
                "quantity": current_evo_stage + 1
            })
            
            # Element essence
            element_material_map = {
                "Fire": 4, "Water": 5, "Earth": 6, "Air": 7,
                "Electric": 8, "Ice": 9, "Light": 10, "Dark": 11,
                "Cute": 12, "Sweet": 13, "Star": 14
            }
            
            if element in element_material_map:
                material_list.append({
                    "id": element_material_map[element],
                    "name": f"{element} Essence",
                    "rarity": "Uncommon" if element in ["Fire", "Water", "Earth", "Air", "Electric", "Ice"] else 
                             "Rare" if element in ["Light", "Dark", "Cute", "Sweet"] else "Epic",
                    "quantity": 2 * (current_evo_stage + 1)
                })
            
            # Rarity fragment
            if rarity in ["Rare", "Epic", "Legendary"]:
                rarity_material_map = {
                    "Rare": 18, "Epic": 17, "Legendary": 16
                }
                
                material_list.append({
                    "id": rarity_material_map[rarity],
                    "name": f"{rarity} Fragment",
                    "rarity": "Uncommon" if rarity == "Rare" else "Rare" if rarity == "Epic" else "Epic",
                    "quantity": current_evo_stage + 1
                })
            
            # For final evolutions, add Anime Soul
            if current_evo_stage >= 4:
                material_list.append({
                    "id": 19,
                    "name": "Anime Soul",
                    "rarity": "Epic",
                    "quantity": 1
                })
            
            return {
                "evolution_id": None,
                "gold_cost": gold_cost,
                "materials": material_list,
                "result_card_id": None
            }
    
    def can_evolve(self, user_id, card_id):
        """Check if a card can be evolved based on player's resources."""
        # Get card details
        card_data = self.get_user_card(user_id, card_id)
        if not card_data:
            return False, "Card not found"
        
        # Check if already at max evolution
        if card_data["evo_stage"] >= card_data["max_evo"]:
            return False, "Card is already at maximum evolution"
        
        # Check if at max level for current evolution
        if card_data["level"] < card_data["max_level"]:
            return False, f"Card must be at maximum level ({card_data['max_level']}) for current evolution"
        
        # Get evolution requirements
        requirements = self.get_evolution_requirements(card_data["base_card_id"], card_data["evo_stage"])
        if not requirements:
            return False, "Evolution requirements could not be determined"
        
        # Get player's gold
        self.cursor.execute("""
            SELECT gold FROM api_players WHERE discord_id = ?
        """, (user_id,))
        
        player_gold = self.cursor.fetchone()
        if not player_gold:
            return False, "Player data not found"
        
        player_gold = player_gold[0]
        
        # Check if player has enough gold
        if player_gold < requirements["gold_cost"]:
            return False, f"Not enough gold. You need {requirements['gold_cost']} gold"
        
        # Get player's materials
        player_materials = self.get_player_materials(user_id)
        
        # Convert to dictionary for easy lookup
        player_materials_dict = {material["id"]: material["quantity"] for material in player_materials}
        
        # Check if player has enough materials
        missing_materials = []
        
        for material in requirements["materials"]:
            material_id = material["id"]
            required_quantity = material["quantity"]
            
            player_quantity = player_materials_dict.get(material_id, 0)
            
            if player_quantity < required_quantity:
                missing_materials.append({
                    "name": material["name"],
                    "have": player_quantity,
                    "need": required_quantity
                })
        
        if missing_materials:
            missing_text = "\n".join([f"{m['name']}: {m['have']}/{m['need']}" for m in missing_materials])
            return False, f"Missing materials:\n{missing_text}"
        
        return True, "Card can be evolved"
    
    def evolve_card(self, user_id, card_id):
        """Evolve a card to the next stage."""
        # Check if card can be evolved
        can_evolve_result, message = self.can_evolve(user_id, card_id)
        if not can_evolve_result:
            return False, message
        
        # Get card details
        card_data = self.get_user_card(user_id, card_id)
        
        # Get evolution requirements
        requirements = self.get_evolution_requirements(card_data["base_card_id"], card_data["evo_stage"])
        
        # Deduct gold
        self.cursor.execute("""
            UPDATE api_players
            SET gold = gold - ?
            WHERE discord_id = ?
        """, (requirements["gold_cost"], user_id))
        
        # Deduct materials
        for material in requirements["materials"]:
            material_id = material["id"]
            quantity = material["quantity"]
            
            self.cursor.execute("""
                UPDATE user_materials
                SET quantity = quantity - ?
                WHERE player_id = (SELECT id FROM api_players WHERE discord_id = ?)
                AND material_id = ?
            """, (quantity, user_id, material_id))
        
        # Update card evolution stage
        new_evo_stage = card_data["evo_stage"] + 1
        
        # If there's a specific result card, change the base card
        if requirements["result_card_id"]:
            self.cursor.execute("""
                UPDATE api_user_cards
                SET card_id = ?, evo_stage = ?
                WHERE id = ?
            """, (requirements["result_card_id"], new_evo_stage, card_id))
        else:
            # Just update the evolution stage
            self.cursor.execute("""
                UPDATE api_user_cards
                SET evo_stage = ?
                WHERE id = ?
            """, (new_evo_stage, card_id))
        
        # Commit changes
        self.db.conn.commit()
        
        return True, f"Successfully evolved {card_data['name']} to evolution stage {new_evo_stage}!"
    
    @commands.command(name="evolution_cards", aliases=["evocard", "evocards"])
    async def evolution_list_command(self, ctx):
        """🔄 View cards that can be evolved"""
        user_id = ctx.author.id
        
        # Get player's cards
        self.cursor.execute("""
            SELECT uc.id
            FROM api_user_cards uc
            JOIN api_cards c ON uc.card_id = c.id
            WHERE uc.player_id = (SELECT id FROM api_players WHERE discord_id = ?)
            ORDER BY uc.level DESC, c.rarity DESC
        """, (user_id,))
        
        card_ids = self.cursor.fetchall()
        
        if not card_ids:
            await ctx.send(f"{ctx.author.mention}, you don't have any cards!")
            return
        
        # Check which cards can be evolved
        evolvable_cards = []
        
        for (card_id,) in card_ids:
            card_data = self.get_user_card(user_id, card_id)
            
            # Skip if at max evolution
            if card_data["evo_stage"] >= card_data["max_evo"]:
                continue
            
            # Check if at max level for current evolution
            if card_data["level"] < card_data["max_level"]:
                continue
            
            # Get evolution requirements
            requirements = self.get_evolution_requirements(card_data["base_card_id"], card_data["evo_stage"])
            if not requirements:
                continue
            
            # Check if requirements are met (simplified check)
            can_evolve_result, _ = self.can_evolve(user_id, card_id)
            
            evolvable_cards.append({
                "card_data": card_data,
                "requirements": requirements,
                "can_evolve": can_evolve_result
            })
        
        if not evolvable_cards:
            await ctx.send(f"{ctx.author.mention}, you don't have any cards that can be evolved!")
            return
        
        # Create embeds
        embeds = []
        
        # Group cards (3 per page)
        chunks = [evolvable_cards[i:i+3] for i in range(0, len(evolvable_cards), 3)]
        
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title="Evolution Available Cards",
                description="Cards that are eligible for evolution:",
                color=discord.Color.blue()
            )
            
            for card_info in chunk:
                card = card_info["card_data"]
                reqs = card_info["requirements"]
                can_evolve = card_info["can_evolve"]
                
                # Format status
                status = "✅ Ready to evolve!" if can_evolve else "❌ Missing requirements"
                
                # Format evolution info
                evo_text = f"**{card['name']}** (ID: {card['id']})\n"
                evo_text += f"Level: {card['level']}/{card['max_level']} | Evolution: {card['evo_stage']}/{card['max_evo']}\n"
                evo_text += f"Gold Cost: {reqs['gold_cost']}\n"
                evo_text += f"Status: {status}\n"
                evo_text += f"Use `!evolve {card['id']}` to evolve this card"
                
                embed.add_field(
                    name=f"{card['rarity']} {card['name']} (Evo {card['evo_stage']}→{card['evo_stage']+1})",
                    value=evo_text,
                    inline=False
                )
            
            embed.set_footer(text=f"Page {i+1}/{len(chunks)} · !evolve <card_id> to evolve a card")
            embeds.append(embed)
        
        # Use pagination if available
        pagination_cog = self.bot.get_cog("Pagination")
        if pagination_cog and embeds:
            await pagination_cog.paginate(ctx, embeds)
        elif embeds:
            await ctx.send(embed=embeds[0])
    
    @commands.command(name="evolve")
    async def evolve_command(self, ctx, card_id: int = None):
        """🔄 Evolve a card to increase its power"""
        if card_id is None:
            await ctx.send(f"{ctx.author.mention}, please specify a card ID to evolve. Use `!evolution_cards` to see evolvable cards.")
            return
        
        user_id = ctx.author.id
        
        # Get card details
        card_data = self.get_user_card(user_id, card_id)
        if not card_data:
            await ctx.send(f"{ctx.author.mention}, card with ID {card_id} not found in your collection!")
            return
        
        # Check if card can be evolved
        can_evolve_result, message = self.can_evolve(user_id, card_id)
        
        if not can_evolve_result:
            # Create an embed with evolution requirements
            embed = discord.Embed(
                title=f"Cannot Evolve: {card_data['name']}",
                description=message,
                color=discord.Color.red()
            )
            
            # Add card details
            embed.add_field(
                name="Card Details",
                value=f"Level: {card_data['level']}/{card_data['max_level']}\n"
                      f"Evolution: {card_data['evo_stage']}/{card_data['max_evo']}",
                inline=False
            )
            
            # Get evolution requirements
            requirements = self.get_evolution_requirements(card_data["base_card_id"], card_data["evo_stage"])
            if requirements:
                # Add gold cost
                embed.add_field(
                    name="Gold Cost",
                    value=f"{requirements['gold_cost']} gold",
                    inline=True
                )
                
                # Add material requirements
                material_text = ""
                for material in requirements["materials"]:
                    material_text += f"{material['name']} x{material['quantity']}\n"
                
                embed.add_field(
                    name="Required Materials",
                    value=material_text or "None",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            return
        
        # Evolution confirmation view
        class EvolutionConfirmView(ui.View):
            def __init__(self, cog, card_data, requirements):
                super().__init__(timeout=60)
                self.cog = cog
                self.card_data = card_data
                self.requirements = requirements
            
            @ui.button(label="Evolve", style=ButtonStyle.success, emoji="⬆️")
            async def confirm_button(self, interaction: Interaction, button: ui.Button):
                """Confirm evolution."""
                # Check if interaction is from the command author
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("This is not your evolution!", ephemeral=True)
                    return
                
                await interaction.response.defer()
                
                # Evolve the card
                success, message = self.cog.evolve_card(ctx.author.id, self.card_data["id"])
                
                if success:
                    # Get updated card data
                    updated_card = self.cog.get_user_card(ctx.author.id, self.card_data["id"])
                    
                    # Create success embed
                    embed = discord.Embed(
                        title="Evolution Successful!",
                        description=message,
                        color=discord.Color.green()
                    )
                    
                    # Calculate stat increases
                    attack_increase = updated_card["attack"] - self.card_data["attack"]
                    defense_increase = updated_card["defense"] - self.card_data["defense"]
                    speed_increase = updated_card["speed"] - self.card_data["speed"]
                    
                    # Add new stats
                    embed.add_field(
                        name="New Stats",
                        value=f"ATK: {updated_card['attack']} (+{attack_increase})\n"
                              f"DEF: {updated_card['defense']} (+{defense_increase})\n"
                              f"SPD: {updated_card['speed']} (+{speed_increase})",
                        inline=False
                    )
                    
                    # Add new max level
                    embed.add_field(
                        name="New Max Level",
                        value=f"{updated_card['max_level']} (was {self.card_data['max_level']})",
                        inline=False
                    )
                    
                    # Add image if available
                    if updated_card["image_url"]:
                        embed.set_thumbnail(url=updated_card["image_url"])
                    
                    # Disable all buttons
                    for child in self.children:
                        child.disabled = True
                    
                    await interaction.message.edit(embed=embed, view=self)
                else:
                    # Something went wrong
                    error_embed = discord.Embed(
                        title="Evolution Failed",
                        description=message,
                        color=discord.Color.red()
                    )
                    
                    await interaction.message.edit(embed=error_embed, view=None)
            
            @ui.button(label="Cancel", style=ButtonStyle.secondary, emoji="❌")
            async def cancel_button(self, interaction: Interaction, button: ui.Button):
                """Cancel evolution."""
                # Check if interaction is from the command author
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("This is not your evolution!", ephemeral=True)
                    return
                
                await interaction.response.defer()
                
                embed = discord.Embed(
                    title="Evolution Cancelled",
                    description="Card evolution was cancelled.",
                    color=discord.Color.light_grey()
                )
                
                await interaction.message.edit(embed=embed, view=None)
        
        # Get evolution requirements
        requirements = self.get_evolution_requirements(card_data["base_card_id"], card_data["evo_stage"])
        
        # Create confirmation embed
        embed = discord.Embed(
            title=f"Evolve: {card_data['name']}",
            description=f"Are you sure you want to evolve this card from evolution stage {card_data['evo_stage']} to {card_data['evo_stage']+1}?",
            color=discord.Color.blue()
        )
        
        # Add card details
        embed.add_field(
            name="Card Details",
            value=f"Level: {card_data['level']}/{card_data['max_level']}\n"
                  f"Evolution: {card_data['evo_stage']}/{card_data['max_evo']}\n"
                  f"Rarity: {card_data['rarity']}",
            inline=False
        )
        
        # Add current stats
        embed.add_field(
            name="Current Stats",
            value=f"ATK: {card_data['attack']}\n"
                  f"DEF: {card_data['defense']}\n"
                  f"SPD: {card_data['speed']}",
            inline=True
        )
        
        # Add costs
        embed.add_field(
            name="Evolution Cost",
            value=f"Gold: {requirements['gold_cost']}",
            inline=True
        )
        
        # Add material requirements
        material_text = ""
        for material in requirements["materials"]:
            material_text += f"{material['name']} x{material['quantity']}\n"
        
        embed.add_field(
            name="Required Materials",
            value=material_text or "None",
            inline=False
        )
        
        # Add image if available
        if card_data["image_url"]:
            embed.set_thumbnail(url=card_data["image_url"])
        
        # Send confirmation message with buttons
        view = EvolutionConfirmView(self, card_data, requirements)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name="evolution_requirements", aliases=["evoreq"])
    async def evolution_requirements_command(self, ctx, card_id: int = None):
        """🔍 View requirements to evolve a specific card"""
        if card_id is None:
            await ctx.send(f"{ctx.author.mention}, please specify a card ID. Use `!cards` to see your cards.")
            return
        
        user_id = ctx.author.id
        
        # Get card details
        card_data = self.get_user_card(user_id, card_id)
        if not card_data:
            await ctx.send(f"{ctx.author.mention}, card with ID {card_id} not found in your collection!")
            return
        
        # Check if already at max evolution
        if card_data["evo_stage"] >= card_data["max_evo"]:
            await ctx.send(f"{ctx.author.mention}, {card_data['name']} is already at maximum evolution!")
            return
        
        # Get evolution requirements
        requirements = self.get_evolution_requirements(card_data["base_card_id"], card_data["evo_stage"])
        if not requirements:
            await ctx.send(f"{ctx.author.mention}, could not determine evolution requirements for this card.")
            return
        
        # Create embed
        embed = discord.Embed(
            title=f"Evolution Requirements: {card_data['name']}",
            description=f"Requirements to evolve from stage {card_data['evo_stage']} to {card_data['evo_stage']+1}:",
            color=discord.Color.blue()
        )
        
        # Add card details
        embed.add_field(
            name="Card Details",
            value=f"Level: {card_data['level']}/{card_data['max_level']}\n"
                  f"Evolution: {card_data['evo_stage']}/{card_data['max_evo']}\n"
                  f"Rarity: {card_data['rarity']}",
            inline=False
        )
        
        # Check if level requirement is met
        level_status = "✅" if card_data["level"] >= card_data["max_level"] else "❌"
        
        embed.add_field(
            name="Level Requirement",
            value=f"{level_status} Level {card_data['max_level']} (Current: {card_data['level']})",
            inline=False
        )
        
        # Add gold cost
        # Get player's gold
        self.cursor.execute("SELECT gold FROM api_players WHERE discord_id = ?", (user_id,))
        player_gold = self.cursor.fetchone()
        player_gold = player_gold[0] if player_gold else 0
        
        gold_status = "✅" if player_gold >= requirements["gold_cost"] else "❌"
        
        embed.add_field(
            name="Gold Cost",
            value=f"{gold_status} {requirements['gold_cost']} gold (You have: {player_gold})",
            inline=True
        )
        
        # Add material requirements
        material_text = ""
        player_materials = self.get_player_materials(user_id)
        player_materials_dict = {material["id"]: material["quantity"] for material in player_materials}
        
        for material in requirements["materials"]:
            material_id = material["id"]
            required_quantity = material["quantity"]
            player_quantity = player_materials_dict.get(material_id, 0)
            
            status = "✅" if player_quantity >= required_quantity else "❌"
            material_text += f"{status} {material['name']} x{required_quantity} (You have: {player_quantity})\n"
        
        embed.add_field(
            name="Required Materials",
            value=material_text or "None",
            inline=False
        )
        
        # Add image if available
        if card_data["image_url"]:
            embed.set_thumbnail(url=card_data["image_url"])
        
        await ctx.send(embed=embed)
    
    @commands.command(name="level_up", aliases=["lvlup"])
    async def level_up_command(self, ctx, card_id: int = None):
        """🆙 Level up a card using gold"""
        if card_id is None:
            await ctx.send(f"{ctx.author.mention}, please specify a card ID to level up. Use `!cards` to see your cards.")
            return
        
        user_id = ctx.author.id
        
        # Get card details
        card_data = self.get_user_card(user_id, card_id)
        if not card_data:
            await ctx.send(f"{ctx.author.mention}, card with ID {card_id} not found in your collection!")
            return
        
        # Check if already at max level for current evolution
        if card_data["level"] >= card_data["max_level"]:
            await ctx.send(
                f"{ctx.author.mention}, {card_data['name']} is already at maximum level for its current evolution stage! "
                f"Use `!evolve {card_id}` to evolve it to the next stage."
            )
            return
        
        # Calculate level up cost
        rarity_multiplier = {"Common": 1.0, "Uncommon": 1.5, "Rare": 2.0, "Epic": 3.0, "Legendary": 5.0}
        base_cost = 100
        level_cost = int(base_cost * rarity_multiplier.get(card_data["rarity"], 1.0) * card_data["level"])
        
        # Get player's gold
        self.cursor.execute("SELECT gold FROM api_players WHERE discord_id = ?", (user_id,))
        player_gold = self.cursor.fetchone()
        
        if not player_gold:
            await ctx.send(f"{ctx.author.mention}, you don't have a profile! Use `!start` to create one.")
            return
        
        player_gold = player_gold[0]
        
        # Check if player has enough gold
        if player_gold < level_cost:
            await ctx.send(
                f"{ctx.author.mention}, you don't have enough gold to level up this card! "
                f"You need {level_cost} gold but only have {player_gold}."
            )
            return
        
        # Level up confirmation view
        class LevelUpConfirmView(ui.View):
            def __init__(self, cog, card_data, level_cost):
                super().__init__(timeout=60)
                self.cog = cog
                self.card_data = card_data
                self.level_cost = level_cost
            
            @ui.button(label="Level Up", style=ButtonStyle.success, emoji="⬆️")
            async def confirm_button(self, interaction: Interaction, button: ui.Button):
                """Confirm level up."""
                # Check if interaction is from the command author
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("This is not your card!", ephemeral=True)
                    return
                
                await interaction.response.defer()
                
                # Level up the card
                # Deduct gold
                self.cog.cursor.execute("""
                    UPDATE api_players
                    SET gold = gold - ?
                    WHERE discord_id = ?
                """, (self.level_cost, ctx.author.id))
                
                # Increase level
                new_level = self.card_data["level"] + 1
                self.cog.cursor.execute("""
                    UPDATE api_user_cards
                    SET level = ?
                    WHERE id = ?
                """, (new_level, self.card_data["id"]))
                
                # Commit changes
                self.cog.db.conn.commit()
                
                # Get updated card data
                updated_card = self.cog.get_user_card(ctx.author.id, self.card_data["id"])
                
                # Calculate stat increases
                attack_increase = updated_card["attack"] - self.card_data["attack"]
                defense_increase = updated_card["defense"] - self.card_data["defense"]
                speed_increase = updated_card["speed"] - self.card_data["speed"]
                
                # Create success embed
                embed = discord.Embed(
                    title="Level Up Successful!",
                    description=f"{self.card_data['name']} is now level {new_level}!",
                    color=discord.Color.green()
                )
                
                # Add new stats
                embed.add_field(
                    name="New Stats",
                    value=f"ATK: {updated_card['attack']} (+{attack_increase})\n"
                          f"DEF: {updated_card['defense']} (+{defense_increase})\n"
                          f"SPD: {updated_card['speed']} (+{speed_increase})",
                    inline=False
                )
                
                # Add progress towards max level
                progress = f"{new_level}/{updated_card['max_level']}"
                if new_level >= updated_card['max_level']:
                    progress += " (Max for current evolution)"
                    
                embed.add_field(
                    name="Level Progress",
                    value=progress,
                    inline=True
                )
                
                # Add gold spent
                embed.add_field(
                    name="Gold Spent",
                    value=f"{self.level_cost} gold",
                    inline=True
                )
                
                # Add image if available
                if updated_card["image_url"]:
                    embed.set_thumbnail(url=updated_card["image_url"])
                
                # Check if max level reached
                if new_level >= updated_card['max_level']:
                    embed.add_field(
                        name="Evolution Available",
                        value=f"This card has reached its maximum level for evolution stage {updated_card['evo_stage']}!\n"
                              f"Use `!evolve {updated_card['id']}` to evolve it to the next stage.",
                        inline=False
                    )
                else:
                    # Calculate cost for next level
                    next_level_cost = int(100 * rarity_multiplier.get(updated_card["rarity"], 1.0) * new_level)
                    embed.add_field(
                        name="Next Level",
                        value=f"Cost for level {new_level + 1}: {next_level_cost} gold",
                        inline=False
                    )
                
                # Disable all buttons
                for child in self.children:
                    child.disabled = True
                
                await interaction.message.edit(embed=embed, view=self)
            
            @ui.button(label="Cancel", style=ButtonStyle.secondary, emoji="❌")
            async def cancel_button(self, interaction: Interaction, button: ui.Button):
                """Cancel level up."""
                # Check if interaction is from the command author
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("This is not your card!", ephemeral=True)
                    return
                
                await interaction.response.defer()
                
                embed = discord.Embed(
                    title="Level Up Cancelled",
                    description="Card level up was cancelled.",
                    color=discord.Color.light_grey()
                )
                
                await interaction.message.edit(embed=embed, view=None)
        
        # Create confirmation embed
        embed = discord.Embed(
            title=f"Level Up: {card_data['name']}",
            description=f"Are you sure you want to level up this card from level {card_data['level']} to {card_data['level']+1}?",
            color=discord.Color.blue()
        )
        
        # Add card details
        embed.add_field(
            name="Card Details",
            value=f"Level: {card_data['level']}/{card_data['max_level']}\n"
                  f"Evolution: {card_data['evo_stage']}/{card_data['max_evo']}\n"
                  f"Rarity: {card_data['rarity']}",
            inline=False
        )
        
        # Add current stats
        embed.add_field(
            name="Current Stats",
            value=f"ATK: {card_data['attack']}\n"
                  f"DEF: {card_data['defense']}\n"
                  f"SPD: {card_data['speed']}",
            inline=True
        )
        
        # Add cost
        embed.add_field(
            name="Level Up Cost",
            value=f"Gold: {level_cost} (You have: {player_gold})",
            inline=True
        )
        
        # Add image if available
        if card_data["image_url"]:
            embed.set_thumbnail(url=card_data["image_url"])
        
        # Send confirmation message with buttons
        view = LevelUpConfirmView(self, card_data, level_cost)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name="materials")
    async def materials_command(self, ctx):
        """🧪 View your evolution materials"""
        user_id = ctx.author.id
        
        # Get player's materials
        materials = self.get_player_materials(user_id)
        
        if not materials:
            await ctx.send(f"{ctx.author.mention}, you don't have any evolution materials!")
            return
        
        # Create embeds for pagination
        embeds = []
        
        # Group materials by rarity
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        materials_by_rarity = {}
        
        for material in materials:
            rarity = material["rarity"]
            if rarity not in materials_by_rarity:
                materials_by_rarity[rarity] = []
                
            materials_by_rarity[rarity].append(material)
        
        # Create an embed for each rarity
        for rarity in rarity_order:
            if rarity not in materials_by_rarity:
                continue
                
            embed = discord.Embed(
                title=f"{rarity} Evolution Materials",
                description=f"Your {rarity.lower()} materials for card evolution:",
                color=discord.Color.blue()
            )
            
            for material in materials_by_rarity[rarity]:
                embed.add_field(
                    name=f"{material['name']} x{material['quantity']}",
                    value=material["description"],
                    inline=False
                )
            
            embeds.append(embed)
        
        # If no materials by rarity, create a single embed
        if not embeds:
            embed = discord.Embed(
                title="Evolution Materials",
                description="Your materials for card evolution:",
                color=discord.Color.blue()
            )
            
            for material in materials:
                embed.add_field(
                    name=f"{material['name']} ({material['rarity']}) x{material['quantity']}",
                    value=material["description"],
                    inline=False
                )
            
            embeds.append(embed)
        
        # Use pagination if available
        pagination_cog = self.bot.get_cog("Pagination")
        if pagination_cog and embeds:
            await pagination_cog.paginate(ctx, embeds)
        elif embeds:
            await ctx.send(embed=embeds[0])

async def setup(bot):
    await bot.add_cog(EvolutionSystem(bot))