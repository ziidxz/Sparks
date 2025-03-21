import discord
from discord.ext import commands
import random
import logging
from collections import defaultdict

logger = logging.getLogger('bot.skill')

class Skill(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        
        # Define skill types for reference
        self.skill_types = {
            "damage": "Deals damage to the opponent",
            "healing": "Restores HP to the user",
            "buff": "Increases user's stats temporarily",
            "debuff": "Decreases opponent's stats temporarily",
            "dot": "Deals damage over time (DoT)",
            "status": "Applies a status effect",
            "ultimate": "Powerful special attack"
        }
        
        # Map keywords to effects for skills
        self.skill_effects = {
            "fire": {"type": "dot", "effect": "burning", "duration": 3, "multiplier": 1.3},
            "flame": {"type": "dot", "effect": "burning", "duration": 3, "multiplier": 1.3},
            "burn": {"type": "dot", "effect": "burning", "duration": 3, "multiplier": 1.3},
            
            "heal": {"type": "healing", "multiplier": 0.25},
            "cure": {"type": "healing", "multiplier": 0.25},
            "recover": {"type": "healing", "multiplier": 0.25},
            
            "stun": {"type": "status", "effect": "stunned", "duration": 1, "multiplier": 1.2},
            "paralyze": {"type": "status", "effect": "stunned", "duration": 1, "multiplier": 1.2},
            
            "poison": {"type": "dot", "effect": "poisoned", "duration": 3, "multiplier": 1.2},
            "toxic": {"type": "dot", "effect": "poisoned", "duration": 3, "multiplier": 1.2},
            
            "ice": {"type": "status", "effect": "frozen", "duration": 2, "multiplier": 1.25},
            "freeze": {"type": "status", "effect": "frozen", "duration": 2, "multiplier": 1.25},
            
            "ultimate": {"type": "damage", "multiplier": 2.0},
            "final": {"type": "damage", "multiplier": 2.0},
            
            "buff": {"type": "buff", "stats": ["attack", "defense"], "multiplier": 1.3},
            "power": {"type": "buff", "stats": ["attack"], "multiplier": 1.5},
            "shield": {"type": "buff", "stats": ["defense"], "multiplier": 1.5},
            "speed": {"type": "buff", "stats": ["speed"], "multiplier": 1.5},
            
            "debuff": {"type": "debuff", "stats": ["attack", "defense"], "multiplier": 0.7},
            "weaken": {"type": "debuff", "stats": ["attack"], "multiplier": 0.5},
            "break": {"type": "debuff", "stats": ["defense"], "multiplier": 0.5},
            "slow": {"type": "debuff", "stats": ["speed"], "multiplier": 0.5}
        }
    
    def get_card_skill_info(self, card_id):
        """Get skill information for a specific card."""
        self.cursor.execute("""
            SELECT name, skill, skill_description, skill_mp_cost, skill_cooldown
            FROM usercards
            WHERE id = ?
        """, (card_id,))
        
        return self.cursor.fetchone()
    
    def generate_skill_description(self, skill_name):
        """Generate a description based on skill name keywords."""
        skill_name_lower = skill_name.lower()
        
        # Identify skill type and effects based on keywords
        primary_effect = None
        secondary_effects = []
        
        for keyword, effect in self.skill_effects.items():
            if keyword in skill_name_lower:
                if primary_effect is None:
                    primary_effect = (keyword, effect)
                else:
                    secondary_effects.append((keyword, effect))
        
        # If no effects found, default to damage
        if primary_effect is None:
            return "Deals significant damage to the opponent.", 20, 3
        
        # Generate description
        effect_desc = []
        mp_cost = 20  # Default
        cooldown = 3  # Default
        
        primary_keyword, primary_data = primary_effect
        
        if primary_data["type"] == "damage":
            effect_desc.append(f"Deals {primary_keyword} damage to the opponent")
            mp_cost = 20
        elif primary_data["type"] == "dot":
            effect_desc.append(f"Inflicts {primary_data['effect']} status for {primary_data['duration']} turns")
            mp_cost = 25
        elif primary_data["type"] == "healing":
            effect_desc.append(f"Restores {int(primary_data['multiplier']*100)}% of max HP")
            mp_cost = 30
        elif primary_data["type"] == "status":
            effect_desc.append(f"Applies {primary_data['effect']} status for {primary_data['duration']} turns")
            mp_cost = 25
        elif primary_data["type"] == "buff":
            stats = ", ".join(primary_data['stats'])
            effect_desc.append(f"Increases {stats} by {int((primary_data['multiplier']-1)*100)}%")
            mp_cost = 30
        elif primary_data["type"] == "debuff":
            stats = ", ".join(primary_data['stats'])
            effect_desc.append(f"Decreases opponent's {stats} by {int((1-primary_data['multiplier'])*100)}%")
            mp_cost = 30
        
        # Add secondary effects
        for keyword, effect in secondary_effects:
            if effect["type"] == "dot":
                effect_desc.append(f"Also inflicts {effect['effect']} status")
                mp_cost += 5
            elif effect["type"] == "status":
                effect_desc.append(f"Also applies {effect['effect']} status")
                mp_cost += 5
            elif effect["type"] == "buff" or effect["type"] == "debuff":
                effect_desc.append(f"Also affects {', '.join(effect['stats'])}")
                mp_cost += 5
        
        # If it's an ultimate skill, increase cost and cooldown
        if "ultimate" in skill_name_lower or "final" in skill_name_lower:
            mp_cost = 40
            cooldown = 5
            if len(effect_desc) == 1:  # If only the basic effect
                effect_desc[0] = "Unleashes a devastating attack on the opponent"
        
        return " and ".join(effect_desc) + ".", mp_cost, cooldown
    
    @commands.command(name="skill")
    async def skill_command(self, ctx, card_id: int = None):
        """View detailed information about a card's skill"""
        user_id = ctx.author.id
        
        # If no card ID provided, try to get equipped card
        if card_id is None:
            self.cursor.execute("""
                SELECT id FROM usercards
                WHERE user_id = ? AND equipped = 1
            """, (user_id,))
            
            result = self.cursor.fetchone()
            if result:
                card_id = result[0]
            else:
                await ctx.send(f"{ctx.author.mention}, you don't have a card equipped. Please specify a card ID or equip a card!")
                return
        
        # Get skill information
        skill_info = self.get_card_skill_info(card_id)
        
        if not skill_info:
            await ctx.send(f"{ctx.author.mention}, you don't own a card with ID `{card_id}`!")
            return
        
        card_name, skill_name, skill_desc, mp_cost, cooldown = skill_info
        
        # Get card element and other details
        self.cursor.execute("""
            SELECT rarity, element, level, image_url
            FROM usercards
            WHERE id = ? AND user_id = ?
        """, (card_id, user_id))
        
        card_details = self.cursor.fetchone()
        if not card_details:
            await ctx.send(f"{ctx.author.mention}, you don't own a card with ID `{card_id}`!")
            return
        
        rarity, element, level, image_url = card_details
        
        # Create embed
        from cogs.colorembed import ColorEmbed
        embed = discord.Embed(
            title=f"Skill: {skill_name}",
            description=f"Card: **{card_name}** (Lvl {level} {rarity})",
            color=ColorEmbed.get_color(rarity)
        )
        
        # Skill details
        embed.add_field(
            name="Description",
            value=skill_desc,
            inline=False
        )
        
        embed.add_field(name="MP Cost", value=str(mp_cost), inline=True)
        embed.add_field(name="Cooldown", value=f"{cooldown} turns", inline=True)
        embed.add_field(name="Element", value=element, inline=True)
        
        # Generate skill type based on name and description
        skill_type = "Unknown"
        for keyword, desc in self.skill_types.items():
            if keyword in skill_name.lower() or keyword in skill_desc.lower():
                skill_type = keyword.capitalize()
                break
        
        embed.add_field(name="Skill Type", value=skill_type, inline=True)
        
        # Determine effectiveness
        effective_against = []
        weak_against = []
        
        element_chart = {
            "Fire": {"strong": ["Earth", "Ice"], "weak": ["Water"]},
            "Water": {"strong": ["Fire"], "weak": ["Electric", "Ice"]},
            "Earth": {"strong": ["Electric"], "weak": ["Fire", "Air"]},
            "Air": {"strong": ["Earth"], "weak": ["Electric", "Ice"]},
            "Electric": {"strong": ["Water", "Air"], "weak": ["Earth"]},
            "Ice": {"strong": ["Water", "Air"], "weak": ["Fire"]},
            "Light": {"strong": ["Dark"], "weak": []},
            "Dark": {"strong": ["Light"], "weak": []},
            "Cute": {"strong": ["Dark"], "weak": ["Light"]},
            "Sweet": {"strong": ["Cute"], "weak": ["Dark"]},
            "Star": {"strong": [], "weak": []}
        }
        
        if element in element_chart:
            effective_against = element_chart[element]["strong"]
            weak_against = element_chart[element]["weak"]
        
        if effective_against:
            embed.add_field(
                name="Effective Against",
                value=", ".join(effective_against),
                inline=True
            )
        
        if weak_against:
            embed.add_field(
                name="Weak Against",
                value=", ".join(weak_against),
                inline=True
            )
        
        # Battle tips
        tips = []
        if "healing" in skill_type.lower() or "heal" in skill_name.lower():
            tips.append("Best used when HP is below 50%")
        
        if "fire" in skill_name.lower() or "burn" in skill_name.lower():
            tips.append("Burning deals damage over time, great for longer battles")
        
        if "stun" in skill_name.lower() or "paralyze" in skill_name.lower():
            tips.append("Stun prevents the enemy from attacking for 1 turn")
        
        if "poison" in skill_name.lower() or "toxic" in skill_name.lower():
            tips.append("Poison deals significant damage over time")
        
        if "ultimate" in skill_name.lower() or "final" in skill_name.lower():
            tips.append("Ultimate skills are best saved for crucial moments")
        
        if tips:
            embed.add_field(
                name="Battle Tips",
                value="• " + "\n• ".join(tips),
                inline=False
            )
        
        # Add card image
        if image_url:
            embed.set_thumbnail(url=image_url)
        
        embed.set_footer(text=f"Card ID: {card_id} • Skills are used automatically in battle")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="skillinfo")
    async def skill_info_command(self, ctx):
        """Learn about different skill types and effects"""
        embed = discord.Embed(
            title="Skill Types & Effects Guide",
            description="Understanding the different types of skills and their effects",
            color=discord.Color.blue()
        )
        
        # Skill types section
        types_text = ""
        for skill_type, description in self.skill_types.items():
            types_text += f"**{skill_type.capitalize()}**: {description}\n"
        
        embed.add_field(
            name="Skill Types",
            value=types_text,
            inline=False
        )
        
        # Status effects section
        status_text = (
            "**Burning**: Deals 5% max HP damage per turn\n"
            "**Poisoned**: Deals 8% max HP damage per turn\n"
            "**Stunned**: Cannot attack for 1 turn\n"
            "**Frozen**: Cannot attack for 2 turns\n"
            "**Weakened**: Attack reduced by 30%\n"
            "**Broken**: Defense reduced by 30%\n"
            "**Slowed**: Speed reduced by 30%"
        )
        
        embed.add_field(
            name="Status Effects",
            value=status_text,
            inline=False
        )
        
        # Element effectiveness
        element_text = (
            "**Fire**: Strong vs Earth, Ice • Weak vs Water\n"
            "**Water**: Strong vs Fire • Weak vs Electric, Ice\n"
            "**Earth**: Strong vs Electric • Weak vs Fire, Air\n"
            "**Air**: Strong vs Earth • Weak vs Electric, Ice\n"
            "**Electric**: Strong vs Water, Air • Weak vs Earth\n"
            "**Ice**: Strong vs Water, Air • Weak vs Fire\n"
            "**Light**: Strong vs Dark\n"
            "**Dark**: Strong vs Light\n"
            "**Cute**: Strong vs Dark • Weak vs Light\n"
            "**Sweet**: Strong vs Cute • Weak vs Dark\n"
            "**Star**: Neutral to all elements"
        )
        
        embed.add_field(
            name="Element Effectiveness",
            value=element_text,
            inline=False
        )
        
        # Battle tips
        battle_tips = (
            "• Element advantage gives a 50% damage boost\n"
            "• MP regenerates at 5% per turn\n"
            "• Status effects can stack (e.g., burning + poisoned)\n"
            "• Higher level skills cost more MP but deal more damage\n"
            "• Some skills have longer cooldowns but stronger effects"
        )
        
        embed.add_field(
            name="Battle Tips",
            value=battle_tips,
            inline=False
        )
        
        embed.set_footer(text="Use !skill [card_id] to view a specific card's skill")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="skills")
    async def skills_list_command(self, ctx):
        """View all skills your cards possess"""
        user_id = ctx.author.id
        
        # Get all user's cards with their skills
        self.cursor.execute("""
            SELECT id, name, rarity, level, skill, skill_description
            FROM usercards
            WHERE user_id = ?
            ORDER BY rarity DESC, level DESC
        """, (user_id,))
        
        cards = self.cursor.fetchall()
        
        if not cards:
            await ctx.send(f"{ctx.author.mention}, you don't have any cards yet!")
            return
        
        # Group skills by type
        skill_types = defaultdict(list)
        
        for card_id, name, rarity, level, skill, desc in cards:
            # Determine skill type
            skill_type = "Damage"  # Default
            
            if "heal" in skill.lower() or "cure" in skill.lower() or "recover" in skill.lower():
                skill_type = "Healing"
            elif "stun" in skill.lower() or "paralyze" in skill.lower():
                skill_type = "Status"
            elif "fire" in skill.lower() or "burn" in skill.lower() or "poison" in skill.lower():
                skill_type = "DoT"
            elif "buff" in skill.lower() or "power" in skill.lower() or "shield" in skill.lower():
                skill_type = "Buff"
            elif "debuff" in skill.lower() or "weaken" in skill.lower() or "break" in skill.lower():
                skill_type = "Debuff"
            elif "ultimate" in skill.lower() or "final" in skill.lower():
                skill_type = "Ultimate"
            
            skill_types[skill_type].append((card_id, name, rarity, level, skill, desc))
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Card Skills",
            description="Overview of all skills your cards possess",
            color=discord.Color.purple()
        )
        
        # Add each skill type as a field
        for skill_type, cards_list in skill_types.items():
            field_text = ""
            
            for card_id, name, rarity, level, skill, desc in cards_list[:3]:  # Limit to 3 per category
                field_text += f"**{skill}** - {name} (Lvl {level} {rarity})\n"
                field_text += f"*{desc[:50]}{'...' if len(desc) > 50 else ''}*\n\n"
            
            if len(cards_list) > 3:
                field_text += f"*And {len(cards_list) - 3} more {skill_type.lower()} skills...*"
            
            embed.add_field(
                name=f"{skill_type} Skills",
                value=field_text,
                inline=False
            )
        
        embed.set_footer(text="Use !skill [card_id] to view detailed skill information")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="updateskill")
    async def update_skill_command(self, ctx, card_id: int):
        """Update a card's skill description"""
        user_id = ctx.author.id
        
        # Check if user owns the card
        self.cursor.execute("""
            SELECT name, skill, skill_description
            FROM usercards
            WHERE id = ? AND user_id = ?
        """, (card_id, user_id))
        
        card = self.cursor.fetchone()
        
        if not card:
            await ctx.send(f"{ctx.author.mention}, you don't own a card with ID `{card_id}`!")
            return
        
        card_name, skill_name, old_desc = card
        
        # Generate new description
        new_desc, mp_cost, cooldown = self.generate_skill_description(skill_name)
        
        # Update card skill
        self.cursor.execute("""
            UPDATE usercards
            SET skill_description = ?, skill_mp_cost = ?, skill_cooldown = ?
            WHERE id = ? AND user_id = ?
        """, (new_desc, mp_cost, cooldown, card_id, user_id))
        
        self.db.conn.commit()
        
        # Create success embed
        embed = discord.Embed(
            title=f"Skill Updated: {skill_name}",
            description=f"Card: **{card_name}**",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Previous Description",
            value=old_desc,
            inline=False
        )
        
        embed.add_field(
            name="Updated Description",
            value=new_desc,
            inline=False
        )
        
        embed.add_field(name="MP Cost", value=str(mp_cost), inline=True)
        embed.add_field(name="Cooldown", value=f"{cooldown} turns", inline=True)
        
        embed.set_footer(text=f"Card ID: {card_id}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Skill(bot))
