import discord
from discord.ext import commands
import random
import asyncio
import time
from utils.probability import calculate_critical, calculate_dodge

class PvP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.pvp_cooldowns = {}  # {user_id: timestamp}
        self.pvp_challenges = {}  # {challenger_id: {target_id, expiry_time}}
    
    def get_equipped_card(self, user_id):
        """Gets a user's equipped card details."""
        self.cursor.execute("""
            SELECT id, name, rarity, level, attack, defense, speed, element,
                   skill, skill_description, skill_mp_cost, critical_rate,
                   dodge_rate, image_url
            FROM usercards
            WHERE user_id = ? AND equipped = 1
        """, (user_id,))
        
        return self.cursor.fetchone()
    
    @commands.command(name="pvp")
    async def pvp_command(self, ctx, opponent: discord.Member = None):
        """Challenge another player to a PvP battle"""
        challenger_id = ctx.author.id
        
        # Self-challenge check
        if opponent and opponent.id == challenger_id:
            await ctx.send(f"{ctx.author.mention}, you can't challenge yourself to a battle!")
            return
        
        # Bot-challenge check
        if opponent and opponent.bot:
            await ctx.send(f"{ctx.author.mention}, you can't challenge a bot to a battle!")
            return
        
        # If no opponent specified, show PvP stats
        if not opponent:
            await self.pvp_stats_command(ctx, ctx.author)
            return
        
        target_id = opponent.id
        
        # Check if both users have profiles
        self.cursor.execute("SELECT stamina FROM players WHERE user_id = ?", (challenger_id,))
        challenger = self.cursor.fetchone()
        
        self.cursor.execute("SELECT stamina FROM players WHERE user_id = ?", (target_id,))
        target = self.cursor.fetchone()
        
        if not challenger or not target:
            await ctx.send(f"{ctx.author.mention}, both players need to have created a profile with `!start`!")
            return
        
        # Check stamina
        if challenger[0] < 3:
            await ctx.send(f"{ctx.author.mention}, you need at least **3 stamina** to initiate a PvP battle!")
            return
        
        # Check if challenger has an equipped card
        challenger_card = self.get_equipped_card(challenger_id)
        
        if not challenger_card:
            await ctx.send(f"{ctx.author.mention}, you need to equip a card first! Use `!equip [card_id]`.")
            return
        
        # Check if target has an equipped card
        target_card = self.get_equipped_card(target_id)
        
        if not target_card:
            await ctx.send(f"{ctx.author.mention}, {opponent.display_name} doesn't have a card equipped!")
            return
        
        # Check cooldown
        current_time = time.time()
        if challenger_id in self.pvp_cooldowns:
            cooldown_time = self.pvp_cooldowns[challenger_id]
            if current_time < cooldown_time:
                remaining = int(cooldown_time - current_time)
                await ctx.send(f"{ctx.author.mention}, you're on cooldown! You can challenge again in {remaining} seconds.")
                return
        
        # Create a challenge that expires in 60 seconds
        expiry_time = current_time + 60
        self.pvp_challenges[challenger_id] = {
            "target_id": target_id,
            "expiry": expiry_time,
            "channel_id": ctx.channel.id
        }
        
        # Set cooldown (2 minutes)
        self.pvp_cooldowns[challenger_id] = current_time + 120
        
        # Create challenge message
        embed = discord.Embed(
            title="⚔️ PvP Challenge",
            description=f"{ctx.author.mention} has challenged {opponent.mention} to a battle!",
            color=discord.Color.red()
        )
        
        # Add card preview
        c_id, c_name, c_rarity, c_level, c_attack, c_defense, c_speed, c_element, c_skill, c_skill_desc, c_skill_mp, c_crit, c_dodge, c_image = challenger_card
        
        embed.add_field(
            name=f"{ctx.author.display_name}'s Card",
            value=f"**{c_name}** (Lvl {c_level} {c_rarity})\n"
                  f"ATK: {c_attack} · DEF: {c_defense} · SPD: {c_speed}",
            inline=True
        )
        
        t_id, t_name, t_rarity, t_level, t_attack, t_defense, t_speed, t_element, t_skill, t_skill_desc, t_skill_mp, t_crit, t_dodge, t_image = target_card
        
        embed.add_field(
            name=f"{opponent.display_name}'s Card",
            value=f"**{t_name}** (Lvl {t_level} {t_rarity})\n"
                  f"ATK: {t_attack} · DEF: {t_defense} · SPD: {t_speed}",
            inline=True
        )
        
        embed.set_footer(text=f"Type !accept to accept the challenge • Expires in 60 seconds")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="accept")
    async def accept_challenge(self, ctx):
        """Accept a PvP challenge from another player"""
        defender_id = ctx.author.id
        
        # Find a challenge where this user is the target
        challenger_id = None
        for cid, challenge in list(self.pvp_challenges.items()):
            if challenge["target_id"] == defender_id:
                challenger_id = cid
                challenge_data = challenge
                break
        
        if not challenger_id:
            await ctx.send(f"{ctx.author.mention}, you don't have any active challenges!")
            return
        
        # Check if challenge is expired
        current_time = time.time()
        if current_time > challenge_data["expiry"]:
            del self.pvp_challenges[challenger_id]
            await ctx.send(f"{ctx.author.mention}, that challenge has expired!")
            return
        
        # Get challenger user
        challenger = self.bot.get_user(challenger_id)
        if not challenger:
            await ctx.send(f"{ctx.author.mention}, the challenger is no longer available!")
            del self.pvp_challenges[challenger_id]
            return
        
        # Check defender stamina
        self.cursor.execute("SELECT stamina FROM players WHERE user_id = ?", (defender_id,))
        defender = self.cursor.fetchone()
        
        if not defender or defender[0] < 3:
            await ctx.send(f"{ctx.author.mention}, you need at least **3 stamina** to accept a PvP battle!")
            return
        
        # Remove the challenge
        del self.pvp_challenges[challenger_id]
        
        # Deduct stamina from both players
        self.cursor.execute("UPDATE players SET stamina = stamina - 3 WHERE user_id = ?", (challenger_id,))
        self.cursor.execute("UPDATE players SET stamina = stamina - 3 WHERE user_id = ?", (defender_id,))
        self.db.conn.commit()
        
        # Get current channel
        channel = ctx.channel
        
        # Start the battle
        await self.start_pvp_battle(channel, challenger, ctx.author)
    
    async def start_pvp_battle(self, channel, player1, player2):
        """Handles the actual PvP battle between two players."""
        p1_id, p2_id = player1.id, player2.id
        
        # Get both players' cards
        p1_card = self.get_equipped_card(p1_id)
        p2_card = self.get_equipped_card(p2_id)
        
        if not p1_card or not p2_card:
            await channel.send(f"Error: One of the players doesn't have a card equipped anymore!")
            return
        
        # Unpack card data
        p1_card_id, p1_name, p1_rarity, p1_level, p1_attack, p1_defense, p1_speed, p1_element, p1_skill, p1_skill_desc, p1_skill_mp, p1_crit, p1_dodge, p1_image = p1_card
        
        p2_card_id, p2_name, p2_rarity, p2_level, p2_attack, p2_defense, p2_speed, p2_element, p2_skill, p2_skill_desc, p2_skill_mp, p2_crit, p2_dodge, p2_image = p2_card
        
        # Set up battle variables
        p1_hp = 500 + (p1_level * 15)
        p1_max_hp = p1_hp
        
        p2_hp = 500 + (p2_level * 15)
        p2_max_hp = p2_hp
        
        # Get MP from database
        self.cursor.execute("SELECT mp FROM players WHERE user_id = ?", (p1_id,))
        p1_mp = self.cursor.fetchone()[0]
        p1_max_mp = 100 + (p1_level * 5)
        
        self.cursor.execute("SELECT mp FROM players WHERE user_id = ?", (p2_id,))
        p2_mp = self.cursor.fetchone()[0]
        p2_max_mp = 100 + (p2_level * 5)
        
        # Determine who goes first based on speed
        player1_first = p1_speed >= p2_speed
        current_turn = "p1" if player1_first else "p2"
        
        # Battle message
        battle_message = await channel.send("⚔️ **PvP Battle Start!**")
        
        # Battle effects and animations
        battle_effects = ["Bonked", "Whacked", "Booped", "Thwacked", "Slammed", "Pummeled"]
        
        # Skill cooldowns
        p1_skill_cooldown = 0
        p2_skill_cooldown = 0
        
        # Status effects (turns remaining)
        p1_status = {}
        p2_status = {}
        
        # Battle loop
        turn = 0
        while p1_hp > 0 and p2_hp > 0:
            turn += 1
            await asyncio.sleep(2)
            
            # Generate resource bars
            def resource_bar(current, max_val, char_filled="█", char_empty="░"):
                percentage = current / max_val
                filled = int(percentage * 10)
                empty = 10 - filled
                return f"**`{char_filled * filled}{char_empty * empty}`** **`{current}/{max_val}`**"
            
            # Handle status effects
            for status, turns in list(p1_status.items()):
                if status == "burning":
                    burn_damage = int(p1_max_hp * 0.05)  # 5% damage
                    p1_hp = max(0, p1_hp - burn_damage)
                    
                p1_status[status] -= 1
                if p1_status[status] <= 0:
                    del p1_status[status]
            
            for status, turns in list(p2_status.items()):
                if status == "burning":
                    burn_damage = int(p2_max_hp * 0.05)  # 5% damage
                    p2_hp = max(0, p2_hp - burn_damage)
                    
                p2_status[status] -= 1
                if p2_status[status] <= 0:
                    del p2_status[status]
            
            # Handle cooldowns
            if p1_skill_cooldown > 0:
                p1_skill_cooldown -= 1
            if p2_skill_cooldown > 0:
                p2_skill_cooldown -= 1
            
            # Battle logic
            if current_turn == "p1":
                # Player 1's turn
                # Check if player has enough MP to use skill
                can_use_skill = p1_mp >= p1_skill_mp and p1_skill_cooldown == 0
                
                # Randomly decide to use skill (more likely if HP is low)
                skill_chance = 0.3
                if p1_hp < p1_max_hp * 0.4:  # Below 40% HP
                    skill_chance = 0.7
                
                use_skill = can_use_skill and random.random() < skill_chance
                
                if use_skill:
                    # Use skill
                    p1_mp -= p1_skill_mp
                    p1_skill_cooldown = 3  # Set cooldown
                    
                    # Apply skill effects
                    if "fire" in p1_skill.lower() or "flame" in p1_skill.lower():
                        p2_status["burning"] = 3  # Burning for 3 turns
                        damage_multiplier = 1.3
                    elif "heal" in p1_skill.lower():
                        heal_amount = int(p1_max_hp * 0.2)  # Heal 20% of max HP
                        p1_hp = min(p1_max_hp, p1_hp + heal_amount)
                        damage_multiplier = 0.5
                    else:
                        damage_multiplier = 1.5  # Generic damage boost
                    
                    # Calculate damage with skill boost
                    base_damage = max(5, p1_attack - (p2_defense // 2))
                    damage = int(base_damage * damage_multiplier)
                    
                    # Critical hit chance
                    is_critical = calculate_critical(p1_crit)
                    if is_critical:
                        damage = int(damage * 1.5)
                    
                    # Apply damage
                    p2_hp = max(0, p2_hp - damage)
                    
                    # Build action text
                    action_text = f"**{player1.display_name}** used **{p1_skill}**!"
                    damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"Dealt `-{damage}`!"
                    
                    if "burning" in p2_status:
                        damage_text += " 🔥 Enemy is burning!"
                    elif "heal" in p1_skill.lower():
                        damage_text = f"💖 Healed `+{heal_amount}`!"
                    
                else:
                    # Regular attack
                    base_damage = max(5, p1_attack - (p2_defense // 2))
                    
                    # Check for dodge
                    is_dodged = calculate_dodge(p2_dodge)
                    
                    if is_dodged:
                        damage = 0
                        action_text = f"**{player1.display_name}** attacked!"
                        damage_text = "😎 Enemy dodged the attack!"
                    else:
                        # Critical hit chance
                        is_critical = calculate_critical(p1_crit)
                        damage = base_damage * 1.5 if is_critical else base_damage
                        
                        # Apply damage
                        p2_hp = max(0, p2_hp - damage)
                        
                        action_text = f"**{player1.display_name}** attacked!"
                        damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"Dealt `-{damage}`!"
                
                current_turn = "p2"
                
            else:
                # Player 2's turn
                # Check if player has enough MP to use skill
                can_use_skill = p2_mp >= p2_skill_mp and p2_skill_cooldown == 0
                
                # Randomly decide to use skill (more likely if HP is low)
                skill_chance = 0.3
                if p2_hp < p2_max_hp * 0.4:  # Below 40% HP
                    skill_chance = 0.7
                
                use_skill = can_use_skill and random.random() < skill_chance
                
                if use_skill:
                    # Use skill
                    p2_mp -= p2_skill_mp
                    p2_skill_cooldown = 3  # Set cooldown
                    
                    # Apply skill effects
                    if "fire" in p2_skill.lower() or "flame" in p2_skill.lower():
                        p1_status["burning"] = 3  # Burning for 3 turns
                        damage_multiplier = 1.3
                    elif "heal" in p2_skill.lower():
                        heal_amount = int(p2_max_hp * 0.2)  # Heal 20% of max HP
                        p2_hp = min(p2_max_hp, p2_hp + heal_amount)
                        damage_multiplier = 0.5
                    else:
                        damage_multiplier = 1.5  # Generic damage boost
                    
                    # Calculate damage with skill boost
                    base_damage = max(5, p2_attack - (p1_defense // 2))
                    damage = int(base_damage * damage_multiplier)
                    
                    # Critical hit chance
                    is_critical = calculate_critical(p2_crit)
                    if is_critical:
                        damage = int(damage * 1.5)
                    
                    # Apply damage
                    p1_hp = max(0, p1_hp - damage)
                    
                    # Build action text
                    action_text = f"**{player2.display_name}** used **{p2_skill}**!"
                    damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"Dealt `-{damage}`!"
                    
                    if "burning" in p1_status:
                        damage_text += " 🔥 Enemy is burning!"
                    elif "heal" in p2_skill.lower():
                        damage_text = f"💖 Healed `+{heal_amount}`!"
                    
                else:
                    # Regular attack
                    base_damage = max(5, p2_attack - (p1_defense // 2))
                    
                    # Check for dodge
                    is_dodged = calculate_dodge(p1_dodge)
                    
                    if is_dodged:
                        damage = 0
                        action_text = f"**{player2.display_name}** attacked!"
                        damage_text = "😎 Enemy dodged the attack!"
                    else:
                        # Critical hit chance
                        is_critical = calculate_critical(p2_crit)
                        damage = base_damage * 1.5 if is_critical else base_damage
                        
                        # Apply damage
                        p1_hp = max(0, p1_hp - damage)
                        
                        action_text = f"**{player2.display_name}** attacked!"
                        damage_text = f"💥 Critical Hit! `-{damage}`!" if is_critical else f"{random.choice(battle_effects)} for `-{damage}`!"
                
                current_turn = "p1"
            
            # MP regeneration (5% of max MP per turn)
            p1_mp = min(p1_max_mp, p1_mp + int(p1_max_mp * 0.05))
            p2_mp = min(p2_max_mp, p2_mp + int(p2_max_mp * 0.05))
            
            # Create battle embed
            title = f"Turn {turn}: {player1.display_name if current_turn == 'p1' else player2.display_name}'s Turn Next"
            embed = discord.Embed(title=title, color=discord.Color.purple())
            
            # Player 1 info
            p1_status_text = ", ".join([f"{status.capitalize()}" for status in p1_status]) if p1_status else "None"
            embed.add_field(
                name=f"{player1.display_name} - {p1_name} (Lvl {p1_level})",
                value=f"HP: {resource_bar(p1_hp, p1_max_hp)}\n"
                      f"MP: {resource_bar(p1_mp, p1_max_mp, '🔷', '⬜')}\n"
                      f"Status: {p1_status_text}\n"
                      f"Skill Ready: {'✅' if p1_skill_cooldown == 0 else f'❌ ({p1_skill_cooldown} turns)'}",
                inline=False
            )
            
            # Player 2 info
            p2_status_text = ", ".join([f"{status.capitalize()}" for status in p2_status]) if p2_status else "None"
            embed.add_field(
                name=f"{player2.display_name} - {p2_name} (Lvl {p2_level})",
                value=f"HP: {resource_bar(p2_hp, p2_max_hp)}\n"
                      f"MP: {resource_bar(p2_mp, p2_max_mp, '🔷', '⬜')}\n"
                      f"Status: {p2_status_text}\n"
                      f"Skill Ready: {'✅' if p2_skill_cooldown == 0 else f'❌ ({p2_skill_cooldown} turns)'}",
                inline=False
            )
            
            # Last action
            embed.add_field(name="Last Action", value=f"{action_text}\n{damage_text}", inline=False)
            
            # Set card images as thumbnails (alternating)
            if turn % 2 == 1 and p1_image:
                embed.set_thumbnail(url=p1_image)
            elif turn % 2 == 0 and p2_image:
                embed.set_thumbnail(url=p2_image)
            
            await battle_message.edit(embed=embed)
        
        # Battle ended - determine winner
        p1_won = p2_hp <= 0
        winner_id = p1_id if p1_won else p2_id
        loser_id = p2_id if p1_won else p1_id
        winner = player1 if p1_won else player2
        loser = player2 if p1_won else player1
        
        # Save PvP battle record
        self.cursor.execute("""
            INSERT INTO pvp_battles (player1_id, player2_id, player1_card, player2_card, winner_id, turns)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (p1_id, p2_id, p1_card_id, p2_card_id, winner_id, turn))
        
        # Update player stats
        if p1_won:
            self.cursor.execute("UPDATE players SET pvp_wins = pvp_wins + 1 WHERE user_id = ?", (p1_id,))
            self.cursor.execute("UPDATE players SET pvp_losses = pvp_losses + 1 WHERE user_id = ?", (p2_id,))
        else:
            self.cursor.execute("UPDATE players SET pvp_wins = pvp_wins + 1 WHERE user_id = ?", (p2_id,))
            self.cursor.execute("UPDATE players SET pvp_losses = pvp_losses + 1 WHERE user_id = ?", (p1_id,))
        
        # Calculate rewards
        gold_earned = 200 + (turn * 10)  # Base gold + extra for longer battles
        self.cursor.execute("UPDATE players SET gold = gold + ? WHERE user_id = ?", (gold_earned, winner_id))
        
        # Add card experience
        if p1_won:
            # Add XP to winner's card
            self.cursor.execute("UPDATE usercards SET xp = xp + ? WHERE id = ?", (50, p1_card_id))
        else:
            # Add XP to winner's card
            self.cursor.execute("UPDATE usercards SET xp = xp + ? WHERE id = ?", (50, p2_card_id))
        
        # Add consolation XP to loser's card
        if p1_won:
            self.cursor.execute("UPDATE usercards SET xp = xp + ? WHERE id = ?", (20, p2_card_id))
        else:
            self.cursor.execute("UPDATE usercards SET xp = xp + ? WHERE id = ?", (20, p1_card_id))
        
        # Update MP in database
        self.cursor.execute("UPDATE players SET mp = ? WHERE user_id = ?", (p1_mp, p1_id))
        self.cursor.execute("UPDATE players SET mp = ? WHERE user_id = ?", (p2_mp, p2_id))
        
        # Commit changes
        self.db.conn.commit()
        
        # Create result embed
        if p1_won:
            result_text = f"🏆 **{player1.display_name} Won!**"
            result_color = discord.Color.green()
        else:
            result_text = f"🏆 **{player2.display_name} Won!**"
            result_color = discord.Color.green()
        
        embed = discord.Embed(
            title=result_text,
            description=f"After an intense {turn}-turn battle, {winner.display_name} emerges victorious!",
            color=result_color
        )
        
        # Winner info
        embed.add_field(
            name="Winner Rewards",
            value=f"💰 {gold_earned} Gold\n✨ 50 Card EXP",
            inline=True
        )
        
        # Loser info
        embed.add_field(
            name="Consolation Prize",
            value=f"✨ 20 Card EXP",
            inline=True
        )
        
        # Battle stats
        embed.add_field(
            name="Battle Stats",
            value=f"Turns: {turn}\n"
                  f"Damage Dealt: {p1_max_hp - p1_hp} vs {p2_max_hp - p2_hp}",
            inline=False
        )
        
        # Set winner's card image
        if p1_won and p1_image:
            embed.set_image(url=p1_image)
        elif not p1_won and p2_image:
            embed.set_image(url=p2_image)
        
        await battle_message.edit(embed=embed)
    
    @commands.command(name="pvpstats")
    async def pvp_stats_command(self, ctx, member: discord.Member = None):
        """View your PvP battle statistics"""
        user = member or ctx.author
        user_id = user.id
        
        # Get player's PvP stats
        self.cursor.execute("""
            SELECT pvp_wins, pvp_losses
            FROM players
            WHERE user_id = ?
        """, (user_id,))
        
        result = self.cursor.fetchone()
        
        if not result:
            await ctx.send(f"{user.mention} hasn't started their journey yet! Use `!start` first.")
            return
        
        wins, losses = result
        total_battles = wins + losses
        win_rate = (wins / total_battles * 100) if total_battles > 0 else 0
        
        # Get recent battles
        self.cursor.execute("""
            SELECT 
                p.id, 
                p.player1_id, p.player2_id, p.winner_id, p.turns, p.timestamp,
                u1.name AS p1_card, u2.name AS p2_card
            FROM pvp_battles p
            JOIN usercards u1 ON p.player1_card = u1.id
            JOIN usercards u2 ON p.player2_card = u2.id
            WHERE p.player1_id = ? OR p.player2_id = ?
            ORDER BY p.timestamp DESC
            LIMIT 5
        """, (user_id, user_id))
        
        recent_battles = self.cursor.fetchall()
        
        # Create stats embed
        embed = discord.Embed(
            title=f"{user.display_name}'s PvP Statistics",
            color=discord.Color.blue()
        )
        
        # Overall stats
        embed.add_field(
            name="Overall Record",
            value=f"Wins: {wins}\n"
                  f"Losses: {losses}\n"
                  f"Total Battles: {total_battles}\n"
                  f"Win Rate: {win_rate:.1f}%",
            inline=False
        )
        
        # Recent battles
        if recent_battles:
            recent_text = ""
            for battle_id, p1_id, p2_id, winner_id, turns, timestamp, p1_card, p2_card in recent_battles:
                # Format timestamp
                import datetime
                battle_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                # Determine if user was player 1 or 2
                is_p1 = p1_id == user_id
                
                # Get opponent name
                opponent_id = p2_id if is_p1 else p1_id
                opponent = self.bot.get_user(opponent_id)
                opponent_name = opponent.display_name if opponent else f"User {opponent_id}"
                
                # Determine if user won
                user_won = winner_id == user_id
                result_text = "Won" if user_won else "Lost"
                emoji = "✅" if user_won else "❌"
                
                # Add to text
                if is_p1:
                    recent_text += f"{emoji} {result_text} vs {opponent_name} ({p1_card} vs {p2_card}) - {battle_time}\n"
                else:
                    recent_text += f"{emoji} {result_text} vs {opponent_name} ({p2_card} vs {p1_card}) - {battle_time}\n"
            
            embed.add_field(
                name="Recent Battles",
                value=recent_text,
                inline=False
            )
        else:
            embed.add_field(
                name="Recent Battles",
                value="No recent PvP battles found.",
                inline=False
            )
        
        # How to battle
        embed.add_field(
            name="How to Battle",
            value="Challenge someone with `!pvp @user`\n"
                  "Each battle costs 3 stamina\n"
                  "Win to earn gold and card EXP",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PvP(bot))
