import random
import logging
from utils.probability import calculate_gacha_rarity

logger = logging.getLogger('bot.card_generator')

class CardGenerator:
    def __init__(self, db):
        self.db = db
        self.cursor = db.conn.cursor()
        
        # Cache all templates on initialization
        self.card_templates = self.get_all_card_templates()
        
        # Base stats ranges by rarity
        self.rarity_stats = {
            "Common": {
                "attack": (50, 80),
                "defense": (40, 70),
                "speed": (40, 70),
                "skill_mp_cost": (15, 20),
                "critical_rate": (3.0, 8.0),
                "dodge_rate": (3.0, 8.0)
            },
            "Uncommon": {
                "attack": (70, 100),
                "defense": (60, 90),
                "speed": (60, 90),
                "skill_mp_cost": (20, 25),
                "critical_rate": (5.0, 10.0),
                "dodge_rate": (5.0, 10.0)
            },
            "Rare": {
                "attack": (90, 120),
                "defense": (80, 110),
                "speed": (80, 110),
                "skill_mp_cost": (20, 30),
                "critical_rate": (8.0, 15.0),
                "dodge_rate": (8.0, 15.0)
            },
            "Epic": {
                "attack": (110, 150),
                "defense": (100, 140),
                "speed": (100, 140),
                "skill_mp_cost": (25, 40),
                "critical_rate": (10.0, 20.0),
                "dodge_rate": (10.0, 20.0)
            },
            "Legendary": {
                "attack": (140, 200),
                "defense": (130, 180),
                "speed": (130, 180),
                "skill_mp_cost": (30, 60),
                "critical_rate": (15.0, 30.0),
                "dodge_rate": (15.0, 30.0)
            }
        }
        
        # Elements
        self.elements = [
            "Fire", "Water", "Earth", "Air", "Electric", "Ice", 
            "Light", "Dark", "Cute", "Sweet", "Star"
        ]
        
        # Skill name patterns
        self.skill_patterns = {
            "Fire": ["Flame", "Blaze", "Inferno", "Burn", "Fire", "Heat"],
            "Water": ["Aqua", "Splash", "Torrent", "Wave", "Deluge", "Bubble"],
            "Earth": ["Quake", "Slam", "Rock", "Stone", "Mountain", "Terra"],
            "Air": ["Wind", "Gust", "Tempest", "Storm", "Breeze", "Sky"],
            "Electric": ["Thunder", "Shock", "Spark", "Zap", "Lightning", "Voltage"],
            "Ice": ["Frost", "Freeze", "Blizzard", "Chill", "Snow", "Glacial"],
            "Light": ["Shine", "Radiance", "Holy", "Divine", "Purify", "Blessing"],
            "Dark": ["Shadow", "Void", "Darkness", "Abyss", "Curse", "Nightmare"],
            "Cute": ["Charm", "Cuddle", "Sweet", "Adorable", "Lovely", "Fluffy"],
            "Sweet": ["Candy", "Sugar", "Honey", "Syrup", "Dessert", "Treat"],
            "Star": ["Celestial", "Cosmic", "Stellar", "Astral", "Nova", "Meteor"]
        }
        
        # Generic skill effect words
        self.skill_effects = ["Strike", "Blast", "Burst", "Beam", "Wave", "Slash", "Punch", "Kick"]
        
        # Skill description templates
        self.skill_descriptions = {
            "damage": [
                "Deals {element} damage to the opponent with {chance}% chance to {status}.",
                "Unleashes a powerful {element} attack that {effect}.",
                "Focuses energy into a concentrated {element} blast.",
                "Channels the power of {element} to strike opponents."
            ],
            "healing": [
                "Restores {amount}% of max HP and provides {bonus}.",
                "Heals for {amount}% of maximum health and {effect}.",
                "Creates a healing aura that restores {amount}% HP.",
                "Channels restorative energy to heal {amount}% of max HP."
            ],
            "buff": [
                "Increases {stat} by {amount}% for {duration} turns.",
                "Powers up {stat} by {amount}%, lasting {duration} turns.",
                "Enhances {stat} capabilities by {amount}% for {duration} turns.",
                "Temporarily boosts {stat} by {amount}% for {duration} turns."
            ],
            "debuff": [
                "Reduces opponent's {stat} by {amount}% for {duration} turns.",
                "Weakens enemy {stat} by {amount}% for {duration} turns.",
                "Diminishes opponent's {stat} capabilities by {amount}% for {duration} turns.",
                "Applies a {element} effect that lowers {stat} by {amount}%."
            ],
            "status": [
                "Has a {chance}% chance to inflict {status} for {duration} turns.",
                "May cause {status} for {duration} turns with {chance}% probability.",
                "Can {status} opponents for {duration} turns.",
                "{element} power has {chance}% chance to cause {status}."
            ]
        }
        
        # Status effects by element
        self.status_effects = {
            "Fire": "burning",
            "Water": "soaked",
            "Earth": "slowed",
            "Air": "disoriented",
            "Electric": "paralyzed",
            "Ice": "frozen",
            "Light": "blinded",
            "Dark": "cursed",
            "Cute": "charmed",
            "Sweet": "distracted",
            "Star": "dazzled"
        }
    
    def get_all_card_templates(self):
        """Fetch all card templates from the database for reference"""
        self.cursor.execute("""
            SELECT id, name, rarity, attack, defense, speed, element, skill, 
                   skill_description, skill_mp_cost, skill_cooldown, 
                   critical_rate, dodge_rate, lore, image_url 
            FROM cards
        """)
        
        templates = self.cursor.fetchall()
        logger.debug(f"Loaded {len(templates)} card templates from database")
        return templates
    
    def generate_card_from_template(self, template_id=None, rarity=None):
        """
        Generate a card based on an existing template with some randomization
        
        Args:
            template_id (int, optional): Specific template ID to use
            rarity (str, optional): Target rarity if no template specified
            
        Returns:
            dict: Generated card data
        """
        # If no template specified, pick based on rarity
        if template_id is None:
            if rarity is None:
                rarity = calculate_gacha_rarity("basic")  # Default to basic pack odds
            
            # Filter templates by rarity
            matching_templates = [t for t in self.card_templates if t[2] == rarity]
            
            if not matching_templates:
                # Fallback to any template of appropriate rarity
                matching_templates = [t for t in self.card_templates if t[2] == rarity]
                
                if not matching_templates:
                    # Last resort: pick any template
                    matching_templates = self.card_templates
            
            template = random.choice(matching_templates)
        else:
            # Find specific template by ID
            matching_templates = [t for t in self.card_templates if t[0] == template_id]
            if not matching_templates:
                # Fallback to random template
                template = random.choice(self.card_templates)
            else:
                template = matching_templates[0]
        
        # Unpack template data
        (id, name, rarity, attack, defense, speed, element, skill, 
         skill_desc, skill_mp, skill_cd, crit_rate, dodge_rate, lore, image_url) = template
        
        # Apply small random variations to stats (±10%)
        attack_variation = int(attack * random.uniform(-0.05, 0.10))
        defense_variation = int(defense * random.uniform(-0.05, 0.10))
        speed_variation = int(speed * random.uniform(-0.05, 0.10))
        
        # Create card data
        card_data = {
            "base_card_id": id,
            "name": name,
            "rarity": rarity,
            "attack": max(1, attack + attack_variation),
            "defense": max(1, defense + defense_variation),
            "speed": max(1, speed + speed_variation),
            "element": element,
            "skill": skill,
            "skill_description": skill_desc,
            "skill_mp_cost": skill_mp,
            "skill_cooldown": skill_cd,
            "critical_rate": crit_rate,
            "dodge_rate": dodge_rate,
            "level": 1,
            "xp": 0,
            "equipped": 0,
            "evolution_stage": 0,
            "image_url": image_url
        }
        
        return card_data
    
    def generate_random_card(self, rarity=None):
        """
        Generate a completely random card with new stats and abilities
        
        Args:
            rarity (str, optional): Target rarity, randomly determined if None
            
        Returns:
            dict: Generated card data
        """
        # Determine rarity if not specified
        if rarity is None:
            rarity = calculate_gacha_rarity("premium")  # Use premium pack odds for random generation
        
        # Choose random element
        element = random.choice(self.elements)
        
        # Generate random stats based on rarity
        stat_ranges = self.rarity_stats[rarity]
        attack = random.randint(*stat_ranges["attack"])
        defense = random.randint(*stat_ranges["defense"])
        speed = random.randint(*stat_ranges["speed"])
        skill_mp_cost = random.randint(*stat_ranges["skill_mp_cost"])
        critical_rate = random.uniform(*stat_ranges["critical_rate"])
        dodge_rate = random.uniform(*stat_ranges["dodge_rate"])
        
        # Generate skill name
        element_words = self.skill_patterns.get(element, ["Mysterious"])
        effect_word = random.choice(self.skill_effects)
        if random.random() < 0.5:
            skill_name = f"{random.choice(element_words)} {effect_word}"
        else:
            skill_name = f"{effect_word} of {random.choice(element_words)}"
        
        # Determine skill type based on stats
        if attack > defense * 1.2:
            skill_type = "damage"
        elif defense > attack * 1.2:
            skill_type = "buff" if random.random() < 0.6 else "healing"
        else:
            skill_type = random.choice(["damage", "buff", "debuff", "status"])
        
        # Generate skill description
        description_template = random.choice(self.skill_descriptions[skill_type])
        
        # Fill in template with appropriate values
        skill_description = description_template.format(
            element=element,
            chance=random.randint(20, 80),
            status=self.status_effects.get(element, "weakened"),
            effect="deals significant damage" if skill_type == "damage" else "increases defense for 2 turns",
            amount=random.randint(20, 40),
            bonus="a defensive shield" if random.random() < 0.5 else "increased speed",
            stat=random.choice(["attack", "defense", "speed", "critical rate"]),
            duration=random.randint(2, 4)
        )
        
        # Generate generic name (for random cards)
        prefixes = ["Mystic", "Ancient", "Heroic", "Legendary", "Divine", "Shadow", "Celestial", "Royal"]
        suffixes = ["Warrior", "Mage", "Guardian", "Knight", "Sorcerer", "Hunter", "Paladin", "Summoner"]
        name = f"{random.choice(prefixes)} {element} {random.choice(suffixes)}"
        
        # Generate card data
        card_data = {
            "base_card_id": None,  # No base card since it's random
            "name": name,
            "rarity": rarity,
            "attack": attack,
            "defense": defense,
            "speed": speed,
            "element": element,
            "skill": skill_name,
            "skill_description": skill_description,
            "skill_mp_cost": skill_mp_cost,
            "skill_cooldown": random.randint(2, 5),
            "critical_rate": critical_rate,
            "dodge_rate": dodge_rate,
            "level": 1,
            "xp": 0,
            "equipped": 0,
            "evolution_stage": 0,
            "image_url": None  # No image for random cards
        }
        
        return card_data
    
    def create_user_card(self, user_id, card_data):
        """
        Create a new card for a user based on generated card data
        
        Args:
            user_id (int): Discord user ID
            card_data (dict): Card data generated from template or random
            
        Returns:
            int: ID of the newly created card
        """
        # Insert card into user's collection
        self.cursor.execute("""
            INSERT INTO usercards (
                user_id, base_card_id, name, rarity, attack, defense, speed,
                element, skill, skill_description, skill_mp_cost, skill_cooldown,
                critical_rate, dodge_rate, level, xp, equipped, evolution_stage, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            card_data.get("base_card_id"),
            card_data["name"],
            card_data["rarity"],
            card_data["attack"],
            card_data["defense"],
            card_data["speed"],
            card_data["element"],
            card_data["skill"],
            card_data["skill_description"],
            card_data["skill_mp_cost"],
            card_data["skill_cooldown"],
            card_data["critical_rate"],
            card_data["dodge_rate"],
            card_data["level"],
            card_data["xp"],
            card_data["equipped"],
            card_data["evolution_stage"],
            card_data["image_url"]
        ))
        
        self.db.conn.commit()
        
        # Return the ID of the new card
        return self.cursor.lastrowid
    
    def generate_boss(self, name, level, element=None):
        """
        Generate a boss with appropriate stats
        
        Args:
            name (str): Boss name
            level (int): Boss level
            element (str, optional): Boss element, random if None
            
        Returns:
            dict: Boss data
        """
        # Choose random element if not specified
        if element is None:
            element = random.choice(self.elements)
        
        # Base stats scaled by level
        hp = 1000 + (level * 50)
        attack = 100 + (level * 6)
        defense = 100 + (level * 5)
        speed = 50 + (level * 3)
        
        # Generate skill
        element_words = self.skill_patterns.get(element, ["Mysterious"])
        effect_word = random.choice(self.skill_effects)
        skill_name = f"Boss {random.choice(element_words)} {effect_word}"
        
        # Generate skill description
        skill_template = random.choice(self.skill_descriptions["damage"])
        skill_description = skill_template.format(
            element=element,
            chance=random.randint(30, 90),
            status=self.status_effects.get(element, "weakened"),
            effect="deals massive damage" if random.random() < 0.7 else "has a chance to instantly defeat weaker opponents",
            amount=random.randint(20, 50),
            bonus="increased defense",
            stat="all stats",
            duration=3
        )
        
        # Generate lore
        lore_templates = [
            "A fearsome {element} boss that rules over the {location}.",
            "This legendary creature has terrorized the {location} for centuries with its {element} powers.",
            "A powerful {element} entity summoned by dark magic to guard the {location}.",
            "Once a normal being, now corrupted by {element} energy into a monstrous form."
        ]
        
        locations = [
            "ancient ruins", "forbidden forest", "volcanic mountains", "frozen tundra", 
            "deep ocean", "stormy peaks", "shadow realm", "celestial plains"
        ]
        
        lore = random.choice(lore_templates).format(element=element, location=random.choice(locations))
        
        # Boss data
        boss_data = {
            "name": name,
            "level": level,
            "hp": hp,
            "attack": attack,
            "defense": defense,
            "speed": speed,
            "element": element,
            "skill": skill_name,
            "skill_description": skill_description,
            "lore": lore,
            "min_player_level": max(1, level - 5),
            "reward_gold": 100 + (level * 20),
            "reward_xp": 50 + (level * 10)
        }
        
        return boss_data
