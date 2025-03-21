"""
Enhanced battle system with MP bars, skill usage, and immersive animations.
This system powers both PvE and PvP battles with a more engaging experience.
"""

import discord
from discord.ext import commands
import random
import time
import asyncio
import math
from datetime import datetime, timedelta

import discord
from discord import ui, Interaction, ButtonStyle

class BattleSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.active_battles = {}  # Track active battles to prevent duplicates
        
    def get_player_card(self, user_id):
        """Get the player's equipped card with detailed stats."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT c.*, uc.level, uc.xp, uc.id as user_card_id
            FROM api_user_cards uc
            JOIN api_cards c ON uc.card_id = c.id
            JOIN api_players p ON uc.player_id = p.id
            WHERE p.discord_id = ? AND uc.equipped = 1
        """, (user_id,))
        
        card = cursor.fetchone()
        cursor.close()
        
        if not card:
            return None
            
        # Convert to dictionary for easier access
        columns = [col[0] for col in cursor.description]
        card_dict = {columns[i]: card[i] for i in range(len(columns))}
        
        # Calculate stats based on level
        level_bonus = (card_dict['level'] - 1) * 0.1  # 10% per level
        card_dict['adjusted_attack'] = int(card_dict['attack'] * (1 + level_bonus))
        card_dict['adjusted_defense'] = int(card_dict['defense'] * (1 + level_bonus))
        card_dict['adjusted_speed'] = int(card_dict['speed'] * (1 + level_bonus))
        
        # Calculate MP stats based on card level
        card_dict['max_mp'] = 50 + (card_dict['level'] * 5)  # 50 MP + 5 per level
        card_dict['mp'] = card_dict['max_mp']  # Start with full MP
        
        # Calculate additional stats
        card_dict['crit_chance'] = 5 + (card_dict['level'] * 0.5)  # Base 5% + 0.5% per level
        card_dict['dodge_chance'] = 3 + (card_dict['level'] * 0.3)  # Base 3% + 0.3% per level
        
        return card_dict
        
    def get_player_data(self, user_id):
        """Get player's battle-relevant data."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, username, level, xp, stamina, max_stamina, 
                   last_stamina_update, gold, diamonds, wins, losses
            FROM api_players
            WHERE discord_id = ?
        """, (user_id,))
        
        player = cursor.fetchone()
        cursor.close()
        
        if not player:
            return None
            
        # Convert to dictionary for easier access
        columns = [col[0] for col in cursor.description]
        player_dict = {columns[i]: player[i] for i in range(len(columns))}
        
        # Calculate current stamina based on regeneration time
        if player_dict['last_stamina_update']:
            last_update = datetime.fromisoformat(player_dict['last_stamina_update'].replace('Z', '+00:00'))
            current_time = datetime.utcnow()
            hours_passed = (current_time - last_update).total_seconds() / 3600
            
            # Regenerate 1 stamina per 10 minutes (6 per hour)
            stamina_gained = int(hours_passed * 6)
            
            if stamina_gained > 0:
                new_stamina = min(player_dict['stamina'] + stamina_gained, player_dict['max_stamina'])
                player_dict['stamina'] = new_stamina
                
                # Update in database
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    UPDATE api_players 
                    SET stamina = ?, last_stamina_update = ? 
                    WHERE id = ?
                """, (new_stamina, current_time.isoformat(), player_dict['id']))
                self.db.conn.commit()
                cursor.close()
        
        return player_dict
        
    def update_player_mp(self, user_id, mp):
        """Update player's MP."""
        # MP is not stored persistently, it's just for battle
        pass
        
    def update_player_stamina(self, user_id, stamina):
        """Update player's stamina."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE api_players 
            SET stamina = ?, last_stamina_update = ? 
            WHERE discord_id = ?
        """, (stamina, datetime.utcnow().isoformat(), user_id))
        self.db.conn.commit()
        cursor.close()
        
    def add_player_exp(self, user_id, exp_amount):
        """Add experience to the player and handle level ups."""
        cursor = self.db.conn.cursor()
        
        # Get current player level and XP
        cursor.execute("""
            SELECT id, level, xp, max_stamina
            FROM api_players
            WHERE discord_id = ?
        """, (user_id,))
        
        player = cursor.fetchone()
        if not player:
            cursor.close()
            return False, 0, 0
            
        player_id, current_level, current_xp, current_max_stamina = player
        
        # Add XP
        new_xp = current_xp + exp_amount
        
        # Check for level up
        required_xp = self.get_required_player_xp(current_level)
        level_ups = 0
        new_level = current_level
        
        while new_xp >= required_xp:
            new_xp -= required_xp
            new_level += 1
            level_ups += 1
            required_xp = self.get_required_player_xp(new_level)
        
        # Calculate new stamina cap if leveled up
        new_max_stamina = current_max_stamina
        if level_ups > 0:
            new_max_stamina = 100 + (new_level * 5)  # Base 100 + 5 per level
        
        # Update player
        cursor.execute("""
            UPDATE api_players
            SET level = ?, xp = ?, max_stamina = ?
            WHERE id = ?
        """, (new_level, new_xp, new_max_stamina, player_id))
        
        self.db.conn.commit()
        cursor.close()
        
        return (level_ups > 0), new_level, level_ups
        
    def get_required_player_xp(self, level):
        """Calculate required XP for next player level."""
        return 100 * level + int(math.pow(level, 1.5) * 20)
        
    def add_card_exp(self, card_id, exp_amount):
        """Add experience to a card and handle level ups."""
        cursor = self.db.conn.cursor()
        
        # Get current card level and XP
        cursor.execute("""
            SELECT uc.id, uc.level, uc.xp, c.rarity
            FROM api_user_cards uc
            JOIN api_cards c ON uc.card_id = c.id
            WHERE uc.id = ?
        """, (card_id,))
        
        card = cursor.fetchone()
        if not card:
            cursor.close()
            return False, 0, 0
            
        user_card_id, current_level, current_xp, rarity = card
        
        # Add XP
        new_xp = current_xp + exp_amount
        
        # Check for level up (XP requirements increase with rarity)
        rarity_multiplier = {
            "Common": 1.0,
            "Uncommon": 1.2,
            "Rare": 1.5,
            "Epic": 1.8,
            "Legendary": 2.0
        }.get(rarity, 1.0)
        
        required_xp = self.get_required_card_xp(current_level, rarity_multiplier)
        level_ups = 0
        new_level = current_level
        
        while new_xp >= required_xp:
            new_xp -= required_xp
            new_level += 1
            level_ups += 1
            required_xp = self.get_required_card_xp(new_level, rarity_multiplier)
        
        # Update card
        cursor.execute("""
            UPDATE api_user_cards
            SET level = ?, xp = ?
            WHERE id = ?
        """, (new_level, new_xp, user_card_id))
        
        self.db.conn.commit()
        cursor.close()
        
        return (level_ups > 0), new_level, level_ups
        
    def get_required_card_xp(self, level, rarity_multiplier=1.0):
        """Calculate required XP for next card level."""
        base_xp = 50 * level + int(math.pow(level, 1.8) * 10)
        return int(base_xp * rarity_multiplier)
        
    def generate_enemy(self, player_level, dungeon_id=None, floor=None, is_boss=False):
        """Generate an enemy based on player level and optionally dungeon info."""
        # Base enemy scaling
        level_factor = 0.8 if not is_boss else 1.5
        enemy_level = max(1, int(player_level * level_factor))
        
        # Further adjust based on dungeon and floor
        if dungeon_id and floor:
            floor_factor = 1.0 + (floor * 0.1)
            enemy_level = max(enemy_level, int(player_level * floor_factor))
        
        # Get potential card templates
        cursor = self.db.conn.cursor()
        
        # For bosses, select higher rarity cards
        if is_boss:
            rarities = ["Epic", "Legendary"]
        else:
            # Regular enemies use more common rarities
            rarities = ["Common", "Uncommon", "Rare"] 
        
        rarities_placeholders = ", ".join(["?" for _ in rarities])
        
        cursor.execute(f"""
            SELECT * FROM api_cards
            WHERE rarity IN ({rarities_placeholders})
            ORDER BY RANDOM()
            LIMIT 1
        """, rarities)
        
        card = cursor.fetchone()
        cursor.close()
        
        if not card:
            # Fallback in case no cards are found
            return {
                "name": f"Level {enemy_level} Slime",
                "level": enemy_level,
                "max_hp": 50 + (enemy_level * 10),
                "hp": 50 + (enemy_level * 10),
                "attack": 10 + (enemy_level * 3),
                "defense": 5 + (enemy_level * 2),
                "speed": 8 + (enemy_level * 2),
                "max_mp": 30 + (enemy_level * 3),
                "mp": 30 + (enemy_level * 3),
                "element": random.choice(["Fire", "Water", "Earth", "Air"]),
                "skill": "Tackle",
                "skill_description": "A basic attack",
                "skill_cost": 10,
                "crit_chance": 5,
                "dodge_chance": 3,
                "is_boss": is_boss,
                "image_url": None
            }
        
        # Convert to dictionary
        columns = [col[0] for col in cursor.description]
        enemy = {columns[i]: card[i] for i in range(len(columns))}
        
        # Scale enemy stats based on level
        stat_multiplier = 1.0 + (enemy_level * 0.1)
        if is_boss:
            stat_multiplier *= 1.5  # Bosses are significantly stronger
            
        # Set HP based on defense stat and level
        enemy["max_hp"] = int((enemy["defense"] * 2) * stat_multiplier)
        enemy["hp"] = enemy["max_hp"]
        
        # Set MP based on level
        enemy["max_mp"] = 40 + (enemy_level * 5)
        enemy["mp"] = enemy["max_mp"]
        
        # Adjust base stats
        enemy["attack"] = int(enemy["attack"] * stat_multiplier)
        enemy["defense"] = int(enemy["defense"] * stat_multiplier)
        enemy["speed"] = int(enemy["speed"] * stat_multiplier)
        
        # Set skill cost
        enemy["skill_cost"] = enemy.get("mp_cost", 15)
        
        # Set combat stats
        enemy["level"] = enemy_level
        enemy["crit_chance"] = 5 + (enemy_level * 0.3)
        enemy["dodge_chance"] = 3 + (enemy_level * 0.2)
        enemy["is_boss"] = is_boss
        
        # Adjust name for bosses
        if is_boss:
            enemy["name"] = f"Boss {enemy['name']}"
        
        return enemy
        
    def calculate_damage(self, attacker, defender, is_skill=False):
        """Calculate damage dealt in an attack."""
        # Base damage from attack stat
        base_damage = attacker["attack"]
        
        # Adjustments for skill usage
        if is_skill:
            base_damage = int(base_damage * 1.5)  # Skills do 50% more damage
        
        # Apply variance (±10%)
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)
        
        # Check for critical hit
        is_critical = random.random() * 100 < attacker.get("crit_chance", 5)
        if is_critical:
            damage = int(damage * 1.8)  # Critical hits do 80% more damage
        
        # Calculate defense reduction
        defense_factor = 100 / (100 + defender["defense"])
        damage = int(damage * defense_factor)
        
        # Check for elemental effectiveness
        element_multiplier = self.calculate_element_effectiveness(
            attacker.get("element", "Normal"),
            defender.get("element", "Normal")
        )
        damage = int(damage * element_multiplier)
        is_effective = element_multiplier > 1.0
        
        # Ensure minimum damage
        damage = max(1, damage)
        
        return damage, is_critical, is_effective
        
    def calculate_element_effectiveness(self, attacker_element, defender_element):
        """Calculate elemental effectiveness multiplier."""
        # Element effectiveness chart
        effectiveness = {
            "Fire": {"Water": 0.5, "Ice": 2.0, "Earth": 0.7, "Air": 1.2},
            "Water": {"Fire": 2.0, "Electric": 0.5, "Earth": 1.2, "Ice": 0.7},
            "Earth": {"Air": 0.5, "Fire": 1.2, "Electric": 2.0, "Water": 0.7},
            "Air": {"Earth": 2.0, "Electric": 0.7, "Ice": 0.5, "Fire": 0.7},
            "Electric": {"Water": 2.0, "Air": 1.2, "Earth": 0.5, "Ice": 0.7},
            "Ice": {"Fire": 0.5, "Water": 1.2, "Air": 2.0, "Earth": 0.7},
            "Light": {"Dark": 2.0, "Cute": 0.7, "Star": 0.5},
            "Dark": {"Light": 0.5, "Sweet": 0.7, "Star": 2.0},
            "Cute": {"Light": 1.2, "Dark": 0.7, "Sweet": 2.0},
            "Sweet": {"Cute": 0.5, "Dark": 1.2, "Light": 0.7},
            "Star": {"Light": 1.5, "Dark": 0.5, "Cute": 1.2, "Sweet": 1.2}
        }
        
        # Default is neutral effectiveness
        if attacker_element not in effectiveness:
            return 1.0
            
        # Get defender-specific multiplier
        element_chart = effectiveness[attacker_element]
        return element_chart.get(defender_element, 1.0)
        
    def resource_bar(self, current, maximum, length=10, filled="█", empty="░"):
        """Generate a visual bar for resources like HP and MP."""
        if maximum <= 0:
            return empty * length
            
        fill_length = int(current / maximum * length)
        bar = filled * fill_length + empty * (length - fill_length)
        return bar
        
    def format_move_result(self, attacker_name, defender_name, damage, defender_hp, defender_max_hp, 
                           is_critical, is_effective, is_skill=False, skill_name=None):
        """Format the result of an attack move for display."""
        # Emoji for attack type
        attack_emoji = "⚡" if is_skill else "⚔️"
        
        # Additional effect emojis
        critical_emoji = "💥 **CRITICAL!** " if is_critical else ""
        effective_emoji = "✨ **SUPER EFFECTIVE!** " if is_effective else ""
        
        # Format the move description
        if is_skill:
            move_text = f"{attack_emoji} {attacker_name} used **{skill_name}**!"
        else:
            move_text = f"{attack_emoji} {attacker_name} attacked!"
            
        # Format the damage line
        damage_text = f"{critical_emoji}{effective_emoji}Deals **{damage}** damage to {defender_name}!"
        
        # HP bar
        hp_percent = int((defender_hp / defender_max_hp) * 100)
        hp_bar = self.resource_bar(defender_hp, defender_max_hp)
        hp_text = f"{defender_name}'s HP: {defender_hp}/{defender_max_hp} ({hp_percent}%)\n{hp_bar}"
        
        return f"{move_text}\n{damage_text}\n{hp_text}"
        
    async def add_battle_reward(self, user_id, player_card, enemy, turns_taken):
        """Add rewards after winning a battle."""
        # Base rewards
        base_xp = 10 + (enemy["level"] * 3)
        base_gold = 5 + (enemy["level"] * 2)
        
        # Adjustments for bosses
        if enemy.get("is_boss", False):
            base_xp *= 2.5
            base_gold *= 3
            
        # Efficiency bonus for quick battles
        efficiency_factor = max(0.5, 1.0 - (turns_taken * 0.05))
        
        # Calculate final rewards
        gained_xp = int(base_xp * efficiency_factor)
        gained_gold = int(base_gold * efficiency_factor)
        
        # Award player XP
        leveled_up, new_level, level_ups = self.add_player_exp(user_id, gained_xp)
        
        # Award card XP
        card_leveled, card_new_level, card_level_ups = self.add_card_exp(
            player_card["user_card_id"], 
            int(gained_xp * 0.8)  # Card gets 80% of player XP
        )
        
        # Award gold
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE api_players
            SET gold = gold + ?, wins = wins + 1
            WHERE discord_id = ?
        """, (gained_gold, user_id))
        self.db.conn.commit()
        cursor.close()
        
        # Return reward information
        return {
            "xp": gained_xp,
            "gold": gained_gold,
            "leveled_up": leveled_up,
            "new_level": new_level if leveled_up else None,
            "level_ups": level_ups,
            "card_leveled": card_leveled,
            "card_new_level": card_new_level if card_leveled else None,
            "card_level_ups": card_level_ups
        }
        
    def format_battle_status(self, player_name, player_card, player_hp, player_max_hp, player_mp, player_max_mp,
                           enemy_name, enemy_hp, enemy_max_hp, enemy_mp, enemy_max_mp):
        """Format the current battle status for display."""
        # Player HP/MP bars
        player_hp_bar = self.resource_bar(player_hp, player_max_hp)
        player_mp_bar = self.resource_bar(player_mp, player_max_mp)
        
        # Enemy HP/MP bars
        enemy_hp_bar = self.resource_bar(enemy_hp, enemy_max_hp)
        enemy_mp_bar = self.resource_bar(enemy_mp, enemy_max_mp)
        
        # Calculate HP/MP percentages
        player_hp_percent = int((player_hp / player_max_hp) * 100)
        player_mp_percent = int((player_mp / player_max_mp) * 100)
        enemy_hp_percent = int((enemy_hp / enemy_max_hp) * 100)
        enemy_mp_percent = int((enemy_mp / enemy_max_mp) * 100)
        
        # Format the status message
        status = (
            f"**{player_name}** [Lv. {player_card['level']}] "
            f"({player_card['element']} {player_card['rarity']})\n"
            f"❤️ HP: {player_hp}/{player_max_hp} ({player_hp_percent}%)\n"
            f"{player_hp_bar}\n"
            f"🔮 MP: {player_mp}/{player_max_mp} ({player_mp_percent}%)\n"
            f"{player_mp_bar}\n\n"
            f"**VS**\n\n"
            f"**{enemy_name}** [Lv. {enemy['level']}] "
            f"({enemy['element']} {enemy['rarity']})\n"
            f"❤️ HP: {enemy_hp}/{enemy_max_hp} ({enemy_hp_percent}%)\n"
            f"{enemy_hp_bar}\n"
            f"🔮 MP: {enemy_mp}/{enemy_max_mp} ({enemy_mp_percent}%)\n"
            f"{enemy_mp_bar}"
        )
        
        return status
        
    class BattleView(ui.View):
        def __init__(self, battle_cog, ctx, player_data, player_card, enemy):
            super().__init__(timeout=120)
            self.battle_cog = battle_cog
            self.ctx = ctx
            self.player_data = player_data
            self.player_card = player_card
            self.enemy = enemy
            
            # Battle state
            self.player_hp = player_card["adjusted_attack"] * 2  # Based on attack for variety
            self.player_max_hp = self.player_hp
            self.player_mp = player_card["max_mp"]
            self.player_max_mp = player_card["max_mp"]
            
            self.enemy_hp = enemy["hp"]
            self.enemy_max_hp = enemy["max_hp"]
            self.enemy_mp = enemy["mp"]
            self.enemy_max_mp = enemy["max_mp"]
            
            self.battle_log = []
            self.turn_count = 0
            self.battle_over = False
            self.update_button_states()
            
        async def interaction_check(self, interaction):
            """Check if the interaction is from the battle owner."""
            return interaction.user.id == self.ctx.author.id
            
        def update_button_states(self):
            """Update button states based on battle state."""
            # Disable buttons if battle is over
            if self.battle_over:
                for item in self.children:
                    item.disabled = True
                return
                
            # Update skill button based on MP
            skill_cost = self.player_card.get("mp_cost", 20)
            self.children[1].disabled = self.player_mp < skill_cost
            
            skill_name = self.player_card.get("skill", "Unknown Skill")
            self.children[1].label = f"{skill_name} ({skill_cost} MP)"
            
        @ui.button(label="Attack", style=ButtonStyle.danger)
        async def attack_button(self, interaction: Interaction, button: ui.Button):
            """Execute a basic attack."""
            if self.battle_over:
                return
                
            # Increment turn counter
            self.turn_count += 1
            
            # Calculate damage
            damage, is_critical, is_effective = self.battle_cog.calculate_damage(
                self.player_card, self.enemy, is_skill=False
            )
            
            # Apply damage to enemy
            self.enemy_hp = max(0, self.enemy_hp - damage)
            
            # Format result
            result = self.battle_cog.format_move_result(
                self.ctx.author.display_name,
                self.enemy["name"],
                damage,
                self.enemy_hp,
                self.enemy_max_hp,
                is_critical,
                is_effective
            )
            
            # Add to battle log
            self.battle_log.append(result)
            
            # Check if enemy defeated
            if self.enemy_hp <= 0:
                await self.end_battle("player")
                return
                
            # Enemy turn
            await self.enemy_turn()
            
            # Update battle status
            await self.update_battle_message("")
            
        @ui.button(label="Skill", style=ButtonStyle.primary)
        async def skill_button(self, interaction: Interaction, button: ui.Button):
            """Use the card's special skill."""
            if self.battle_over:
                return
                
            # Check MP cost
            skill_cost = self.player_card.get("mp_cost", 20)
            if self.player_mp < skill_cost:
                await interaction.response.send_message("Not enough MP to use skill!", ephemeral=True)
                return
                
            # Consume MP
            self.player_mp -= skill_cost
            
            # Increment turn counter
            self.turn_count += 1
            
            # Calculate damage
            damage, is_critical, is_effective = self.battle_cog.calculate_damage(
                self.player_card, self.enemy, is_skill=True
            )
            
            # Apply damage to enemy
            self.enemy_hp = max(0, self.enemy_hp - damage)
            
            # Format result
            result = self.battle_cog.format_move_result(
                self.ctx.author.display_name,
                self.enemy["name"],
                damage,
                self.enemy_hp,
                self.enemy_max_hp,
                is_critical,
                is_effective,
                is_skill=True,
                skill_name=self.player_card["skill"]
            )
            
            # Add to battle log
            self.battle_log.append(result)
            
            # Check if enemy defeated
            if self.enemy_hp <= 0:
                await self.end_battle("player")
                return
                
            # Enemy turn
            await self.enemy_turn()
            
            # Update battle status
            await self.update_battle_message("")
            
        @ui.button(label="Flee", style=ButtonStyle.secondary)
        async def flee_button(self, interaction: Interaction, button: ui.Button):
            """Attempt to flee from battle."""
            if self.battle_over:
                return
                
            # 60% chance to succeed, increased by player speed compared to enemy
            speed_factor = self.player_card["adjusted_speed"] / max(1, self.enemy["speed"])
            flee_chance = min(90, 60 + (speed_factor - 1) * 20)
            
            if random.random() * 100 < flee_chance:
                # Successful flee
                self.battle_over = True
                self.update_button_states()
                
                # Update message
                await self.update_battle_message("🏃 You successfully fled from battle!")
                
                # Remove player from active battles
                self.battle_cog.active_battles.pop(self.ctx.author.id, None)
            else:
                # Failed flee attempt
                failed_message = "❌ Failed to flee! Enemy attacks!"
                
                # Enemy gets a free attack for failed flee attempt
                await self.enemy_turn()
                
                # Update battle status
                await self.update_battle_message(failed_message)
            
        async def enemy_turn(self):
            """Execute the enemy's turn."""
            if self.battle_over or self.enemy_hp <= 0:
                return
                
            # Decide between basic attack and skill
            use_skill = False
            if self.enemy_mp >= self.enemy["skill_cost"] and random.random() < 0.4:  # 40% chance to use skill if MP available
                use_skill = True
                
            # Calculate damage
            damage, is_critical, is_effective = self.battle_cog.calculate_damage(
                self.enemy, self.player_card, is_skill=use_skill
            )
            
            # Apply damage to player
            self.player_hp = max(0, self.player_hp - damage)
            
            # Consume MP if skill used
            if use_skill:
                self.enemy_mp -= self.enemy["skill_cost"]
                
            # Format result
            result = self.battle_cog.format_move_result(
                self.enemy["name"],
                self.ctx.author.display_name,
                damage,
                self.player_hp,
                self.player_max_hp,
                is_critical,
                is_effective,
                is_skill=use_skill,
                skill_name=self.enemy["skill"] if use_skill else None
            )
            
            # Add to battle log
            self.battle_log.append(result)
            
            # Check if player defeated
            if self.player_hp <= 0:
                await self.end_battle("enemy")
                
        async def update_battle_message(self, message):
            """Update the battle message with current state."""
            # Format battle status
            status = self.battle_cog.format_battle_status(
                self.ctx.author.display_name,
                self.player_card,
                self.player_hp,
                self.player_max_hp,
                self.player_mp,
                self.player_max_mp,
                self.enemy["name"],
                self.enemy_hp,
                self.enemy_max_hp,
                self.enemy_mp,
                self.enemy_max_mp
            )
            
            # Get the most recent battle log entries (last 2)
            recent_log = "\n\n".join(self.battle_log[-2:]) if self.battle_log else ""
            
            # Create embed
            embed = discord.Embed(
                title=f"⚔️ Battle: {self.ctx.author.display_name} vs {self.enemy['name']}",
                description=status,
                color=discord.Color.red()
            )
            
            if recent_log:
                embed.add_field(name="🔥 Battle Log", value=recent_log, inline=False)
                
            if message:
                embed.add_field(name="📢 Message", value=message, inline=False)
                
            # Add image if available
            if self.enemy.get("image_url"):
                embed.set_thumbnail(url=self.enemy["image_url"])
                
            # Update buttons based on state
            self.update_button_states()
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        async def end_battle(self, victor):
            """End the battle and handle rewards."""
            self.battle_over = True
            self.update_button_states()
            
            # Remove from active battles
            self.battle_cog.active_battles.pop(self.ctx.author.id, None)
            
            if victor == "player":
                # Player won
                rewards = await self.battle_cog.add_battle_reward(
                    self.ctx.author.id, 
                    self.player_card,
                    self.enemy,
                    self.turn_count
                )
                
                # Format rewards message
                reward_message = (
                    f"🎉 **Victory!** You defeated {self.enemy['name']}!\n\n"
                    f"🏆 **Rewards:**\n"
                    f"• +{rewards['xp']} XP\n"
                    f"• +{rewards['gold']} Gold\n"
                    f"• Your {self.player_card['name']} gained {int(rewards['xp'] * 0.8)} XP"
                )
                
                if rewards["leveled_up"]:
                    reward_message += f"\n\n🌟 **Level Up!** You are now level {rewards['new_level']}!"
                    
                if rewards["card_leveled"]:
                    reward_message += f"\n\n🌟 **Card Level Up!** Your {self.player_card['name']} is now level {rewards['card_new_level']}!"
                
                # Final battle stats
                stats = (
                    f"⏱️ Battle completed in {self.turn_count} turns.\n"
                    f"📊 Remaining HP: {self.player_hp}/{self.player_max_hp}"
                )
                
                # Update database with win
                cursor = self.battle_cog.db.conn.cursor()
                cursor.execute("""
                    UPDATE api_players
                    SET wins = wins + 1
                    WHERE discord_id = ?
                """, (self.ctx.author.id,))
                self.battle_cog.db.conn.commit()
                cursor.close()
                
                final_message = f"{reward_message}\n\n{stats}"
                
            else:
                # Player lost
                defeat_message = (
                    f"💀 **Defeat!** You were defeated by {self.enemy['name']}.\n\n"
                    f"Better luck next time!"
                )
                
                # Update database with loss
                cursor = self.battle_cog.db.conn.cursor()
                cursor.execute("""
                    UPDATE api_players
                    SET losses = losses + 1
                    WHERE discord_id = ?
                """, (self.ctx.author.id,))
                self.battle_cog.db.conn.commit()
                cursor.close()
                
                final_message = defeat_message
                
            # Create final status
            status = self.battle_cog.format_battle_status(
                self.ctx.author.display_name,
                self.player_card,
                self.player_hp,
                self.player_max_hp,
                self.player_mp,
                self.player_max_mp,
                self.enemy["name"],
                self.enemy_hp,
                self.enemy_max_hp,
                self.enemy_mp,
                self.enemy_max_mp
            )
            
            # Create final embed
            embed = discord.Embed(
                title=f"⚔️ Battle Complete: {self.ctx.author.display_name} vs {self.enemy['name']}",
                description=status,
                color=discord.Color.gold() if victor == "player" else discord.Color.dark_red()
            )
            
            embed.add_field(name="📢 Results", value=final_message, inline=False)
            
            # Add image if available
            if self.enemy.get("image_url"):
                embed.set_thumbnail(url=self.enemy["image_url"])
                
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def battle_command(self, ctx):
        """⚔️ Battle against a random enemy to earn rewards"""
        # Check if player exists
        player_data = self.get_player_data(ctx.author.id)
        if not player_data:
            return await ctx.send("❌ You don't have a profile yet! Use `!start` to create one.")
            
        # Check if player has equipped card
        player_card = self.get_player_card(ctx.author.id)
        if not player_card:
            return await ctx.send("❌ You don't have a card equipped! Use `!equip` to equip a card.")
            
        # Check if player is already in a battle
        if ctx.author.id in self.active_battles:
            return await ctx.send("❌ You're already in a battle! Finish it first.")
            
        # Check if player has stamina
        if player_data["stamina"] < 10:
            return await ctx.send(f"❌ Not enough stamina! You need 10 stamina to battle. (You have {player_data['stamina']}/{player_data['max_stamina']})")
            
        # Deduct stamina
        self.update_player_stamina(ctx.author.id, player_data["stamina"] - 10)
        
        # Generate enemy based on player level
        enemy = self.generate_enemy(player_data["level"])
        
        # Mark player as in battle
        self.active_battles[ctx.author.id] = True
        
        # Format battle initiation
        embed = discord.Embed(
            title=f"⚔️ Battle: {ctx.author.display_name} vs {enemy['name']}",
            description=f"Prepare for battle! You're facing a level {enemy['level']} {enemy['name']}.",
            color=discord.Color.red()
        )
        
        # Add stats
        embed.add_field(
            name="Your Card",
            value=(
                f"**{player_card['name']}** (Level {player_card['level']})\n"
                f"Element: {player_card['element']}\n"
                f"Skill: {player_card['skill']}\n"
                f"ATK: {player_card['adjusted_attack']} | DEF: {player_card['adjusted_defense']} | SPD: {player_card['adjusted_speed']}"
            ),
            inline=True
        )
        
        embed.add_field(
            name="Enemy",
            value=(
                f"**{enemy['name']}** (Level {enemy['level']})\n"
                f"Element: {enemy['element']}\n"
                f"Skill: {enemy['skill']}\n"
                f"ATK: {enemy['attack']} | DEF: {enemy['defense']} | SPD: {enemy['speed']}"
            ),
            inline=True
        )
        
        # Create battle view
        view = self.BattleView(self, ctx, player_data, player_card, enemy)
        
        # Send battle message
        battle_message = await ctx.send(embed=embed, view=view)
        
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(BattleSystem(bot))