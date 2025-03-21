import discord
from discord.ext import commands
import random
import asyncio
import time
import logging
from utils.rewards import get_gold_drop, get_exp_drop
from utils.probability import calculate_critical, calculate_dodge, calculate_drop_chance

logger = logging.getLogger('bot.boss')

class Boss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.active_boss_battles = {}  # {user_id: boss_id}
    
    def get_boss_list(self, player_level):
        """Get list of bosses available to fight based on player level."""
        self.cursor.execute("""
            SELECT id, name, level, hp, attack, defense, speed, element, min_player_level
            FROM bosses
            WHERE min_player_level <= ?
            ORDER BY level ASC
        """, (player_level,))
        
        return self.cursor.fetchall()
    
    def get_boss_details(self, boss_id):
        """Get detailed boss information."""
        self.cursor.execute("""
            SELECT id, name, level, hp, attack, defense, speed, element, 
                   skill, skill_description, lore, image_url,
                   min_player_level, reward_gold, reward_xp
            FROM bosses
            WHERE id = ?
        """, (boss_id,))
        
        return self.cursor.fetchone()
    
    def get_boss_drops(self, boss_id):
        """Get potential drops from a boss."""
        self.cursor.execute("""
            SELECT bd.material_id, m.name, m.rarity, bd.drop_rate, 
                   bd.min_quantity, bd.max_quantity
            FROM boss_drops bd
            JOIN materials m ON bd.material_id = m.id
            WHERE bd.boss_id = ?
        """, (boss_id,))
        
        return self.cursor.fetchall()
    
    def add_material_to_user(self, user_id, material_id, quantity):
        """Add a material to a user's inventory."""
        # Check if user already has this material
        self.cursor.execute("""
            SELECT id, quantity FROM user_materials
            WHERE user_id = ? AND material_id = ?
        """, (user_id, material_id))
        
        existing = self.cursor.fetchone()
        
        if existing:
            # Update quantity
            self.cursor.execute("""
                UPDATE user_materials
                SET quantity = quantity + ?
                WHERE id = ?
            """, (quantity, existing[0]))
        else:
            # Add new entry
            self.cursor.execute("""
                INSERT INTO user_materials (user_id, material_id, quantity)
                VALUES (?, ?, ?)
            """, (user_id, material_id, quantity))
    
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="boss")
    async def boss_command(self, ctx, boss_id: int = None):
        """Battle against a powerful boss for special rewards"""
        user_id = ctx.author.id
        
        # Check if user exists and get level
        self.cursor.execute("SELECT stamina, level FROM players WHERE user_id = ?", (user_id,))
        player_data = self.cursor.fetchone()
        
        if not player_data:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
        
        stamina, player_level = player_data
        
        # Check stamina requirement (5 for boss battles)
        if stamina < 5:
            await ctx.send(f"{ctx.author.mention}, you need at least **5 stamina** to challenge a boss!")
            return
        
        # If no boss_id provided, show available bosses
        if boss_id is None:
            available_bosses = self.get_boss_list(player_level)
            
            if not available_bosses:
                await ctx.send(f"{ctx.author.mention}, no bosses are available for you yet! Level up more.")
                return
            
            embed = discord.Embed(
                title="🐉 Available Bosses",
                description="Challenge these bosses to earn special rewards!",
                color=discord.Color.dark_red()
            )
            
            for b_id, name, level, hp, attack, defense, speed, element, min_level in available_bosses:
                embed.add_field(
                    name=f"{name} (Level {level})",
                    value=f"**ID:** `{b_id}`\n"
                          f"**HP:** {hp} · **ATK:** {attack} · **DEF:** {defense}\n"
                          f"**Element:** {element} · **Min. Level:** {min_level}\n"
                          f"Use `!boss {b_id}` to challenge",
                    inline=False
                )
            
            embed.set_footer(text="Each boss battle costs 5 stamina")
            
            await ctx.send(embed=embed)
            return
        
        # Get boss details
        boss = self.get_boss_details(boss_id)
        
        if not boss:
            await ctx.send(f"{ctx.author.mention}, that boss doesn't exist! Use `!boss` to see available bosses.")
            return
        
        # Unpack boss data
        b_id, name, level, hp, attack, defense, speed, element, skill, skill_desc, lore, image_url, min_level, reward_gold, reward_xp = boss
        
        # Check if player meets level requirement
        if player_level < min_level:
            await ctx.send(f"{ctx.author.mention}, you need to be at least level **{min_level}** to challenge this boss!")
            return
        
        # Get player's equipped card
        self.cursor.execute("""
            SELECT id, name, attack, defense, speed, level, 
                   element, skill, skill_description, skill_mp_cost, 
                   critical_rate, dodge_rate, rarity, image_url
            FROM usercards 
            WHERE user_id = ? AND equipped = 1
        """, (user_id,))
        
        player_card = self.cursor.fetchone()
        
        if not player_card:
            await ctx.send(f"{ctx.author.mention}, you need to equip a card first! Use `!equip [card_id]`.")
            return
        
        # Unpack player card data
        card_id, card_name, attack_stat, defense_stat, speed_stat, card_level, card_element, card_skill, card_skill_desc, skill_mp_cost, crit_rate, dodge_rate, rarity, card_image = player_card
        
        # Deduct stamina
        self.cursor.execute("UPDATE players SET stamina = stamina - 5 WHERE user_id = ?", (user_id,))
        self.db.conn.commit()
        
        # Save this battle in active battles
        self.active_boss_battles[user_id] = boss_id
        
        # Battle setup
        max_boss_hp = hp
        boss_hp = hp
        boss_mp = 100
        boss_max_mp = 100
        boss_skill_mp_cost = 30  # Default value
        boss_crit_rate = 10  # Default value
        boss_dodge_rate = 8  # Default value
        
        # Setup player stats
        player_hp = 500 + (card_level * 15)
        player_max_hp = player_hp
        
        # Get player MP from database
        self.cursor.execute("SELECT mp FROM players WHERE user_id = ?", (user_id,))
        player_mp = self.cursor.fetchone()[0]
        player_max_mp = 100 + (card_level * 5)  # Scale max MP with level
        
        # Element effectiveness
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
        
        # Calculate element effectiveness
        element_multiplier = 1.0
        if card_element in element_chart and element in element_chart[card_element]["strong"]:
            element_multiplier = 1.5
        elif card_element in element_chart and element in element_chart[card_element]["weak"]:
            element_multiplier = 0.75
        
        # Battle message
        battle_message = await ctx.send(f"⚔️ **Boss Battle: {ctx.author.display_name} vs {name}**")
        
        # Battle effects and animations
        battle_effects = ["Bonked", "Whacked", "Booped", "Thwacked", "Slammed", "Pummeled"]
        
        # Skill cooldowns
        player_skill_cooldown = 0
        boss_skill_cooldown = 0
        
        # Status effects (turns remaining)
        player_status = {}
        boss_status = {}
        
        # Determine who goes first based on speed
        player_first = speed_stat >= speed
        current_turn = "player" if player_first else "boss"
        
        # Battle loop
        turn = 0
        while player_hp > 0 and boss_hp > 0:
            turn += 1
            await asyncio.sleep(2)
            
            # Generate HP and MP bars
            def resource_bar(current, max_val, char_filled="█", char_empty="░"):
                percentage = current / max_val
                filled = int(percentage * 10)
                empty = 10 - filled
                return f"**`{char_filled * filled}{char_empty * empty}`** **`{current}/{max_val}`**"
            
            # Handle status effects
            for status, turns in list(player_status.items()):
                if status == "burning":
                    burn_damage = int(player_max_hp * 0.05)  # 5% damage
                    player_hp = max(0, player_hp - burn_damage)
                
                player_status[status] -= 1
                if player_status[status] <= 0:
                    del player_status[status]
            
            for status, turns in list(boss_status.items()):
                if status == "burning":
                    burn_damage = int(max_boss_hp * 0.05)  # 5% damage
                    boss_hp = max(0, boss_hp - burn_damage)
                
                boss_status[status] -= 1
                if boss_status[status] <= 0:
                    del boss_status[status]
            
            # Handle cooldowns
            if player_skill_cooldown > 0:
                player_skill_cooldown -= 1
            if boss_skill_cooldown > 0:
                boss_skill_cooldown -= 1
            
            # Battle logic
            if current_turn == "player":
                # Player's turn
                # Check if player has enough MP to use skill
                can_use_skill = player_mp >= skill_mp_cost and player_skill_cooldown == 0
                
                # Boss battles have higher skill chance
                skill_chance = 0.4
                if player_hp < player_max_hp * 0.4:  # Below 40% HP
                    skill_chance = 0.8
                
                use_skill = can_use_skill and random.random() < skill_chance
                
                if use_skill:
                    # Use skill
                    player_mp -= skill_mp_cost
                    player_skill_cooldown = 3  # Set cooldown
                    
                    # Apply skill effects based on card's skill
                    damage_multiplier = 1.5  # Default damage multiplier
                    healing = False
                    
                    # Apply different effects based on skill key words
                    if "fire" in card_skill.lower() or "flame" in card_skill.lower() or "burn" in card_skill.lower():
                        boss_status["burning"] = 3  # Burning for 3 turns
                        damage_multiplier = 1.3
                    elif "heal" in card_skill.lower() or "cure" in card_skill.lower() or "recover" in card_skill.lower():
                        heal_amount = int(player_max_hp * 0.25)  # Heal 25% of max HP
                        player_hp = min(player_max_hp, player_hp + heal_amount)
                        damage_multiplier = 0.5
                        healing = True
                    elif "stun" in card_skill.lower() or "paralyz" in card_skill.lower():
                        boss_status["stunned"] = 1  # Stunned for 1 turn
                        damage_multiplier = 1.2
                    elif "poison" in card_skill.lower() or "toxic" in card_skill.lower():
                        boss_status["poisoned"] = 3  # Poisoned for 3 turns
                        damage_multiplier = 1.2
                    elif "ultimate" in card_skill.lower() or "final" in card_skill.lower():
                        damage_multiplier = 2.0  # Ultimate skills do double damage
                    
                    # Calculate damage with skill boost and element multiplier
                    base_damage = max(5, attack_stat - (defense // 2))
                    damage = int(base_damage * damage_multiplier * element_multiplier)
                    
                    # Critical hit chance
                    is_critical = calculate_critical(crit_rate)
                    if is_critical:
                        damage = int(damage * 1.5)
                    
                    # Apply damage
                    if not healing:
                        boss_hp = max(0, boss_hp - damage)
                    
                    # Build action text
                    action_text = f"**{ctx.author.display_name}** used **{card_skill}**!"
                    
                    if healing:
                        damage_text = f"💖 Healed `+{heal_amount}` HP!"
                    else:
                        damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"Dealt `-{damage}`!"
                        
                        # Add status effect text
                        if "burning" in boss_status:
                            damage_text += " 🔥 Boss is burning!"
                        elif "stunned" in boss_status:
                            damage_text += " ⚡ Boss is stunned!"
                        elif "poisoned" in boss_status:
                            damage_text += " ☠️ Boss is poisoned!"
                    
                    # Element effectiveness text
                    if element_multiplier > 1:
                        damage_text += " (Element effective! x1.5)"
                    elif element_multiplier < 1:
                        damage_text += " (Element ineffective! x0.75)"
                
                else:
                    # Regular attack
                    base_damage = max(5, attack_stat - (defense // 2))
                    
                    # Apply element effectiveness
                    base_damage = int(base_damage * element_multiplier)
                    
                    # Check for dodge
                    is_dodged = calculate_dodge(boss_dodge_rate)
                    
                    if is_dodged:
                        damage = 0
                        action_text = f"**{ctx.author.display_name}** attacked!"
                        damage_text = "😎 Boss dodged the attack!"
                    else:
                        # Critical hit chance
                        is_critical = calculate_critical(crit_rate)
                        damage = int(base_damage * 1.5) if is_critical else base_damage
                        
                        # Apply damage
                        boss_hp = max(0, boss_hp - damage)
                        
                        action_text = f"**{ctx.author.display_name}** attacked!"
                        damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"{random.choice(battle_effects)} for `-{damage}`!"
                        
                        # Element effectiveness text
                        if element_multiplier > 1:
                            damage_text += " (Element effective! x1.5)"
                        elif element_multiplier < 1:
                            damage_text += " (Element ineffective! x0.75)"
                
                current_turn = "boss"
                
            else:
                # Boss's turn
                if "stunned" in boss_status:
                    action_text = f"**{name}** is stunned!"
                    damage_text = "Cannot attack this turn!"
                    current_turn = "player"
                    continue
                
                # Check if boss has enough MP to use skill
                can_use_skill = boss_mp >= boss_skill_mp_cost and boss_skill_cooldown == 0
                
                # Boss uses skills more often, especially when low on HP
                skill_chance = 0.5
                if boss_hp < max_boss_hp * 0.4:  # Below 40% HP
                    skill_chance = 0.9
                
                use_skill = can_use_skill and random.random() < skill_chance
                
                if use_skill:
                    # Use skill
                    boss_mp -= boss_skill_mp_cost
                    boss_skill_cooldown = 3  # Set cooldown
                    
                    # Apply skill effects based on boss's skill
                    damage_multiplier = 1.5  # Default damage multiplier
                    
                    # Apply different effects based on skill
                    if "fire" in skill.lower() or "flame" in skill.lower() or "burn" in skill.lower():
                        player_status["burning"] = 3  # Burning for 3 turns
                        damage_multiplier = 1.3
                    elif "stun" in skill.lower() or "paralyz" in skill.lower():
                        player_status["stunned"] = 1  # Stunned for 1 turn
                        damage_multiplier = 1.2
                    elif "poison" in skill.lower() or "toxic" in skill.lower():
                        player_status["poisoned"] = 3  # Poisoned for 3 turns
                        damage_multiplier = 1.2
                    elif "ultimate" in skill.lower() or "final" in skill.lower():
                        damage_multiplier = 2.0  # Ultimate skills do double damage
                    
                    # Calculate damage with skill boost
                    base_damage = max(5, attack - (defense_stat // 2))
                    
                    # Reverse element effectiveness for boss attacks
                    reverse_element_multiplier = 1.0
                    if element in element_chart and card_element in element_chart[element]["strong"]:
                        reverse_element_multiplier = 1.5
                    elif element in element_chart and card_element in element_chart[element]["weak"]:
                        reverse_element_multiplier = 0.75
                    
                    damage = int(base_damage * damage_multiplier * reverse_element_multiplier)
                    
                    # Critical hit chance
                    is_critical = calculate_critical(boss_crit_rate)
                    if is_critical:
                        damage = int(damage * 1.5)
                    
                    # Apply damage
                    player_hp = max(0, player_hp - damage)
                    
                    # Build action text
                    action_text = f"**{name}** used **{skill}**!"
                    damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"Dealt `-{damage}`!"
                    
                    # Add status effect text
                    if "burning" in player_status:
                        damage_text += " 🔥 You are burning!"
                    elif "stunned" in player_status:
                        damage_text += " ⚡ You are stunned!"
                    elif "poisoned" in player_status:
                        damage_text += " ☠️ You are poisoned!"
                    
                    # Element effectiveness text
                    if reverse_element_multiplier > 1:
                        damage_text += " (Element effective! x1.5)"
                    elif reverse_element_multiplier < 1:
                        damage_text += " (Element ineffective! x0.75)"
                
                else:
                    # Regular attack
                    base_damage = max(5, attack - (defense_stat // 2))
                    
                    # Reverse element effectiveness for boss attacks
                    reverse_element_multiplier = 1.0
                    if element in element_chart and card_element in element_chart[element]["strong"]:
                        reverse_element_multiplier = 1.5
                    elif element in element_chart and card_element in element_chart[element]["weak"]:
                        reverse_element_multiplier = 0.75
                    
                    base_damage = int(base_damage * reverse_element_multiplier)
                    
                    # Check for dodge
                    is_dodged = calculate_dodge(dodge_rate)
                    
                    if is_dodged:
                        damage = 0
                        action_text = f"**{name}** attacked!"
                        damage_text = "😎 You dodged the attack!"
                    else:
                        # Critical hit chance
                        is_critical = calculate_critical(boss_crit_rate)
                        damage = int(base_damage * 1.5) if is_critical else base_damage
                        
                        # Apply damage
                        player_hp = max(0, player_hp - damage)
                        
                        action_text = f"**{name}** attacked!"
                        damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"{random.choice(battle_effects)} for `-{damage}`!"
                        
                        # Element effectiveness text
                        if reverse_element_multiplier > 1:
                            damage_text += " (Element effective! x1.5)"
                        elif reverse_element_multiplier < 1:
                            damage_text += " (Element ineffective! x0.75)"
                
                current_turn = "player"
            
            # MP regeneration (5% of max MP per turn)
            player_mp = min(player_max_mp, player_mp + int(player_max_mp * 0.05))
            boss_mp = min(boss_max_mp, boss_mp + int(boss_max_mp * 0.05))
            
            # Apply poison damage if applicable
            if "poisoned" in player_status:
                poison_damage = int(player_max_hp * 0.08)  # 8% damage
                player_hp = max(0, player_hp - poison_damage)
                damage_text += f" (☠️ -{poison_damage} poison damage)"
            
            if "poisoned" in boss_status:
                poison_damage = int(max_boss_hp * 0.08)  # 8% damage
                boss_hp = max(0, boss_hp - poison_damage)
                damage_text += f" (☠️ -{poison_damage} poison damage)"
            
            # Create battle embed
            title = f"Turn {turn}: {ctx.author.display_name if current_turn == 'player' else name}'s Turn Next"
            embed = discord.Embed(title=title, color=discord.Color.dark_red())
            
            # Player info
            player_status_text = ", ".join([f"{status.capitalize()}" for status in player_status]) if player_status else "None"
            embed.add_field(
                name=f"{ctx.author.display_name} - {card_name} (Lvl {card_level})",
                value=f"HP: {resource_bar(player_hp, player_max_hp)}\n"
                      f"MP: {resource_bar(player_mp, player_max_mp, '🔷', '⬜')}\n"
                      f"Status: {player_status_text}\n"
                      f"Skill Ready: {'✅' if player_skill_cooldown == 0 else f'❌ ({player_skill_cooldown} turns)'}",
                inline=False
            )
            
            # Boss info
            boss_status_text = ", ".join([f"{status.capitalize()}" for status in boss_status]) if boss_status else "None"
            embed.add_field(
                name=f"{name} (Lvl {level})",
                value=f"HP: {resource_bar(boss_hp, max_boss_hp)}\n"
                      f"MP: {resource_bar(boss_mp, boss_max_mp, '🔷', '⬜')}\n"
                      f"Status: {boss_status_text}\n"
                      f"Skill Ready: {'✅' if boss_skill_cooldown == 0 else f'❌ ({boss_skill_cooldown} turns)'}",
                inline=False
            )
            
            # Last action
            embed.add_field(name="Last Action", value=f"{action_text}\n{damage_text}", inline=False)
            
            # Set card image as thumbnail
            if card_image and turn == 1:
                embed.set_thumbnail(url=card_image)
            
            # Set boss image
            if image_url and turn == 1:
                embed.set_image(url=image_url)
            
            await battle_message.edit(embed=embed)
        
        # Battle ended - determine winner
        player_won = boss_hp <= 0
        
        # Remove from active battles
        if user_id in self.active_boss_battles:
            del self.active_boss_battles[user_id]
        
        # Update player stats
        if player_won:
            self.cursor.execute("UPDATE players SET boss_wins = boss_wins + 1 WHERE user_id = ?", (user_id,))
        
        # Calculate rewards
        if player_won:
            # Base rewards
            gold_earned = reward_gold
            exp_gained = reward_xp
            
            # Boost rewards based on remaining HP percentage
            hp_percent = player_hp / player_max_hp
            reward_multiplier = 1 + (hp_percent * 0.5)  # Up to 50% boost for full HP
            
            gold_earned = int(gold_earned * reward_multiplier)
            exp_gained = int(exp_gained * reward_multiplier)
            
            # Update player gold and MP in database
            self.cursor.execute("UPDATE players SET gold = gold + ?, mp = ? WHERE user_id = ?", 
                             (gold_earned, player_mp, user_id))
            
            # Add card experience
            self.cursor.execute("UPDATE usercards SET xp = xp + ? WHERE id = ?", (exp_gained, card_id))
            
            # Check for card level up
            self.cursor.execute("SELECT level, xp, rarity FROM usercards WHERE id = ?", (card_id,))
            card_level, card_xp, card_rarity = self.cursor.fetchone()
            
            # Calculate XP needed for next level
            xp_needed = int(100 * (1.2 ** (card_level - 1)) * (1.5 if card_rarity == "Legendary" else 
                                                              1.3 if card_rarity == "Epic" else 
                                                              1.2 if card_rarity == "Rare" else 
                                                              1.1 if card_rarity == "Uncommon" else 1.0))
            
            leveled_up = False
            new_level = card_level
            
            if card_xp >= xp_needed:
                new_level = card_level + 1
                new_xp = card_xp - xp_needed
                
                # Update card level and stats
                attack_boost = random.randint(3, 7)
                defense_boost = random.randint(2, 5)
                speed_boost = random.randint(1, 3)
                
                self.cursor.execute("""
                    UPDATE usercards 
                    SET level = ?, xp = ?, 
                        attack = attack + ?, 
                        defense = defense + ?,
                        speed = speed + ?
                    WHERE id = ?
                """, (new_level, new_xp, attack_boost, defense_boost, speed_boost, card_id))
                
                leveled_up = True
            
            # Add player experience
            player_exp_gained = int(exp_gained * 0.5)  # Half of card exp for player
            self.cursor.execute("UPDATE players SET xp = xp + ? WHERE user_id = ?", (player_exp_gained, user_id))
            
            # Check for player level up
            self.cursor.execute("SELECT level, xp FROM players WHERE user_id = ?", (user_id,))
            player_level, player_xp = self.cursor.fetchone()
            
            # Calculate player XP needed for next level
            player_xp_needed = 150 * (1.5 ** (player_level - 1))
            
            player_leveled_up = False
            new_player_level = player_level
            
            if player_xp >= player_xp_needed:
                new_player_level = player_level + 1
                player_xp = player_xp - player_xp_needed
                
                # Update player level
                self.cursor.execute("""
                    UPDATE players 
                    SET level = ?, xp = ?, 
                        max_stamina = max_stamina + 2,
                        max_mp = max_mp + 10
                    WHERE user_id = ?
                """, (new_player_level, player_xp, user_id))
                
                player_leveled_up = True
            
            # Calculate material drops
            boss_drops = self.get_boss_drops(boss_id)
            dropped_materials = []
            
            for material_id, material_name, material_rarity, drop_rate, min_qty, max_qty in boss_drops:
                # Calculate if drop happens
                if calculate_drop_chance(drop_rate):
                    # Determine quantity
                    quantity = random.randint(min_qty, max_qty)
                    
                    # Add to user's inventory
                    self.add_material_to_user(user_id, material_id, quantity)
                    
                    # Track for display
                    dropped_materials.append((material_name, quantity, material_rarity))
        else:
            # Still update MP if player lost
            self.cursor.execute("UPDATE players SET mp = ? WHERE user_id = ?", (player_mp, user_id))
        
        # Commit changes
        self.db.conn.commit()
        
        # Battle result embed
        if player_won:
            result_text = "**Victory!** 🎊"
            result_color = discord.Color.green()
            
            # Format materials text
            materials_text = ""
            if dropped_materials:
                materials_text = "**Materials Obtained:**\n"
                for mat_name, mat_qty, mat_rarity in dropped_materials:
                    rarity_emoji = "✨" if mat_rarity == "Legendary" else "🔥" if mat_rarity == "Epic" else "💫" if mat_rarity == "Rare" else "⭐"
                    materials_text += f"{rarity_emoji} {mat_qty}x {mat_name}\n"
            
            # XP and level-up messages
            xp_message = f"Your card gained `{exp_gained}` EXP!"
            if leveled_up:
                xp_message += f"\n✨ **{card_name} leveled up to {new_level}!** ✨"
            
            player_xp_message = f"You gained `{player_exp_gained}` EXP!"
            if player_leveled_up:
                player_xp_message += f"\n🌟 **You leveled up to {new_player_level}!** 🌟"
            
            result_message = (
                f"{card_name} defeated **{name}** in `{turn}` turns!\n"
                f"You earned `{gold_earned}` gold!\n"
                f"{xp_message}\n"
                f"{player_xp_message}\n\n"
                f"{materials_text}"
            )
        else:
            result_text = "**Defeat!** 💔"
            result_color = discord.Color.red()
            result_message = f"**{name}** defeated {card_name} in `{turn}` turns.\n"
                           
            # Add encouraging message
            encouragement = random.choice([
                "The boss was too powerful this time.",
                "Try again with a stronger card or different strategy.",
                "Maybe a card with a different element would be more effective?",
                "Keep training and you'll defeat it next time!",
                "Consider evolving your cards to gain more power."
            ])
            
            result_message += f"\n{encouragement}"
        
        embed = discord.Embed(title=result_text, color=result_color, description=result_message)
        
        # Add boss lore
        if player_won:
            embed.add_field(name="Boss Lore", value=lore, inline=False)
        
        # Set card and boss images
        if card_image:
            embed.set_thumbnail(url=card_image)
        if image_url:
            embed.set_image(url=image_url)
        
        await battle_message.edit(embed=embed)
    
    @commands.command(name="bossstats")
    async def boss_stats_command(self, ctx):
        """View your boss battle statistics"""
        user_id = ctx.author.id
        
        # Get player's boss stats
        self.cursor.execute("SELECT boss_wins FROM players WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        
        if not result:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
        
        boss_wins = result[0] or 0
        
        # Get recent boss battles
        self.cursor.execute("""
            SELECT b.enemy_card, b.turns, b.result, b.timestamp
            FROM battles b
            WHERE b.user_id = ? AND b.enemy_card IN (SELECT name FROM bosses)
            ORDER BY b.timestamp DESC
            LIMIT 5
        """, (user_id,))
        
        recent_battles = self.cursor.fetchall()
        
        # Create stats embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Boss Battle Statistics",
            description=f"Total Boss Victories: **{boss_wins}**",
            color=discord.Color.purple()
        )
        
        # Recent battles
        if recent_battles:
            recent_text = ""
            for boss_name, turns, result, timestamp in recent_battles:
                # Format timestamp
                import datetime
                battle_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                emoji = "✅" if result == "Win" else "❌"
                recent_text += f"{emoji} **{boss_name}** - {result} in {turns} turns - {battle_time}\n"
            
            embed.add_field(
                name="Recent Boss Battles",
                value=recent_text,
                inline=False
            )
        else:
            embed.add_field(
                name="Recent Boss Battles",
                value="No recent boss battles found.",
                inline=False
            )
        
        # Add boss rewards explanation
        embed.add_field(
            name="Boss Rewards",
            value="• Higher gold and EXP than regular battles\n"
                  "• Rare materials for card evolution\n"
                  "• Bonus rewards for quick victories\n"
                  "• Element advantages give 50% damage boost",
            inline=False
        )
        
        embed.set_footer(text="Use !boss to see available bosses • Each boss battle costs 5 stamina")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Boss(bot))
