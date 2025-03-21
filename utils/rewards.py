import random
import math
import logging
from utils.probability import calculate_drop_chance

logger = logging.getLogger('bot.rewards')

def get_gold_drop(level, difficulty_multiplier=1.0, bonus_multiplier=1.0):
    """
    Calculate gold rewards from battles based on enemy level and other factors
    
    Args:
        level (int): The level of the enemy/boss
        difficulty_multiplier (float): Multiplier for difficulty (higher for bosses)
        bonus_multiplier (float): Additional bonus multiplier (e.g., from boosts)
        
    Returns:
        int: Amount of gold to award
    """
    # Base gold is level-dependent with randomness
    base_gold = int((level * 15 + random.randint(0, level * 5)) * difficulty_multiplier * bonus_multiplier)
    
    # Add a small chance for bonus gold
    if calculate_drop_chance(0.1):  # 10% chance
        bonus = int(base_gold * 0.5)  # 50% bonus
        logger.debug(f"Bonus gold drop! +{bonus}")
        base_gold += bonus
    
    return base_gold

def get_exp_drop(level, difficulty_multiplier=1.0, bonus_multiplier=1.0):
    """
    Calculate experience rewards from battles based on enemy level and other factors
    
    Args:
        level (int): The level of the enemy/boss
        difficulty_multiplier (float): Multiplier for difficulty (higher for bosses)
        bonus_multiplier (float): Additional bonus multiplier (e.g., from boosts)
        
    Returns:
        int: Amount of experience to award
    """
    # Base EXP calculation with some randomness
    base_exp = int((10 + level * 8 + random.randint(0, level * 3)) * difficulty_multiplier * bonus_multiplier)
    
    # Add a small chance for bonus EXP
    if calculate_drop_chance(0.15):  # 15% chance
        bonus = int(base_exp * 0.4)  # 40% bonus
        logger.debug(f"Bonus EXP drop! +{bonus}")
        base_exp += bonus
    
    return base_exp

def get_material_rewards(enemy_level, enemy_type="normal", bonus_multiplier=1.0):
    """
    Determine material rewards from battles
    
    Args:
        enemy_level (int): The level of the enemy/boss
        enemy_type (str): Type of enemy ("normal", "boss", "raid")
        bonus_multiplier (float): Additional bonus multiplier
        
    Returns:
        list: List of tuples (material_id, quantity)
    """
    rewards = []
    
    # Basic material drop rates based on enemy type
    if enemy_type == "normal":
        # Common material (Crystal Shard)
        if calculate_drop_chance(0.3 * bonus_multiplier):  # 30% chance
            quantity = random.randint(1, 2)
            rewards.append((1, quantity))
        
        # Uncommon material (Magical Essence) for higher level enemies
        if enemy_level >= 10 and calculate_drop_chance(0.15 * bonus_multiplier):  # 15% chance
            quantity = 1
            rewards.append((2, quantity))
    
    elif enemy_type == "boss":
        # Common material (Crystal Shard)
        if calculate_drop_chance(0.8 * bonus_multiplier):  # 80% chance
            quantity = random.randint(2, 4)
            rewards.append((1, quantity))
        
        # Uncommon material (Magical Essence)
        if calculate_drop_chance(0.5 * bonus_multiplier):  # 50% chance
            quantity = random.randint(1, 3)
            rewards.append((2, quantity))
        
        # Rare material (Star Fragment) for higher level bosses
        if enemy_level >= 15 and calculate_drop_chance(0.25 * bonus_multiplier):  # 25% chance
            quantity = random.randint(1, 2)
            rewards.append((3, quantity))
    
    elif enemy_type == "raid":
        # Guaranteed common material (Crystal Shard)
        quantity = random.randint(5, 10)
        rewards.append((1, quantity))
        
        # High chance for uncommon material (Magical Essence)
        if calculate_drop_chance(0.8 * bonus_multiplier):  # 80% chance
            quantity = random.randint(3, 6)
            rewards.append((2, quantity))
        
        # Better chance for rare material (Star Fragment)
        if calculate_drop_chance(0.5 * bonus_multiplier):  # 50% chance
            quantity = random.randint(2, 4)
            rewards.append((3, quantity))
        
        # Epic material (Dragon Scale) for high level raids
        if enemy_level >= 30 and calculate_drop_chance(0.3 * bonus_multiplier):  # 30% chance
            quantity = 1
            rewards.append((4, quantity))
    
    # Very rare chance for cosmic dust regardless of enemy type
    if enemy_level >= 40 and calculate_drop_chance(0.05 * bonus_multiplier):  # 5% chance
        rewards.append((5, 1))  # Cosmic Dust
    
    # Elemental Cores based on the enemy's element (would need enemy element info)
    # This is just a placeholder logic - actual implementation would use the enemy's element
    if enemy_level >= 20 and calculate_drop_chance(0.2 * bonus_multiplier):  # 20% chance
        # Random elemental core (IDs 6-11)
        element_core_id = random.randint(6, 11)
        rewards.append((element_core_id, 1))
    
    return rewards

