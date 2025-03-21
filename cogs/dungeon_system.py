"""
Dungeon system for the anime card game.
Players can explore themed dungeons with multiple floors,
battle enemies, and earn rewards including card drops.
"""

import discord
from discord.ext import commands
import random
import asyncio
import time
import math
from discord import ui, ButtonStyle, Interaction

class DungeonSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.active_dungeons = {}
        
    def get_player_data(self, user_id):
        """Get player's battle-relevant data."""
        self.cursor.execute("""
            SELECT id, level, stamina, mp, max_mp
            FROM api_players
            WHERE discord_id = ?
        """, (user_id,))
        
        player = self.cursor.fetchone()
        if not player:
            return None
            
        player_id, level, stamina, mp, max_mp = player
        
        return {
            "id": player_id,
            "level": level,
            "stamina": stamina,
            "mp": mp,
            "max_mp": max_mp
        }
    
    def get_player_card(self, user_id):
        """Get the player's equipped card with detailed stats."""
        self.cursor.execute("""
            SELECT uc.id, c.name, uc.level, c.rarity, 
                   c.attack, c.defense, c.speed, c.element, 
                   c.skill, c.skill_description, c.image_url, c.mp_cost,
                   uc.xp, uc.evo_stage
            FROM api_user_cards uc
            JOIN api_cards c ON uc.card_id = c.id
            WHERE uc.player_id = (SELECT id FROM api_players WHERE discord_id = ?)
            AND uc.equipped = 1
        """, (user_id,))
        
        card = self.cursor.fetchone()
        if not card:
            return None
            
        # Extract card details
        card_id, name, level, rarity, base_attack, base_defense, base_speed, element, skill, skill_desc, image_url, mp_cost, xp, evo_stage = card
        
        # Calculate stats based on level and rarity
        rarity_multiplier = {"Common": 1.0, "Uncommon": 1.2, "Rare": 1.5, "Epic": 2.0, "Legendary": 2.5}
        multiplier = rarity_multiplier.get(rarity, 1.0)
        
        # Stats increase with level
        level_bonus = (level - 1) * 0.1 * multiplier
        
        # Evolution stage boosts stats
        evo_bonus = (evo_stage - 1) * 0.2
        
        attack = int(base_attack * (1 + level_bonus + evo_bonus))
        defense = int(base_defense * (1 + level_bonus + evo_bonus))
        speed = int(base_speed * (1 + level_bonus + evo_bonus))
        
        # Construct card object
        card_obj = {
            "id": card_id,
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
            "xp": xp,
            "evo_stage": evo_stage
        }
        
        return card_obj
    
    def get_available_dungeons(self, player_level):
        """Get dungeons available to the player based on level."""
        self.cursor.execute("""
            SELECT id, name, description, anime_series, min_level, floor_count, image_url
            FROM dungeons
            WHERE min_level <= ?
            ORDER BY min_level ASC
        """, (player_level,))
        
        dungeons = self.cursor.fetchall()
        return dungeons
    
    def get_dungeon_details(self, dungeon_id):
        """Get detailed information about a dungeon."""
        self.cursor.execute("""
            SELECT id, name, description, anime_series, min_level, floor_count, image_url
            FROM dungeons
            WHERE id = ?
        """, (dungeon_id,))
        
        dungeon = self.cursor.fetchone()
        if not dungeon:
            return None
            
        dungeon_id, name, description, anime_series, min_level, floor_count, image_url = dungeon
        
        return {
            "id": dungeon_id,
            "name": name,
            "description": description,
            "anime_series": anime_series,
            "min_level": min_level,
            "floor_count": floor_count,
            "image_url": image_url
        }
    
    def get_dungeon_floor(self, dungeon_id, floor_number):
        """Get information about a specific dungeon floor."""
        self.cursor.execute("""
            SELECT id, floor_number, boss_id, description, min_level
            FROM dungeon_floors
            WHERE dungeon_id = ? AND floor_number = ?
        """, (dungeon_id, floor_number))
        
        floor = self.cursor.fetchone()
        
        # If floor doesn't exist in database, generate it
        if not floor:
            # Get dungeon details
            dungeon = self.get_dungeon_details(dungeon_id)
            if not dungeon:
                return None
                
            # Generate floor data
            min_level = dungeon["min_level"] + floor_number - 1
            is_boss_floor = (floor_number % 4 == 0)  # Boss every 4 floors
            boss_id = None
            description = f"Floor {floor_number} of {dungeon['name']}"
            
            if is_boss_floor:
                # Get a boss card from this anime series
                self.cursor.execute("""
                    SELECT id FROM api_cards
                    WHERE anime_series = ? AND (rarity = 'Epic' OR rarity = 'Legendary')
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (dungeon["anime_series"],))
                
                boss_result = self.cursor.fetchone()
                if boss_result:
                    boss_id = boss_result[0]
                description = f"Boss Floor {floor_number} of {dungeon['name']}"
            
            # Insert floor into database
            self.cursor.execute("""
                INSERT INTO dungeon_floors (dungeon_id, floor_number, boss_id, description, min_level)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id, floor_number, boss_id, description, min_level
            """, (dungeon_id, floor_number, boss_id, description, min_level))
            
            self.db.conn.commit()
            floor = self.cursor.fetchone()
            
        if not floor:
            return None
            
        floor_id, floor_number, boss_id, description, min_level = floor
        
        return {
            "id": floor_id,
            "floor_number": floor_number,
            "boss_id": boss_id,
            "description": description,
            "min_level": min_level,
            "is_boss": boss_id is not None
        }
    
    def has_completed_floor(self, player_id, dungeon_id, floor_number):
        """Check if player has completed this floor."""
        self.cursor.execute("""
            SELECT id FROM completed_floors
            WHERE player_id = ? AND dungeon_id = ? AND floor_number = ?
        """, (player_id, dungeon_id, floor_number))
        
        return self.cursor.fetchone() is not None
    
    def mark_floor_completed(self, player_id, dungeon_id, floor_number):
        """Mark a floor as completed by player."""
        self.cursor.execute("""
            INSERT INTO completed_floors (player_id, dungeon_id, floor_number)
            VALUES (?, ?, ?)
        """, (player_id, dungeon_id, floor_number))
        
        self.db.conn.commit()
    
    def get_player_highest_floor(self, player_id, dungeon_id):
        """Get the highest floor completed by player in this dungeon."""
        self.cursor.execute("""
            SELECT MAX(floor_number) FROM completed_floors
            WHERE player_id = ? AND dungeon_id = ?
        """, (player_id, dungeon_id))
        
        result = self.cursor.fetchone()
        if not result or result[0] is None:
            return 0
            
        return result[0]
    
    def update_player_stamina(self, user_id, stamina):
        """Update player's stamina."""
        self.cursor.execute("""
            UPDATE api_players
            SET stamina = ?
            WHERE discord_id = ?
        """, (stamina, user_id))
        self.db.conn.commit()
    
    def generate_floor_enemies(self, dungeon_id, floor_number, player_level):
        """Generate enemies for this floor."""
        # Get dungeon details
        dungeon = self.get_dungeon_details(dungeon_id)
        if not dungeon:
            return []
            
        # Get floor details
        floor = self.get_dungeon_floor(dungeon_id, floor_number)
        if not floor:
            return []
            
        # Determine number of enemies (1-3 normal enemies or 1 boss)
        is_boss_floor = floor["is_boss"]
        
        if is_boss_floor:
            # Boss floor has one powerful boss
            enemy_count = 1
        else:
            # Normal floor has 1-3 enemies
            enemy_count = random.randint(1, 3)
        
        enemies = []
        
        # Generate enemies
        battle_cog = self.bot.get_cog("BattleSystem")
        if not battle_cog:
            return []
            
        for i in range(enemy_count):
            # Boss or normal enemy
            enemy = battle_cog.generate_enemy(
                player_level,
                dungeon_id=dungeon_id,
                floor=floor_number,
                is_boss=is_boss_floor and i == 0  # First enemy is boss on boss floors
            )
            
            enemies.append(enemy)
        
        return enemies
    
    class DungeonFloorView(ui.View):
        def __init__(self, dungeon_cog, ctx, dungeon_data, floor_number, player_data):
            super().__init__(timeout=180)
            self.dungeon_cog = dungeon_cog
            self.ctx = ctx
            self.dungeon_data = dungeon_data
            self.floor_number = floor_number
            self.player_data = player_data
            self.enemies = []
            self.current_enemy_index = 0
            self.battle_active = False
            self.battle_log = []
            
            # Generate enemies for this floor
            self.enemies = dungeon_cog.generate_floor_enemies(
                dungeon_data["id"],
                floor_number,
                player_data["level"]
            )
            
            # Get player's card
            self.player_card = dungeon_cog.get_player_card(ctx.author.id)
            
            # Battle stats
            self.player_hp = self.player_card["level"] * 50
            self.player_max_hp = self.player_hp
            self.player_mp = player_data["mp"]
            self.player_max_mp = player_data["max_mp"]
            
            # Configure buttons based on floor state
            self.update_buttons()
        
        async def interaction_check(self, interaction):
            """Check if the interaction is from the dungeon owner."""
            return interaction.user.id == self.ctx.author.id
        
        def update_buttons(self):
            """Update button states based on dungeon state."""
            # Enable/disable battle button
            battle_button = [item for item in self.children if item.custom_id == "battle"]
            if battle_button:
                battle_button[0].disabled = self.battle_active or len(self.enemies) == 0
            
            # Enable/disable next floor button
            next_floor_button = [item for item in self.children if item.custom_id == "next_floor"]
            if next_floor_button:
                # Only enable if all enemies defeated
                next_floor_button[0].disabled = len(self.enemies) > 0
        
        @ui.button(label="Battle", style=ButtonStyle.danger, emoji="⚔️", custom_id="battle")
        async def battle_button(self, interaction: Interaction, button: ui.Button):
            """Start a battle with the next enemy."""
            if self.battle_active or len(self.enemies) == 0:
                return
                
            await interaction.response.defer()
            
            # Get the next enemy
            enemy = self.enemies[self.current_enemy_index]
            
            # Start battle
            self.battle_active = True
            
            # Create battle embed
            embed = discord.Embed(
                title=f"Floor {self.floor_number} Battle",
                description=f"You are battling {enemy['name']}!",
                color=discord.Color.red()
            )
            
            # Add battle stats
            battle_stats = self.dungeon_cog.bot.get_cog("BattleSystem").format_battle_status(
                self.ctx.author.display_name,
                self.player_card,
                self.player_hp,
                self.player_max_hp,
                self.player_mp,
                self.player_max_mp,
                enemy["name"],
                enemy["hp"],
                enemy["max_hp"],
                enemy["mp"],
                enemy["max_mp"]
            )
            
            embed.add_field(
                name="Battle Status",
                value=battle_stats,
                inline=False
            )
            
            # Create battle view
            battle_view = self.DungeonBattleView(
                self.dungeon_cog,
                self.ctx,
                self.player_card,
                enemy,
                self.player_hp,
                self.player_max_hp,
                self.player_mp,
                self.player_max_mp,
                self
            )
            
            # Send battle message
            battle_message = await self.ctx.send(embed=embed, view=battle_view)
            
            # Update buttons
            self.update_buttons()
            await interaction.message.edit(view=self)
        
        @ui.button(label="Next Floor", style=ButtonStyle.success, emoji="⬆️", custom_id="next_floor")
        async def next_floor_button(self, interaction: Interaction, button: ui.Button):
            """Proceed to the next floor."""
            if len(self.enemies) > 0:
                await interaction.response.send_message(
                    "You must defeat all enemies on this floor before proceeding!",
                    ephemeral=True
                )
                return
                
            await interaction.response.defer()
            
            # Mark current floor as completed
            player_id = self.player_data["id"]
            dungeon_id = self.dungeon_data["id"]
            self.dungeon_cog.mark_floor_completed(player_id, dungeon_id, self.floor_number)
            
            # Check if this was the final floor
            if self.floor_number >= self.dungeon_data["floor_count"]:
                embed = discord.Embed(
                    title="Dungeon Completed!",
                    description=f"Congratulations! You have completed all floors of {self.dungeon_data['name']}!",
                    color=discord.Color.gold()
                )
                
                embed.add_field(
                    name="Reward",
                    value="You earned a special achievement for completing this dungeon!",
                    inline=False
                )
                
                await self.ctx.send(embed=embed)
                
                # Close the view
                self.stop()
                await interaction.message.edit(view=None)
                return
            
            # Start the next floor
            next_floor = self.floor_number + 1
            new_floor_view = await self.dungeon_cog.start_dungeon_floor(
                self.ctx,
                self.dungeon_data["id"],
                next_floor
            )
            
            # Stop this view
            self.stop()
            await interaction.message.edit(view=None)
        
        @ui.button(label="Leave Dungeon", style=ButtonStyle.secondary, emoji="🚪", custom_id="leave")
        async def leave_button(self, interaction: Interaction, button: ui.Button):
            """Leave the dungeon."""
            await interaction.response.defer()
            
            embed = discord.Embed(
                title="Leaving Dungeon",
                description=f"You have left {self.dungeon_data['name']} from floor {self.floor_number}.",
                color=discord.Color.light_grey()
            )
            
            await self.ctx.send(embed=embed)
            
            # Stop the view
            self.stop()
            await interaction.message.edit(view=None)
        
        def enemy_defeated(self, enemy_index):
            """Mark an enemy as defeated."""
            # Remove enemy from list
            if 0 <= enemy_index < len(self.enemies):
                del self.enemies[enemy_index]
                
                # Update current enemy index if needed
                if self.current_enemy_index >= len(self.enemies):
                    self.current_enemy_index = 0
                    
                # Battle is no longer active
                self.battle_active = False
                
                # Update buttons
                self.update_buttons()
                
                return True
                
            return False
            
    
    class DungeonBattleView(ui.View):
        def __init__(self, dungeon_cog, ctx, player_card, enemy, player_hp, player_max_hp, player_mp, player_max_mp, parent_view):
            super().__init__(timeout=60)
            self.dungeon_cog = dungeon_cog
            self.ctx = ctx
            self.player_card = player_card
            self.enemy = enemy
            self.player_hp = player_hp
            self.player_max_hp = player_max_hp
            self.player_mp = player_mp
            self.player_max_mp = player_max_mp
            self.parent_view = parent_view
            
            self.turn = 0
            self.last_move_description = ""
            self.battle_log = []
            self.battle_ended = False
            
            # Update button states
            self.update_button_states()
        
        async def interaction_check(self, interaction):
            """Check if the interaction is from the battle owner."""
            return interaction.user.id == self.ctx.author.id
        
        def update_button_states(self):
            """Update button states based on battle state."""
            # Disable buttons if battle ended
            if self.battle_ended:
                for item in self.children:
                    item.disabled = True
                return
                
            # Disable skill button if not enough MP
            skill_button = [item for item in self.children if item.custom_id == "use_skill"]
            if skill_button:
                skill_button[0].disabled = self.player_mp < self.player_card["mp_cost"]
        
        @ui.button(label="Attack", style=ButtonStyle.primary, emoji="⚔️", custom_id="attack")
        async def attack_button(self, interaction: Interaction, button: ui.Button):
            """Execute a basic attack."""
            if self.battle_ended:
                return
                
            await interaction.response.defer()
            
            # Player attacks
            battle_cog = self.dungeon_cog.bot.get_cog("BattleSystem")
            damage, is_critical, is_effective = battle_cog.calculate_damage(
                self.player_card, self.enemy, is_skill=False
            )
            
            # Apply damage
            self.enemy["hp"] = max(0, self.enemy["hp"] - damage)
            
            # Update battle log
            player_name = self.ctx.author.display_name
            move_result = battle_cog.format_move_result(
                f"{player_name}'s {self.player_card['name']}", 
                self.enemy["name"],
                damage, 
                self.enemy["hp"],
                self.enemy["max_hp"],
                is_critical,
                is_effective
            )
            
            self.battle_log.append(move_result)
            self.last_move_description = move_result
            
            # Check if enemy defeated
            if self.enemy["hp"] <= 0:
                await self.end_battle(victor="player")
                return
                
            # Enemy turn
            await self.enemy_turn()
            
            # Increment turn counter
            self.turn += 1
            
            # Regenerate some MP each turn
            mp_regen = 5
            self.player_mp = min(self.player_max_mp, self.player_mp + mp_regen)
            
            # Update button states
            self.update_button_states()
            
            # Update the battle message
            await self.update_battle_message(interaction.message)
        
        @ui.button(label="Use Skill", style=ButtonStyle.danger, emoji="✨", custom_id="use_skill")
        async def skill_button(self, interaction: Interaction, button: ui.Button):
            """Use the card's special skill."""
            if self.battle_ended:
                return
                
            # Check if enough MP
            if self.player_mp < self.player_card["mp_cost"]:
                await interaction.response.send_message(
                    f"Not enough MP! You need {self.player_card['mp_cost']} MP to use {self.player_card['skill']}.",
                    ephemeral=True
                )
                return
                
            await interaction.response.defer()
            
            # Use MP
            self.player_mp -= self.player_card["mp_cost"]
            
            # Player uses skill
            battle_cog = self.dungeon_cog.bot.get_cog("BattleSystem")
            damage, is_critical, is_effective = battle_cog.calculate_damage(
                self.player_card, self.enemy, is_skill=True
            )
            
            # Skills do more damage
            damage = int(damage * 1.5)
            
            # Apply damage
            self.enemy["hp"] = max(0, self.enemy["hp"] - damage)
            
            # Update battle log
            player_name = self.ctx.author.display_name
            move_result = battle_cog.format_move_result(
                f"{player_name}'s {self.player_card['name']}", 
                self.enemy["name"],
                damage, 
                self.enemy["hp"],
                self.enemy["max_hp"],
                is_critical,
                is_effective,
                is_skill=True,
                skill_name=self.player_card['skill']
            )
            
            self.battle_log.append(move_result)
            self.last_move_description = move_result
            
            # Check if enemy defeated
            if self.enemy["hp"] <= 0:
                await self.end_battle(victor="player")
                return
                
            # Enemy turn
            await self.enemy_turn()
            
            # Increment turn counter
            self.turn += 1
            
            # Regenerate some MP each turn
            mp_regen = 5
            self.player_mp = min(self.player_max_mp, self.player_mp + mp_regen)
            
            # Update button states
            self.update_button_states()
            
            # Update the battle message
            await self.update_battle_message(interaction.message)
        
        @ui.button(label="Flee", style=ButtonStyle.secondary, emoji="🏃", custom_id="flee")
        async def flee_button(self, interaction: Interaction, button: ui.Button):
            """Attempt to flee from battle."""
            if self.battle_ended:
                return
                
            await interaction.response.defer()
            
            # 70% chance to flee successfully
            if random.randint(1, 100) <= 70:
                self.battle_log.append(f"**{self.ctx.author.display_name} fled from the battle!**")
                self.last_move_description = f"**{self.ctx.author.display_name} fled from the battle!**"
                await self.end_battle(victor="flee")
            else:
                self.battle_log.append(f"**{self.ctx.author.display_name} tried to flee but couldn't escape!**")
                self.last_move_description = f"**{self.ctx.author.display_name} tried to flee but couldn't escape!**"
                
                # Enemy gets a free attack if flee fails
                await self.enemy_turn()
                
                # Increment turn counter
                self.turn += 1
                
                # Regenerate some MP each turn
                mp_regen = 5
                self.player_mp = min(self.player_max_mp, self.player_mp + mp_regen)
            
            # Update button states
            self.update_button_states()
            
            # Update the battle message
            await self.update_battle_message(interaction.message)
        
        async def enemy_turn(self):
            """Execute the enemy's turn."""
            battle_cog = self.dungeon_cog.bot.get_cog("BattleSystem")
            
            # Decide action: 70% normal attack, 30% skill if enough MP
            use_skill = random.randint(1, 100) <= 30 and self.enemy["mp"] >= self.enemy["mp_cost"]
            
            if use_skill:
                # Use MP
                self.enemy["mp"] -= self.enemy["mp_cost"]
                
                # Enemy uses skill
                damage, is_critical, is_effective = battle_cog.calculate_damage(
                    self.enemy, self.player_card, is_skill=True
                )
                
                # Skills do more damage
                damage = int(damage * 1.5)
            else:
                # Regular attack
                damage, is_critical, is_effective = battle_cog.calculate_damage(
                    self.enemy, self.player_card, is_skill=False
                )
            
            # Apply damage
            self.player_hp = max(0, self.player_hp - damage)
            
            # Update battle log
            player_name = self.ctx.author.display_name
            move_result = battle_cog.format_move_result(
                self.enemy["name"],
                f"{player_name}'s {self.player_card['name']}",
                damage, 
                self.player_hp,
                self.player_max_hp,
                is_critical,
                is_effective,
                is_skill=use_skill,
                skill_name=self.enemy['skill'] if use_skill else None
            )
            
            self.battle_log.append(move_result)
            self.last_move_description = move_result
            
            # Regenerate some enemy MP
            mp_regen = 5
            self.enemy["mp"] = min(self.enemy["max_mp"], self.enemy["mp"] + mp_regen)
            
            # Check if player defeated
            if self.player_hp <= 0:
                await self.end_battle(victor="enemy")
        
        async def update_battle_message(self, message):
            """Update the battle message with current state."""
            battle_cog = self.dungeon_cog.bot.get_cog("BattleSystem")
            
            # Create embed
            embed = discord.Embed(
                title=f"Floor {self.parent_view.floor_number} Battle: {self.ctx.author.display_name} vs {self.enemy['name']}",
                description=battle_cog.format_battle_status(
                    self.ctx.author.display_name,
                    self.player_card,
                    self.player_hp,
                    self.player_max_hp,
                    self.player_mp,
                    self.player_max_mp,
                    self.enemy["name"],
                    self.enemy["hp"],
                    self.enemy["max_hp"],
                    self.enemy["mp"],
                    self.enemy["max_mp"]
                ),
                color=discord.Color.blue()
            )
            
            # Add last move
            if self.last_move_description:
                embed.add_field(
                    name="Last Action",
                    value=self.last_move_description,
                    inline=False
                )
            
            # Add turn counter
            embed.set_footer(text=f"Turn: {self.turn}")
            
            # Update message
            await message.edit(embed=embed, view=self)
        
        async def end_battle(self, victor):
            """End the battle and handle rewards."""
            self.battle_ended = True
            
            if victor == "player":
                # Player won
                battle_cog = self.dungeon_cog.bot.get_cog("BattleSystem")
                reward = await battle_cog.add_battle_reward(
                    self.ctx.author.id, 
                    self.player_card, 
                    self.enemy,
                    self.turn
                )
                
                # Update parent view (enemy defeated)
                self.parent_view.enemy_defeated(self.parent_view.current_enemy_index)
                
                # Update parent view with player's current HP/MP
                self.parent_view.player_hp = self.player_hp
                self.parent_view.player_mp = self.player_mp
                
                # Update player's MP in database
                self.dungeon_cog.bot.get_cog("BattleSystem").update_player_mp(self.ctx.author.id, self.player_mp)
                
                # Create victory embed
                embed = discord.Embed(
                    title=f"Victory! {self.ctx.author.display_name} defeated {self.enemy['name']}",
                    description=f"You won the battle in {self.turn} turns!",
                    color=discord.Color.green()
                )
                
                # Add rewards
                reward_text = f"🪙 **Gold:** {reward['gold']}\n"
                reward_text += f"✨ **Player EXP:** {reward['player_exp']}\n"
                reward_text += f"📈 **Card EXP:** {reward['card_exp']}"
                
                embed.add_field(
                    name="Rewards",
                    value=reward_text,
                    inline=False
                )
                
                # Add level ups
                if reward['player_level_up']:
                    embed.add_field(
                        name="Level Up!",
                        value=f"Your trainer level increased to {reward['player_level_up']['new_level']}!",
                        inline=False
                    )
                    
                if reward['card_level_up']:
                    embed.add_field(
                        name="Card Level Up!",
                        value=f"Your {self.player_card['name']} leveled up to {reward['card_level_up']['new_level']}!",
                        inline=False
                    )
                
                # Add drops
                if reward['card_drop']:
                    embed.add_field(
                        name="Card Drop!",
                        value=f"You obtained a **{reward['card_drop']['rarity']}** {reward['card_drop']['name']}!",
                        inline=False
                    )
                    
                if reward['material_drop']:
                    embed.add_field(
                        name="Material Drop!",
                        value=f"You obtained **{reward['material_drop']['quantity']}x {reward['material_drop']['name']}**!",
                        inline=False
                    )
                
                # Update dungeon status
                embed.add_field(
                    name="Dungeon Status",
                    value=f"Enemies remaining on floor {self.parent_view.floor_number}: {len(self.parent_view.enemies)}",
                    inline=False
                )
                
                # Send results
                await self.ctx.send(embed=embed)
                
                # Update parent view
                await self.parent_view.update_buttons()
                
            elif victor == "enemy":
                # Player lost
                # Update player's MP in database
                self.dungeon_cog.bot.get_cog("BattleSystem").update_player_mp(self.ctx.author.id, self.player_mp)
                
                # Create defeat embed
                embed = discord.Embed(
                    title=f"Defeat! {self.ctx.author.display_name} was defeated by {self.enemy['name']}",
                    description=f"You were defeated after {self.turn} turns!",
                    color=discord.Color.red()
                )
                
                # Add dungeon failure
                embed.add_field(
                    name="Dungeon Failed",
                    value="You have been expelled from the dungeon. Try again with a stronger card or better strategy!",
                    inline=False
                )
                
                # Send results
                await self.ctx.send(embed=embed)
                
                # Stop parent view
                await self.parent_view.leave_button.callback(None, self.parent_view.leave_button)
                
            elif victor == "flee":
                # Player fled
                # Update player's MP in database
                self.dungeon_cog.bot.get_cog("BattleSystem").update_player_mp(self.ctx.author.id, self.player_mp)
                
                # Create flee embed
                embed = discord.Embed(
                    title=f"{self.ctx.author.display_name} fled from battle!",
                    description="You escaped safely.",
                    color=discord.Color.light_grey()
                )
                
                # Send results
                await self.ctx.send(embed=embed)
                
                # Update parent view (enemy not defeated)
                self.parent_view.battle_active = False
                await self.parent_view.update_buttons()
            
            # Update button states
            self.update_button_states()
        
    async def start_dungeon_floor(self, ctx, dungeon_id, floor_number):
        """Start a specific floor of a dungeon."""
        # Get dungeon details
        dungeon_data = self.get_dungeon_details(dungeon_id)
        if not dungeon_data:
            await ctx.send(f"{ctx.author.mention}, that dungeon doesn't exist!")
            return None
        
        # Get floor details
        floor = self.get_dungeon_floor(dungeon_id, floor_number)
        if not floor:
            await ctx.send(f"{ctx.author.mention}, that floor doesn't exist!")
            return None
        
        # Get player data
        player_data = self.get_player_data(ctx.author.id)
        if not player_data:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return None
        
        # Check player level against floor requirement
        if player_data["level"] < floor["min_level"]:
            await ctx.send(
                f"{ctx.author.mention}, you need to be level {floor['min_level']} to enter this floor! "
                f"You are only level {player_data['level']}."
            )
            return None
        
        # Check player's equipped card
        player_card = self.get_player_card(ctx.author.id)
        if not player_card:
            await ctx.send(f"{ctx.author.mention}, you need to equip a card first! Use `!equip <card_id>`")
            return None
        
        # Create floor embed
        embed = discord.Embed(
            title=f"{dungeon_data['name']} - Floor {floor_number}",
            description=floor["description"],
            color=discord.Color.blue()
        )
        
        # Add floor info
        embed.add_field(
            name="Floor Type",
            value="Boss Floor" if floor["is_boss"] else "Normal Floor",
            inline=True
        )
        
        embed.add_field(
            name="Recommended Level",
            value=str(floor["min_level"]),
            inline=True
        )
        
        embed.add_field(
            name="Player Level",
            value=str(player_data["level"]),
            inline=True
        )
        
        # Add equipped card info
        embed.add_field(
            name="Equipped Card",
            value=f"{player_card['name']} (Lv.{player_card['level']} {player_card['rarity']})",
            inline=False
        )
        
        # Create dungeon floor view
        view = self.DungeonFloorView(self, ctx, dungeon_data, floor_number, player_data)
        
        # Add enemy info
        enemy_info = "Enemies on this floor:\n"
        for i, enemy in enumerate(view.enemies, 1):
            enemy_info += f"{i}. Lv.{enemy['level']} {enemy['rarity']} {enemy['name']}\n"
        
        embed.add_field(
            name="Enemies",
            value=enemy_info,
            inline=False
        )
        
        # Add instructions
        embed.add_field(
            name="Instructions",
            value="Use the buttons below to navigate the dungeon floor.",
            inline=False
        )
        
        # Add dungeon image if available
        if dungeon_data["image_url"]:
            embed.set_image(url=dungeon_data["image_url"])
        
        # Send message
        await ctx.send(embed=embed, view=view)
        return view
    
    @commands.command(name="dungeons", aliases=["dg"])
    async def dungeons_command(self, ctx):
        """🏰 View available dungeons to explore"""
        # Get player data
        player_data = self.get_player_data(ctx.author.id)
        if not player_data:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
        
        # Get available dungeons
        dungeons = self.get_available_dungeons(player_data["level"])
        
        if not dungeons:
            await ctx.send(f"{ctx.author.mention}, there are no dungeons available for your level!")
            return
        
        # Create embeds for pagination
        embeds = []
        
        # Group dungeons (5 per page)
        chunks = [dungeons[i:i+5] for i in range(0, len(dungeons), 5)]
        
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title="Available Dungeons",
                description=f"Select a dungeon to explore! Your level: {player_data['level']}",
                color=discord.Color.blue()
            )
            
            for dungeon_id, name, description, anime_series, min_level, floor_count, image_url in chunk:
                # Get player's highest floor
                highest_floor = self.get_player_highest_floor(player_data["id"], dungeon_id)
                
                # Format progress
                progress = f"Progress: {highest_floor}/{floor_count} floors"
                if highest_floor == floor_count:
                    progress += " (Completed)"
                elif highest_floor == 0:
                    progress += " (Not started)"
                
                embed.add_field(
                    name=f"{name} (Lv.{min_level}+)",
                    value=f"{description}\nAnime: {anime_series}\n{progress}\nUse `!dungeon {dungeon_id}` to enter",
                    inline=False
                )
            
            embed.set_footer(text=f"Page {i+1}/{len(chunks)} · !dungeon <id> to enter")
            embeds.append(embed)
        
        # Use pagination if available
        pagination_cog = self.bot.get_cog("Pagination")
        if pagination_cog and embeds:
            await pagination_cog.paginate(ctx, embeds)
        elif embeds:
            await ctx.send(embed=embeds[0])
    
    @commands.command(name="dungeon", aliases=["dun"])
    async def dungeon_command(self, ctx, dungeon_id: int = None, floor: int = None):
        """🏰 Enter a specific dungeon"""
        # Validate parameters
        if dungeon_id is None:
            await ctx.send(
                f"{ctx.author.mention}, please specify a dungeon ID. Use `!dungeons` to see available dungeons."
            )
            return
        
        # Get player data
        player_data = self.get_player_data(ctx.author.id)
        if not player_data:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
        
        # Check stamina (5 stamina per dungeon entry)
        if player_data["stamina"] < 5:
            await ctx.send(f"{ctx.author.mention}, you need at least 5 stamina to enter a dungeon!")
            return
        
        # Use stamina
        new_stamina = player_data["stamina"] - 5
        self.update_player_stamina(ctx.author.id, new_stamina)
        
        # Get dungeon details
        dungeon_data = self.get_dungeon_details(dungeon_id)
        if not dungeon_data:
            await ctx.send(f"{ctx.author.mention}, that dungeon doesn't exist!")
            return
        
        # Check player level
        if player_data["level"] < dungeon_data["min_level"]:
            await ctx.send(
                f"{ctx.author.mention}, you need to be level {dungeon_data['min_level']} to enter this dungeon! "
                f"You are only level {player_data['level']}."
            )
            return
        
        # Determine floor to enter
        if floor is None:
            # Get player's highest floor
            highest_floor = self.get_player_highest_floor(player_data["id"], dungeon_id)
            
            # Start at the next floor or first floor
            floor = min(highest_floor + 1, dungeon_data["floor_count"])
        
        # Validate floor number
        if floor < 1 or floor > dungeon_data["floor_count"]:
            await ctx.send(
                f"{ctx.author.mention}, invalid floor number! The dungeon has floors 1-{dungeon_data['floor_count']}."
            )
            return
        
        # Check if floor is accessible
        highest_floor = self.get_player_highest_floor(player_data["id"], dungeon_id)
        if floor > highest_floor + 1:
            await ctx.send(
                f"{ctx.author.mention}, you cannot skip floors! "
                f"Your highest completed floor is {highest_floor}."
            )
            return
        
        # Start the dungeon floor
        await self.start_dungeon_floor(ctx, dungeon_id, floor)
    
    @commands.command(name="floor")
    async def floor_command(self, ctx, dungeon_id: int = None, floor: int = None):
        """🏰 Enter a specific floor of a dungeon"""
        # Forward to dungeon command
        await self.dungeon_command(ctx, dungeon_id, floor)
    
    @commands.command(name="progress")
    async def progress_command(self, ctx):
        """🏰 View your dungeon progress"""
        # Get player data
        player_data = self.get_player_data(ctx.author.id)
        if not player_data:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
        
        # Get completed floors
        self.cursor.execute("""
            SELECT d.id, d.name, d.floor_count, MAX(cf.floor_number) as highest_floor
            FROM dungeons d
            LEFT JOIN completed_floors cf ON d.id = cf.dungeon_id AND cf.player_id = ?
            GROUP BY d.id, d.name, d.floor_count
            ORDER BY d.min_level ASC
        """, (player_data["id"],))
        
        results = self.cursor.fetchall()
        
        if not results:
            await ctx.send(f"{ctx.author.mention}, you haven't unlocked any dungeons yet!")
            return
        
        # Create progress embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Dungeon Progress",
            description="Your progress in each dungeon:",
            color=discord.Color.blue()
        )
        
        for dungeon_id, name, floor_count, highest_floor in results:
            # Handle null highest floor
            highest_floor = highest_floor or 0
            
            # Calculate completion percentage
            completion = (highest_floor / floor_count) * 100
            
            # Create progress bar
            bar_length = 10
            filled_length = int(bar_length * (highest_floor / floor_count))
            progress_bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            # Add field
            embed.add_field(
                name=name,
                value=f"`{progress_bar}` {highest_floor}/{floor_count} floors ({completion:.1f}%)\n"
                      f"Next floor: {min(highest_floor + 1, floor_count)}\n"
                      f"Use `!dungeon {dungeon_id}` to continue",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(DungeonSystem(bot))