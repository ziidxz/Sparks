import random
import math
import logging

logger = logging.getLogger('bot.probability')

def calculate_critical(crit_rate):
    """
    Calculates if an attack is a critical hit based on the critical rate
    
    Args:
        crit_rate (float): The chance of a critical hit in percentage (e.g., 15.0 for 15%)
        
    Returns:
        bool: True if critical hit, False otherwise
    """
    return random.random() * 100 < crit_rate

def calculate_dodge(dodge_rate):
    """
    Calculates if an attack is dodged based on the dodge rate
    
    Args:
        dodge_rate (float): The chance of dodging in percentage (e.g., 10.0 for 10%)
        
    Returns:
        bool: True if attack is dodged, False otherwise
    """
    return random.random() * 100 < dodge_rate

def calculate_drop_chance(drop_rate):
    """
    Calculates if an item drops based on the drop rate
    
    Args:
        drop_rate (float): The chance of the item dropping (e.g., 0.1 for 10%)
        
    Returns:
        bool: True if item drops, False otherwise
    """
    return random.random() < drop_rate

def calculate_gacha_rarity(pack_type):
    """
    Calculates the rarity of a card pulled from a gacha pack
    
    Args:
        pack_type (str): The type of pack ('basic', 'premium', or 'legendary')
        
    Returns:
        str: The rarity of the pulled card
    """
    rarities = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    
    # Define probability weights based on pack type
    if pack_type == "basic":
        weights = [55, 30, 10, 4, 1]  # 55% Common, 30% Uncommon, etc.
    elif pack_type == "premium":
        weights = [20, 35, 30, 10, 5]
    elif pack_type == "legendary":
        weights = [5, 15, 35, 30, 15]
    else:
        weights = [40, 30, 20, 7, 3]  # Default weights if unknown pack type
    
    # Normalize weights to add up to 1.0
    total = sum(weights)
    normalized_weights = [w / total for w in weights]
    
    # Cumulative distribution for weighted random selection
    cumulative = 0
    cumulative_weights = []
    for weight in normalized_weights:
        cumulative += weight
        cumulative_weights.append(cumulative)
    
    # Roll random number between 0 and 1
    roll = random.random()
    
    # Find which rarity the roll corresponds to
    for i, threshold in enumerate(cumulative_weights):
        if roll <= threshold:
            logger.debug(f"Gacha roll: {roll}, got {rarities[i]} from {pack_type} pack")
            return rarities[i]
    
    # Fallback to Common (should never happen due to cumulative weights)
    return "Common"

def calculate_skill_proc(skill_chance):
    """
    Calculates if a skill triggers based on its activation chance
    
    Args:
        skill_chance (float): The chance of skill activation (e.g., 0.3 for 30%)
        
    Returns:
        bool: True if skill triggers, False otherwise
    """
    return random.random() < skill_chance

def calculate_level_stats_bonus(base_stat, rarity, level_multiplier=0.1):
    """
    Calculates the bonus stats gained from leveling up based on card rarity
    
    Args:
        base_stat (int): The base value of the stat
        rarity (str): The rarity of the card
        level_multiplier (float): Multiplier for how much stats increase per level
        
    Returns:
        float: The stat bonus to be added
    """
    rarity_multipliers = {
        "Common": 1.0,
        "Uncommon": 1.2,
        "Rare": 1.5,
        "Epic": 1.8,
        "Legendary": 2.2
    }
    
    multiplier = rarity_multipliers.get(rarity, 1.0)
    return base_stat * level_multiplier * multiplier

def calculate_trade_fairness(card1_data, card2_data):
    """
    Calculates a fairness score for a trade between two cards
    
    Args:
        card1_data (tuple): (rarity, level, attack, defense, speed)
        card2_data (tuple): (rarity, level, attack, defense, speed)
        
    Returns:
        float: Fairness score (1.0 is perfectly fair, >1.0 favors card1, <1.0 favors card2)
    """
    # Rarity weights
    rarity_values = {
        "Common": 1,
        "Uncommon": 2,
        "Rare": 4,
        "Epic": 8,
        "Legendary": 16
    }
    
    rarity1, level1, attack1, defense1, speed1 = card1_data
    rarity2, level2, attack2, defense2, speed2 = card2_data
    
    # Calculate card values
    card1_value = (rarity_values.get(rarity1, 1) * 100) + (level1 * 20) + (attack1 + defense1 + speed1) * 0.5
    card2_value = (rarity_values.get(rarity2, 1) * 100) + (level2 * 20) + (attack2 + defense2 + speed2) * 0.5
    
    # Return fairness ratio
    if card2_value == 0:  # Avoid division by zero
        return float('inf')
    
    return card1_value / card2_value

def calculate_reward_multiplier(difficulty, performance=1.0):
    """
    Calculates a reward multiplier based on difficulty and performance
    
    Args:
        difficulty (int): Difficulty level (1-10)
        performance (float): Performance score (0.0-1.0)
        
    Returns:
        float: Reward multiplier
    """
    base_multiplier = 0.8 + (difficulty * 0.2)  # Base multiplier based on difficulty
    performance_bonus = performance * 0.5  # Performance bonus up to 50%
    
    return base_multiplier + performance_bonus

def calculate_battle_element_effectiveness(attacker_element, defender_element):
    """
    Calculates the element effectiveness multiplier for battles
    
    Args:
        attacker_element (str): The element of the attacker
        defender_element (str): The element of the defender
        
    Returns:
        float: Damage multiplier based on element effectiveness
    """
    # Element effectiveness chart
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
        "Star": {"strong": [], "weak": []},
        "Wind": {"strong": ["Earth"], "weak": ["Electric"]},  # For Naruto characters
        "Lightning": {"strong": ["Water"], "weak": ["Earth"]}  # For Naruto characters
    }
    
    # Default is neutral effectiveness
    multiplier = 1.0
    
    # Check if attacker's element exists in chart
    if attacker_element in element_chart:
        # Check if defender is weak to this element
        if defender_element in element_chart[attacker_element]["strong"]:
            multiplier = 1.5  # Super effective
        # Check if defender resists this element
        elif defender_element in element_chart[attacker_element]["weak"]:
            multiplier = 0.75  # Not very effective
            
    return multiplier