def get_daily_rewards(streak_days):
    """
    Determine rewards for daily login
    
    Args:
        streak_days (int): Number of consecutive daily logins
        
    Returns:
        dict: Dictionary of rewards {type: amount}
    """
    rewards = {
        "gold": 100 + (50 * min(streak_days, 7)),  # Caps at 450 gold
        "stamina": "full",  # Full stamina refill
    }
    
    # Every 3 days: material rewards
    if streak_days % 3 == 0:
        if streak_days < 9:  # First two 3-day milestones
            rewards["materials"] = [(1, 3), (2, 1)]  # Crystal Shards and Magical Essence
        elif streak_days < 21:  # Next four 3-day milestones
            rewards["materials"] = [(2, 2), (3, 1)]  # More Magical Essence and Star Fragment
        else:  # Beyond 21 days
            rewards["materials"] = [(2, 3), (3, 2), (4, 1)]  # Add Dragon Scale
    
    # Every 7 days: pack rewards
    if streak_days % 7 == 0:
        if streak_days < 14:  # First 7-day milestone
            rewards["pack"] = "basic"
        elif streak_days < 28:  # Second and third 7-day milestones
            rewards["pack"] = "premium"
        else:  # Beyond 28 days
            rewards["pack"] = "legendary"
    
    # Special milestones
    if streak_days == 30:
        rewards["special"] = "Exclusive 30-Day Card"
    elif streak_days == 100:
        rewards["special"] = "Exclusive 100-Day Card"
    
    return rewards

def get_pvp_rewards(winner, loser, turns_taken):
    """
    Calculate rewards for PvP battles
    
    Args:
        winner (int): Winner's level
        loser (int): Loser's level
        turns_taken (int): Number of battle turns
        
    Returns:
        dict: Dictionary of rewards for winner {type: amount}
    """
    # Base rewards
    base_gold = 100
    base_exp = 50
    
    # Level difference adjustment
    level_diff = loser - winner
    level_multiplier = 1.0 + (level_diff * 0.1)  # Bonus for beating higher levels, penalty for lower
    level_multiplier = max(0.5, min(level_multiplier, 2.0))  # Clamp between 0.5x and 2.0x
    
    # Quick victory bonus
    turn_multiplier = 1.0
    if turns_taken <= 5:
        turn_multiplier = 1.5  # 50% bonus for quick victory
    elif turns_taken >= 15:
        turn_multiplier = 0.8  # 20% penalty for long battles
    
    # Calculate final rewards
    gold = int(base_gold * level_multiplier * turn_multiplier)
    exp = int(base_exp * level_multiplier * turn_multiplier)
    
    # Ensure minimum rewards
    gold = max(50, gold)
    exp = max(20, exp)
    
    # Material reward chance increases with opponent level
    material_chance = min(0.3, 0.1 + (loser * 0.01))  # Caps at 30%
    materials = []
    
    if calculate_drop_chance(material_chance):
        if loser >= 20:
            materials.append((3, 1))  # Star Fragment
        elif loser >= 10:
            materials.append((2, 1))  # Magical Essence
        else:
            materials.append((1, 2))  # Crystal Shards
    
    return {
        "gold": gold,
        "exp": exp,
        "materials": materials
    }

def get_boss_rewards(boss_level, boss_id, player_performance=1.0):
    """
    Calculate rewards for boss battles
    
    Args:
        boss_level (int): Level of the boss
        boss_id (int): ID of the boss (for specific drops)
        player_performance (float): Performance score (0.0-1.0)
        
    Returns:
        dict: Dictionary of rewards {type: amount}
    """
    # Base rewards scaled by boss level
    base_gold = boss_level * 50
    base_exp = boss_level * 25
    
    # Performance multiplier (higher for better performance)
    performance_multiplier = 0.7 + (player_performance * 0.6)  # Range: 0.7x to 1.3x
    
    # Calculate final rewards
    gold = int(base_gold * performance_multiplier)
    exp = int(base_exp * performance_multiplier)
    
    # Boss-specific rewards would typically come from the database
    # This is placeholder logic
    materials = []
    
    # Guaranteed materials based on boss level
    if boss_level >= 30:
        materials.append((4, 1))  # Dragon Scale
        materials.append((3, random.randint(2, 4)))  # Star Fragments
    elif boss_level >= 15:
        materials.append((3, random.randint(1, 3)))  # Star Fragments
        materials.append((2, random.randint(2, 5)))  # Magical Essence
    else:
        materials.append((2, random.randint(1, 3)))  # Magical Essence
        materials.append((1, random.randint(3, 8)))  # Crystal Shards
    
    # Chance for elemental cores based on boss's element (would be from database)
    # This is placeholder logic - actual implementation would use boss's element
    element_core_chance = min(0.8, 0.3 + (boss_level * 0.02))  # Caps at 80%
    if calculate_drop_chance(element_core_chance):
        # Random elemental core (IDs 6-11)
        element_core_id = random.randint(6, 11)
        materials.append((element_core_id, random.randint(1, 2)))
    
    # Rare chance for cosmic dust from high-level bosses
    if boss_level >= 40 and calculate_drop_chance(0.15):  # 15% chance
        materials.append((5, 1))  # Cosmic Dust
    
    return {
        "gold": gold,
        "exp": exp,
        "materials": materials
    }
