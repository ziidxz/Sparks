import discord
from discord.ext import commands
import random
from cogs.colorembed import ColorEmbed

class Evolution(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
    
    def get_user_card(self, user_id, card_id):
        """Gets detailed card information for a specific card."""
        self.cursor.execute("""
            SELECT c.id, c.base_card_id, c.name, c.rarity, c.level, c.evolution_stage, c.equipped,
                   c.attack, c.defense, c.speed, c.element, c.skill, c.skill_description,
                   c.image_url
            FROM usercards c
            WHERE c.user_id = ? AND c.id = ?
        """, (user_id, card_id))
        
        return self.cursor.fetchone()
    
    def get_evolution_requirements(self, base_card_id, evolution_stage):
        """Gets all materials and gold required for evolution."""
        self.cursor.execute("""
            SELECT er.material_id, m.name, er.quantity, er.gold_cost
            FROM evolution_requirements er
            JOIN materials m ON er.material_id = m.id
            WHERE er.base_card_id = ? AND er.evolution_stage = ?
        """, (base_card_id, evolution_stage))
        
        return self.cursor.fetchall()
    
    def get_evolution_result(self, base_card_id, evolution_stage):
        """Gets the evolution result information."""
        self.cursor.execute("""
            SELECT new_name, attack_boost, defense_boost, speed_boost, 
                   new_skill, new_skill_description, new_image_url
            FROM evolution_results
            WHERE base_card_id = ? AND evolution_stage = ?
        """, (base_card_id, evolution_stage))
        
        return self.cursor.fetchone()
    
    def get_user_materials(self, user_id, material_id):
        """Gets the quantity of a specific material a user has."""
        self.cursor.execute("""
            SELECT quantity
            FROM user_materials
            WHERE user_id = ? AND material_id = ?
        """, (user_id, material_id))
        
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def can_evolve(self, user_id, card_id):
        """Checks if a card can be evolved based on available materials and gold."""
        # Get card information
        card = self.get_user_card(user_id, card_id)
        
        if not card:
            return False, "Card not found", None, None
        
        # Unpack card data
        card_id, base_card_id, name, rarity, level, evo_stage, equipped, attack, defense, speed, element, skill, skill_desc, image_url = card
        
        # Check if card is equipped
        if equipped:
            return False, "Card is equipped", None, None
        
        # Check evolution requirements
        requirements = self.get_evolution_requirements(base_card_id, evo_stage)
        
        if not requirements:
            return False, "No evolution path available for this card", None, None
        
        # Get evolution result
        evo_result = self.get_evolution_result(base_card_id, evo_stage)
        
        if not evo_result:
            return False, "No evolution result defined for this card", None, None
        
        # Check if user has required materials
        missing_materials = []
        total_gold_cost = 0
        
        for material_id, material_name, required_qty, gold_cost in requirements:
            user_qty = self.get_user_materials(user_id, material_id)
            
            if user_qty < required_qty:
                missing_materials.append((material_name, required_qty, user_qty))
            
            total_gold_cost = gold_cost  # All requirements for a card have the same gold cost
        
        # Check if user has enough gold
        self.cursor.execute("SELECT gold FROM players WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        user_gold = result[0] if result else 0
        
        if user_gold < total_gold_cost:
            gold_needed = total_gold_cost - user_gold
            missing_materials.append(("Gold", total_gold_cost, user_gold))
        
        if missing_materials:
            return False, "Missing required materials", missing_materials, total_gold_cost
        
        return True, "Can evolve", requirements, total_gold_cost
    
    @commands.command(name="evolist")
    async def evolution_list(self, ctx):
        """View all cards that can be evolved in your collection"""
        user_id = ctx.author.id
        
        # Get all user's cards that might be evolvable
        self.cursor.execute("""
            SELECT c.id, c.name, c.rarity, c.level, c.evolution_stage
            FROM usercards c
            JOIN cards b ON c.base_card_id = b.id
            WHERE c.user_id = ? AND b.evolvable = 1
            ORDER BY c.rarity DESC, c.level DESC
        """, (user_id,))
        
        potential_cards = self.cursor.fetchall()
        
        if not potential_cards:
            await ctx.send(f"{ctx.author.mention}, you don't have any cards that can evolve!")
            return
        
        # Check which cards actually have evolution paths available
        evolvable_cards = []
        
        for card_id, name, rarity, level, evo_stage in potential_cards:
            # Get the base card ID for this card
            self.cursor.execute("SELECT base_card_id FROM usercards WHERE id = ?", (card_id,))
            base_id = self.cursor.fetchone()[0]
            
            # Check if evolution requirements exist
            self.cursor.execute("""
                SELECT COUNT(*)
                FROM evolution_requirements
                WHERE base_card_id = ? AND evolution_stage = ?
            """, (base_id, evo_stage))
            
            if self.cursor.fetchone()[0] > 0:
                evolvable_cards.append((card_id, name, rarity, level, evo_stage))
        
        if not evolvable_cards:
            await ctx.send(f"{ctx.author.mention}, none of your cards can currently evolve!")
            return
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Evolvable Cards",
            description="Use `!evorequire [card_id]` to see evolution requirements",
            color=discord.Color.purple()
        )
        
        # Add cards to embed
        for card_id, name, rarity, level, evo_stage in evolvable_cards:
            next_stage = evo_stage + 1
            
            embed.add_field(
                name=f"ID: {card_id} - {name}",
                value=f"Lvl {level} {rarity}\nCurrent Stage: {evo_stage} → Next: {next_stage}",
                inline=True
            )
        
        embed.set_footer(text="Use !evolve [card_id] to evolve a card")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="evorequire", aliases=["evoreq"])
    async def evolution_requirements(self, ctx, card_id: int):
        """View the requirements to evolve a specific card"""
        user_id = ctx.author.id
        
        # Get card details
        card = self.get_user_card(user_id, card_id)
        
        if not card:
            await ctx.send(f"{ctx.author.mention}, you don't own a card with ID `{card_id}`!")
            return
        
        # Unpack card data
        _, base_card_id, name, rarity, level, evo_stage, _, attack, defense, speed, element, skill, _, image_url = card
        
        # Get evolution requirements
        requirements = self.get_evolution_requirements(base_card_id, evo_stage)
        
        if not requirements:
            await ctx.send(f"{ctx.author.mention}, this card cannot be evolved further!")
            return
        
        # Get evolution result
        evo_result = self.get_evolution_result(base_card_id, evo_stage)
        
        if not evo_result:
            await ctx.send(f"{ctx.author.mention}, evolution result is not defined for this card!")
            return
        
        # Unpack evolution result
        new_name, attack_boost, defense_boost, speed_boost, new_skill, new_skill_desc, new_image = evo_result
        
        # Create embed
        embed = discord.Embed(
            title=f"Evolution Requirements: {name}",
            description=f"Current Stage: {evo_stage} → Next: {evo_stage + 1}",
            color=ColorEmbed.get_color(rarity)
        )
        
        if image_url:
            embed.set_thumbnail(url=image_url)
        
        # Evolution result preview
        embed.add_field(
            name="Evolution Result",
            value=f"**{new_name}**\n"
                  f"ATK: {attack} → {attack + attack_boost} (+{attack_boost})\n"
                  f"DEF: {defense} → {defense + defense_boost} (+{defense_boost})\n"
                  f"SPD: {speed} → {speed + speed_boost} (+{speed_boost})",
            inline=False
        )
        
        if new_skill and new_skill != skill:
            embed.add_field(
                name=f"New Skill: {new_skill}",
                value=new_skill_desc,
                inline=False
            )
        
        # Required Materials
        materials_text = ""
        gold_cost = 0
        
        for material_id, material_name, required_qty, material_gold_cost in requirements:
            user_qty = self.get_user_materials(user_id, material_id)
            
            # Visual indicator if user has enough
            has_enough = user_qty >= required_qty
            indicator = "✅" if has_enough else "❌"
            
            materials_text += f"{indicator} {material_name}: {user_qty}/{required_qty}\n"
            gold_cost = material_gold_cost  # All requirements have same gold cost
        
        embed.add_field(
            name="Required Materials",
            value=materials_text,
            inline=True
        )
        
        # Gold Cost
        self.cursor.execute("SELECT gold FROM players WHERE user_id = ?", (user_id,))
        user_gold = self.cursor.fetchone()[0]
        
        has_enough_gold = user_gold >= gold_cost
        gold_indicator = "✅" if has_enough_gold else "❌"
        
        embed.add_field(
            name="Gold Cost",
            value=f"{gold_indicator} {user_gold}/{gold_cost} Gold",
            inline=True
        )
        
        # Can evolve?
        can_evolve_now = all([user_qty >= required_qty for _, _, required_qty, _ in requirements]) and user_gold >= gold_cost
        
        if can_evolve_now:
            embed.add_field(
                name="Status",
                value="✨ **Ready to evolve!** ✨\nUse `!evolve {card_id}` to evolve this card.",
                inline=False
            )
        else:
            embed.add_field(
                name="Status",
                value="⚠️ **Missing requirements!** ⚠️\nGather the required materials before evolving.",
                inline=False
            )
        
        embed.set_footer(text=f"Card ID: {card_id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="evolve")
    async def evolve_card(self, ctx, card_id: int):
        """Evolve a card to its next stage"""
        user_id = ctx.author.id
        
        # Check if card can be evolved
        can_evolve, message, requirements, gold_cost = self.can_evolve(user_id, card_id)
        
        if not can_evolve:
            await ctx.send(f"{ctx.author.mention}, {message}!")
            
            if message == "Missing required materials" and requirements:
                missing_text = "\n".join([f"- {name}: {have}/{need} {'Gold' if name == 'Gold' else ''}" for name, need, have in requirements])
                await ctx.send(f"Missing materials:\n{missing_text}")
            
            return
        
        # Get card info before evolution
        card = self.get_user_card(user_id, card_id)
        _, base_card_id, old_name, rarity, level, evo_stage, _, old_attack, old_defense, old_speed, element, old_skill, old_skill_desc, old_image = card
        
        # Get evolution result
        evo_result = self.get_evolution_result(base_card_id, evo_stage)
        new_name, attack_boost, defense_boost, speed_boost, new_skill, new_skill_desc, new_image = evo_result
        
        # Consume materials
        for material_id, _, quantity, _ in requirements:
            self.cursor.execute("""
                UPDATE user_materials
                SET quantity = quantity - ?
                WHERE user_id = ? AND material_id = ?
            """, (quantity, user_id, material_id))
        
        # Deduct gold
        self.cursor.execute("UPDATE players SET gold = gold - ? WHERE user_id = ?", (gold_cost, user_id))
        
        # Update card stats and stage
        self.cursor.execute("""
            UPDATE usercards
            SET name = ?,
                attack = attack + ?,
                defense = defense + ?,
                speed = speed + ?,
                skill = CASE WHEN ? IS NOT NULL AND ? != '' THEN ? ELSE skill END,
                skill_description = CASE WHEN ? IS NOT NULL AND ? != '' THEN ? ELSE skill_description END,
                image_url = CASE WHEN ? IS NOT NULL AND ? != '' THEN ? ELSE image_url END,
                evolution_stage = evolution_stage + 1
            WHERE id = ? AND user_id = ?
        """, (
            new_name, attack_boost, defense_boost, speed_boost,
            new_skill, new_skill, new_skill,
            new_skill_desc, new_skill_desc, new_skill_desc,
            new_image, new_image, new_image,
            card_id, user_id
        ))
        
        self.db.conn.commit()
        
        # Get updated card info
        updated_card = self.get_user_card(user_id, card_id)
        _, _, name, rarity, level, new_evo_stage, _, attack, defense, speed, element, skill, skill_desc, image_url = updated_card
        
        # Create success embed
        embed = discord.Embed(
            title="✨ Evolution Successful! ✨",
            description=f"{old_name} evolved into **{name}**!",
            color=ColorEmbed.get_color(rarity)
        )
        
        # Before and after stats
        embed.add_field(
            name="Stats Improved",
            value=f"ATK: {old_attack} → {attack} (+{attack_boost})\n"
                  f"DEF: {old_defense} → {defense} (+{defense_boost})\n"
                  f"SPD: {old_speed} → {speed} (+{speed_boost})",
            inline=False
        )
        
        # Skill change (if applicable)
        if new_skill and new_skill != old_skill:
            embed.add_field(
                name="New Skill Acquired",
                value=f"**{skill}**: {skill_desc}",
                inline=False
            )
        
        # Show materials used
        materials_text = "\n".join([f"- {material_name} x{quantity}" for _, material_name, quantity, _ in requirements])
        
        embed.add_field(
            name="Materials Used",
            value=f"{materials_text}\nGold: {gold_cost}",
            inline=False
        )
        
        # Show evolution stage
        embed.add_field(
            name="Evolution Stage",
            value=f"Stage {evo_stage} → Stage {new_evo_stage}",
            inline=False
        )
        
        # Set card image
        if image_url:
            embed.set_image(url=image_url)
        
        embed.set_footer(text=f"Card ID: {card_id} • Use !view {card_id} to see full details")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="materials", aliases=["mats"])
    async def materials_command(self, ctx):
        """View your evolution materials"""
        user_id = ctx.author.id
        
        # Get all materials the user has
        self.cursor.execute("""
            SELECT m.id, m.name, m.rarity, m.description, um.quantity
            FROM materials m
            JOIN user_materials um ON m.id = um.material_id
            WHERE um.user_id = ? AND um.quantity > 0
            ORDER BY m.rarity DESC, m.name ASC
        """, (user_id,))
        
        materials = self.cursor.fetchall()
        
        if not materials:
            await ctx.send(f"{ctx.author.mention}, you don't have any materials!")
            return
        
        # Group materials by rarity
        materials_by_rarity = {}
        for material_id, name, rarity, description, quantity in materials:
            if rarity not in materials_by_rarity:
                materials_by_rarity[rarity] = []
            
            materials_by_rarity[rarity].append((material_id, name, description, quantity))
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Evolution Materials",
            description="Materials used for card evolution",
            color=discord.Color.blue()
        )
        
        # Display materials by rarity group
        for rarity in ["Legendary", "Epic", "Rare", "Uncommon", "Common"]:
            if rarity in materials_by_rarity:
                material_list = materials_by_rarity[rarity]
                
                field_text = ""
                for material_id, name, description, quantity in material_list:
                    field_text += f"**{name}** (x{quantity})\n{description}\n\n"
                
                embed.add_field(
                    name=f"{rarity} Materials",
                    value=field_text,
                    inline=False
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Evolution(bot))
