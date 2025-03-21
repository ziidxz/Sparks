import discord
from discord.ext import commands
import random
import asyncio
import time
from cogs.card_images import card_images
from cogs.cards1 import cards_list as cards1
from cogs.cards2 import cards_list as cards2
from cogs.cards3 import cards_list as cards3
from utils.rewards import get_gold_drop, get_exp_drop
from utils.probability import calculate_critical, calculate_dodge

class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="battle")
    async def battle_command(self, ctx):
        """⚔️ Battle against an AI opponent"""
        user_id = ctx.author.id

        # Check if user exists
        self.cursor.execute("SELECT stamina, level FROM players WHERE user_id = ?", (user_id,))
        player_data = self.cursor.fetchone()
        
        if not player_data:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
        
        stamina, player_level = player_data
        
        # Check stamina
        if stamina < 3:
            await ctx.send(f"{ctx.author.mention}, you need at least **3 stamina** to battle!")
            return
        
        # Deduct stamina
        self.cursor.execute("UPDATE players SET stamina = stamina - 3 WHERE user_id = ?", (user_id,))
        self.db.conn.commit()
        
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
        
        card_id, card_name, attack, defense, speed, level, element, skill, skill_desc, skill_mp, crit_rate, dodge_rate, rarity, image_url = player_card
        
        # Combine all cards and filter by player level
        all_cards = cards1 + cards2 + cards3
        
        # Filter enemies by player level (slightly above or below)
        max_enemy_level = player_level + 3
        min_enemy_level = max(1, player_level - 2)
        
        # Select suitable opponents
        suitable_enemies = []
        for card in all_cards:
            enemy_level = random.randint(min_enemy_level, max_enemy_level)
            if enemy_level <= max_enemy_level:
                # Create a copy of the card with the adjusted level
                enemy_card = card.copy()
                enemy_card["level"] = enemy_level
                suitable_enemies.append(enemy_card)
        
        # Pick a random enemy
        enemy_card_data = random.choice(suitable_enemies)
        
        # Adjust enemy stats based on level
        enemy_level = enemy_card_data["level"]
        enemy_attack = enemy_card_data["attack"] + (enemy_level * 4)
        enemy_defense = enemy_card_data["defense"] + (enemy_level * 3)
        enemy_speed = enemy_card_data.get("speed", 50) + (enemy_level * 2)
        enemy_hp = 500 + (enemy_level * 15)
        enemy_max_hp = enemy_hp
        enemy_mp = 100
        enemy_max_mp = 100
        enemy_crit_rate = enemy_card_data.get("critical_rate", 5)
        enemy_dodge_rate = enemy_card_data.get("dodge_rate", 5)
        
        # Get enemy image
        enemy_image = card_images.get(enemy_card_data["name"], None)
        
        # Setup player stats
        player_hp = 500 + (level * 15)
        player_max_hp = player_hp
        
        # Get player MP from database
        self.cursor.execute("SELECT mp FROM players WHERE user_id = ?", (user_id,))
        player_mp = self.cursor.fetchone()[0]
        player_max_mp = 100 + (level * 5)  # Scale max MP with level
        
        # Battle setup
        battle_message = await ctx.send("⚔️ **Battle Start!**")
        turn = 0
        
        # Determine who goes first based on speed
        player_first = speed >= enemy_speed
        current_turn = "player" if player_first else "enemy"
        
        # Battle effects and animations
        battle_effects = ["Bonked", "Whacked", "Booped", "Thwacked", "Slammed", "Pummeled"]
        
        # Skill cooldowns
        player_skill_cooldown = 0
        enemy_skill_cooldown = 0
        
        # Status effects (turns remaining)
        player_status = {}
        enemy_status = {}
        
        # Battle loop
        while player_hp > 0 and enemy_hp > 0:
            turn += 1
            await asyncio.sleep(1.5)  # Slightly faster pacing
            
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
            
            for status, turns in list(enemy_status.items()):
                if status == "burning":
                    burn_damage = int(enemy_max_hp * 0.05)  # 5% damage
                    enemy_hp = max(0, enemy_hp - burn_damage)
                    
                enemy_status[status] -= 1
                if enemy_status[status] <= 0:
                    del enemy_status[status]
            
            # Handle cooldowns
            if player_skill_cooldown > 0:
                player_skill_cooldown -= 1
            if enemy_skill_cooldown > 0:
                enemy_skill_cooldown -= 1
            
            # Battle logic
            if current_turn == "player":
                # Player's turn
                # Check if player has enough MP to use skill
                can_use_skill = player_mp >= skill_mp and player_skill_cooldown == 0
                
                # Randomly decide to use skill (more likely if HP is low)
                skill_chance = 0.3
                if player_hp < player_max_hp * 0.4:  # Below 40% HP
                    skill_chance = 0.7
                
                use_skill = can_use_skill and random.random() < skill_chance
                
                if use_skill:
                    # Use skill
                    player_mp -= skill_mp
                    player_skill_cooldown = 3  # Set cooldown
                    
                    # Apply skill effects
                    if "fire" in skill.lower() or "flame" in skill.lower():
                        enemy_status["burning"] = 3  # Burning for 3 turns
                        damage_multiplier = 1.3
                    elif "heal" in skill.lower():
                        heal_amount = int(player_max_hp * 0.2)  # Heal 20% of max HP
                        player_hp = min(player_max_hp, player_hp + heal_amount)
                        damage_multiplier = 0.5
                    else:
                        damage_multiplier = 1.5  # Generic damage boost
                    
                    # Calculate damage with skill boost
                    base_damage = max(5, attack - (enemy_defense // 2))
                    damage = int(base_damage * damage_multiplier)
                    
                    # Critical hit chance
                    is_critical = calculate_critical(crit_rate)
                    if is_critical:
                        damage = int(damage * 1.5)
                    
                    # Apply damage
                    enemy_hp = max(0, enemy_hp - damage)
                    
                    # Build action text
                    action_text = f"**{ctx.author.display_name}** used **{skill}**!"
                    damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"Dealt `-{damage}`!"
                    
                    if "burning" in enemy_status:
                        damage_text += " 🔥 Enemy is burning!"
                    elif "heal" in skill.lower():
                        damage_text = f"💖 Healed `+{heal_amount}`!"
                    
                else:
                    # Regular attack
                    base_damage = max(5, attack - (enemy_defense // 2))
                    
                    # Check for dodge
                    is_dodged = calculate_dodge(enemy_dodge_rate)
                    
                    if is_dodged:
                        damage = 0
                        action_text = f"**{ctx.author.display_name}** attacked!"
                        damage_text = "😎 Enemy dodged the attack!"
                    else:
                        # Critical hit chance
                        is_critical = calculate_critical(crit_rate)
                        damage = base_damage * 1.5 if is_critical else base_damage
                        
                        # Apply damage
                        enemy_hp = max(0, enemy_hp - damage)
                        
                        action_text = f"**{ctx.author.display_name}** attacked!"
                        damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"Dealt `-{damage}`!"
                
                current_turn = "enemy"
                
            else:
                # Enemy's turn
                # Check if enemy has enough MP to use skill
                enemy_skill = enemy_card_data.get("skill", "Basic Attack")
                enemy_skill_mp_cost = enemy_card_data.get("skill_mp_cost", 20)
                can_use_skill = enemy_mp >= enemy_skill_mp_cost and enemy_skill_cooldown == 0
                
                # Randomly decide to use skill (more likely if HP is low)
                skill_chance = 0.3
                if enemy_hp < enemy_max_hp * 0.4:  # Below 40% HP
                    skill_chance = 0.7
                
                use_skill = can_use_skill and random.random() < skill_chance
                
                if use_skill:
                    # Use skill
                    enemy_mp -= enemy_skill_mp_cost
                    enemy_skill_cooldown = 3  # Set cooldown
                    
                    # Apply skill effects
                    if "fire" in enemy_skill.lower() or "flame" in enemy_skill.lower():
                        player_status["burning"] = 3  # Burning for 3 turns
                        damage_multiplier = 1.3
                    elif "heal" in enemy_skill.lower():
                        heal_amount = int(enemy_max_hp * 0.2)  # Heal 20% of max HP
                        enemy_hp = min(enemy_max_hp, enemy_hp + heal_amount)
                        damage_multiplier = 0.5
                    else:
                        damage_multiplier = 1.5  # Generic damage boost
                    
                    # Calculate damage with skill boost
                    base_damage = max(5, enemy_attack - (defense // 2))
                    damage = int(base_damage * damage_multiplier)
                    
                    # Critical hit chance
                    is_critical = calculate_critical(enemy_crit_rate)
                    if is_critical:
                        damage = int(damage * 1.5)
                    
                    # Apply damage
                    player_hp = max(0, player_hp - damage)
                    
                    # Build action text
                    action_text = f"**{enemy_card_data['name']}** used **{enemy_skill}**!"
                    damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"Dealt `-{damage}`!"
                    
                    if "burning" in player_status:
                        damage_text += " 🔥 You are burning!"
                    elif "heal" in enemy_skill.lower():
                        damage_text = f"💖 Healed `+{heal_amount}`!"
                    
                else:
                    # Regular attack
                    base_damage = max(5, enemy_attack - (defense // 2))
                    
                    # Check for dodge
                    is_dodged = calculate_dodge(dodge_rate)
                    
                    if is_dodged:
                        damage = 0
                        action_text = f"**{enemy_card_data['name']}** attacked!"
                        damage_text = "😎 You dodged the attack!"
                    else:
                        # Critical hit chance
                        is_critical = calculate_critical(enemy_crit_rate)
                        damage = base_damage * 1.5 if is_critical else base_damage
                        
                        # Apply damage
                        player_hp = max(0, player_hp - damage)
                        
                        action_text = f"**{enemy_card_data['name']}** attacked!"
                        damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"{random.choice(battle_effects)} for `-{damage}`!"
                
                current_turn = "player"
            
            # MP regeneration (5% of max MP per turn)
            player_mp = min(player_max_mp, player_mp + int(player_max_mp * 0.05))
            enemy_mp = min(enemy_max_mp, enemy_mp + int(enemy_max_mp * 0.05))
            
            # Create battle embed
            title = f"Turn {turn}: {current_turn.capitalize()}'s Turn Next"
            embed = discord.Embed(title=title, color=discord.Color.purple())
            
            # Player info
            player_status_text = ", ".join([f"{status.capitalize()}" for status in player_status]) if player_status else "None"
            embed.add_field(
                name=f"{ctx.author.display_name} - {card_name} (Lvl {level})",
                value=f"HP: {resource_bar(player_hp, player_max_hp)}\n"
                      f"MP: {resource_bar(player_mp, player_max_mp, '🔷', '⬜')}\n"
                      f"Status: {player_status_text}\n"
                      f"Skill Ready: {'✅' if player_skill_cooldown == 0 else f'❌ ({player_skill_cooldown} turns)'}",
                inline=False
            )
            
            # Enemy info
            enemy_status_text = ", ".join([f"{status.capitalize()}" for status in enemy_status]) if enemy_status else "None"
            embed.add_field(
                name=f"{enemy_card_data['name']} (Lvl {enemy_level})",
                value=f"HP: {resource_bar(enemy_hp, enemy_max_hp)}\n"
                      f"MP: {resource_bar(enemy_mp, enemy_max_mp, '🔷', '⬜')}\n"
                      f"Status: {enemy_status_text}\n"
                      f"Skill Ready: {'✅' if enemy_skill_cooldown == 0 else f'❌ ({enemy_skill_cooldown} turns)'}",
                inline=False
            )
            
            # Last action
            embed.add_field(name="Last Action", value=f"{action_text}\n{damage_text}", inline=False)
            
            # Set image
            if image_url and turn == 1:
                embed.set_thumbnail(url=image_url)
            if enemy_image and turn == 1:
                embed.set_image(url=enemy_image)
            
            await battle_message.edit(embed=embed)
        
        # Battle ended - determine winner
        player_won = enemy_hp <= 0
        
        # Save battle record
        self.cursor.execute("""
            INSERT INTO battles (user_id, player_card, enemy_card, turns, result)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, card_name, enemy_card_data["name"], turn, "Win" if player_won else "Loss"))
        
        # Update player stats
        if player_won:
            self.cursor.execute("UPDATE players SET wins = wins + 1 WHERE user_id = ?", (user_id,))
        else:
            self.cursor.execute("UPDATE players SET losses = losses + 1 WHERE user_id = ?", (user_id,))
        
        # Calculate rewards
        if player_won:
            # Calculate gold and exp earned
            gold_earned = get_gold_drop(enemy_level)
            exp_gained = get_exp_drop(enemy_level)
            
            # Update player gold in database
            self.cursor.execute("UPDATE players SET gold = gold + ? WHERE user_id = ?", (gold_earned, user_id,))
            
            # Add card experience
            self.cursor.execute("UPDATE usercards SET xp = xp + ? WHERE id = ?", (exp_gained, card_id))
            
            # Check for card level up
            self.cursor.execute("SELECT level, xp FROM usercards WHERE id = ?", (card_id,))
            card_level, card_xp = self.cursor.fetchone()
            
            # Calculate XP needed for next level
            xp_needed = 100 * (1.2 ** (card_level - 1))
            
            leveled_up = False
            new_level = card_level
            
            if card_xp >= xp_needed:
                new_level = card_level + 1
                card_xp = card_xp - xp_needed
                
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
                """, (new_level, card_xp, attack_boost, defense_boost, speed_boost, card_id))
                
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
        
        # Update MP in database
        self.cursor.execute("UPDATE players SET mp = ? WHERE user_id = ?", (player_mp, user_id))
        
        # Commit changes
        self.db.conn.commit()
        
        # Battle result embed
        if player_won:
            result_text = "**You Won!** 🎉"
            result_color = discord.Color.green()
            
            # XP and level-up messages
            xp_message = f"Your card gained `{exp_gained}` EXP!"
            if leveled_up:
                xp_message += f"\n✨ **{card_name} leveled up to {new_level}!** ✨"
            
            player_xp_message = f"You gained `{player_exp_gained}` EXP!"
            if player_leveled_up:
                player_xp_message += f"\n🌟 **You leveled up to {new_player_level}!** 🌟"
            
            result_message = (
                f"{card_name} defeated {enemy_card_data['name']} in `{turn}` turns!\n"
                f"You earned `{gold_earned}` gold!\n"
                f"{xp_message}\n"
                f"{player_xp_message}"
            )
        else:
            result_text = "**You Lost!** 💔"
            result_color = discord.Color.red()
            result_message = f"{enemy_card_data['name']} defeated {card_name} in `{turn}` turns.\nBetter luck next time!"
        
        embed = discord.Embed(title=result_text, color=result_color, description=result_message)
        
        # Set card and enemy images
        if image_url:
            embed.set_thumbnail(url=image_url)
        if enemy_image:
            embed.set_image(url=enemy_image)
        
        await battle_message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Battle(bot))
