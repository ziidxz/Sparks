"""
Initialize the database with anime cards from various series.
This script creates cards with unique skills and abilities.
"""

import sqlite3

conn = sqlite3.connect("database/sparks.db")
import random
import os

# Card rarity levels
RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]

# Elements for cards
ELEMENTS = ["Fire", "Water", "Earth", "Air", "Electric", "Ice", "Light", "Dark", "Cute", "Sweet", "Star"]

# Anime series with their characters
ANIME_SERIES = {
    "Naruto": {
        "characters": [
            {"name": "Naruto Uzumaki", "skill": "Shadow Clone", "skill_description": "Create shadow clones to attack multiple enemies", "element": "Air"},
            {"name": "Sasuke Uchiha", "skill": "Sharingan", "skill_description": "High chance to dodge attacks and counter", "element": "Fire"},
            {"name": "Sakura Haruno", "skill": "Chakra Control", "skill_description": "Heal a portion of HP", "element": "Earth"},
            {"name": "Kakashi Hatake", "skill": "Copy Ninja", "skill_description": "Copy opponent's last skill", "element": "Electric"},
            {"name": "Itachi Uchiha", "skill": "Tsukuyomi", "skill_description": "Stun enemy for 1 turn", "element": "Dark"},
            {"name": "Hinata Hyuga", "skill": "Gentle Fist", "skill_description": "Reduce enemy defense", "element": "Air"},
            {"name": "Rock Lee", "skill": "Eight Gates", "skill_description": "Double ATK for 2 turns", "element": "Earth"},
            {"name": "Gaara", "skill": "Sand Shield", "skill_description": "Block next attack", "element": "Earth"},
            {"name": "Jiraiya", "skill": "Sage Mode", "skill_description": "Boost all stats temporarily", "element": "Earth"},
            {"name": "Tsunade", "skill": "Creation Rebirth", "skill_description": "Fully restore HP once per battle", "element": "Earth"},
        ]
    },
    "One Piece": {
        "characters": [
            {"name": "Monkey D. Luffy", "skill": "Gum-Gum Pistol", "skill_description": "High damage single attack", "element": "Star"},
            {"name": "Roronoa Zoro", "skill": "Three Sword Style", "skill_description": "Attack three times", "element": "Air"},
            {"name": "Nami", "skill": "Weather Tempo", "skill_description": "Chance to stun all enemies", "element": "Electric"},
            {"name": "Sanji", "skill": "Diable Jambe", "skill_description": "Fire damage and burn effect", "element": "Fire"},
            {"name": "Tony Tony Chopper", "skill": "Rumble Ball", "skill_description": "Transform and gain different abilities", "element": "Cute"},
            {"name": "Nico Robin", "skill": "Clutch", "skill_description": "Hold enemy in place for 1 turn", "element": "Dark"},
            {"name": "Franky", "skill": "Radical Beam", "skill_description": "Piercing damage", "element": "Electric"},
            {"name": "Brook", "skill": "Soul Solid", "skill_description": "Freeze enemy for 1 turn", "element": "Ice"},
            {"name": "Jinbe", "skill": "Fish-Man Karate", "skill_description": "Deal water damage to enemy", "element": "Water"},
            {"name": "Trafalgar Law", "skill": "Room", "skill_description": "Switch positions with enemy", "element": "Dark"},
        ]
    },
    "My Hero Academia": {
        "characters": [
            {"name": "Izuku Midoriya", "skill": "One For All", "skill_description": "Increase ATK and SPD", "element": "Air"},
            {"name": "Katsuki Bakugo", "skill": "Explosion", "skill_description": "Area damage to all enemies", "element": "Fire"},
            {"name": "Shoto Todoroki", "skill": "Half Cold Half Hot", "skill_description": "Deal both fire and ice damage", "element": "Ice"},
            {"name": "Ochaco Uraraka", "skill": "Zero Gravity", "skill_description": "Enemy skips next turn", "element": "Air"},
            {"name": "All Might", "skill": "Detroit Smash", "skill_description": "Massive single target damage", "element": "Star"},
            {"name": "Tenya Iida", "skill": "Recipro Burst", "skill_description": "First attack in battle does extra damage", "element": "Electric"},
            {"name": "Momo Yaoyorozu", "skill": "Creation", "skill_description": "Generate a random item effect", "element": "Light"},
            {"name": "Tsuyu Asui", "skill": "Frog", "skill_description": "High dodge chance", "element": "Water"},
            {"name": "Endeavor", "skill": "Hellflame", "skill_description": "Deals damage over time with burns", "element": "Fire"},
            {"name": "Eraserhead", "skill": "Erasure", "skill_description": "Disable enemy special abilities", "element": "Dark"},
        ]
    },
    "Dragon Ball": {
        "characters": [
            {"name": "Goku", "skill": "Kamehameha", "skill_description": "Charge up for a powerful attack", "element": "Light"},
            {"name": "Vegeta", "skill": "Final Flash", "skill_description": "High damage when HP is low", "element": "Electric"},
            {"name": "Piccolo", "skill": "Special Beam Cannon", "skill_description": "Piercing attack ignores DEF", "element": "Earth"},
            {"name": "Gohan", "skill": "Father-Son Kamehameha", "skill_description": "More powerful when allies are defeated", "element": "Light"},
            {"name": "Frieza", "skill": "Death Ball", "skill_description": "Damage increases each turn", "element": "Dark"},
            {"name": "Trunks", "skill": "Burning Attack", "skill_description": "Chance to critical hit", "element": "Fire"},
            {"name": "Android 18", "skill": "Energy Absorption", "skill_description": "Steal MP from enemy", "element": "Electric"},
            {"name": "Beerus", "skill": "Hakai", "skill_description": "Chance to instantly defeat enemy", "element": "Star"},
            {"name": "Whis", "skill": "Time Reversal", "skill_description": "Undo the last turn", "element": "Star"},
            {"name": "Jiren", "skill": "Power of Trust", "skill_description": "Ignore status effects", "element": "Fire"},
        ]
    },
    "Demon Slayer": {
        "characters": [
            {"name": "Tanjiro Kamado", "skill": "Water Breathing", "skill_description": "Multi-hit combo attack", "element": "Water"},
            {"name": "Nezuko Kamado", "skill": "Blood Demon Art", "skill_description": "Heal and remove debuffs", "element": "Fire"},
            {"name": "Zenitsu Agatsuma", "skill": "Thunder Breathing", "skill_description": "High speed first strike", "element": "Electric"},
            {"name": "Inosuke Hashibira", "skill": "Beast Breathing", "skill_description": "Unpredictable attack pattern", "element": "Earth"},
            {"name": "Giyu Tomioka", "skill": "Water Hashira", "skill_description": "Counter enemy attacks", "element": "Water"},
            {"name": "Shinobu Kocho", "skill": "Insect Breathing", "skill_description": "Poison enemy over time", "element": "Cute"},
            {"name": "Kyojuro Rengoku", "skill": "Flame Hashira", "skill_description": "Increasing damage each turn", "element": "Fire"},
            {"name": "Muzan Kibutsuji", "skill": "Blood Demon", "skill_description": "Drain HP from enemy", "element": "Dark"},
            {"name": "Akaza", "skill": "Compass Needle", "skill_description": "Predict and counter enemy attacks", "element": "Air"},
            {"name": "Kanao Tsuyuri", "skill": "Flower Breathing", "skill_description": "Increase critical hit chance", "element": "Sweet"},
        ]
    },
    "Attack on Titan": {
        "characters": [
            {"name": "Eren Yeager", "skill": "Titan Transformation", "skill_description": "Transform to increase all stats", "element": "Earth"},
            {"name": "Mikasa Ackerman", "skill": "Ackerman Strength", "skill_description": "High damage and critical chance", "element": "Air"},
            {"name": "Armin Arlert", "skill": "Colossal Strategy", "skill_description": "Increase party ATK and DEF", "element": "Light"},
            {"name": "Levi Ackerman", "skill": "Captain's Fury", "skill_description": "Multiple high-speed attacks", "element": "Air"},
            {"name": "Historia Reiss", "skill": "Royal Command", "skill_description": "Boost party morale, increasing stats", "element": "Light"},
            {"name": "Annie Leonhart", "skill": "Female Titan", "skill_description": "Crystallize to block damage", "element": "Ice"},
            {"name": "Reiner Braun", "skill": "Armored Defense", "skill_description": "Greatly reduce incoming damage", "element": "Earth"},
            {"name": "Hange Zoe", "skill": "Scientific Analysis", "skill_description": "Reveal enemy weaknesses", "element": "Light"},
            {"name": "Erwin Smith", "skill": "Charge!", "skill_description": "Rally allies for coordinated attack", "element": "Star"},
            {"name": "Beast Titan", "skill": "Projectile Barrage", "skill_description": "Attack all enemies at once", "element": "Earth"},
        ]
    },
    "Pokemon": {
        "characters": [
            {"name": "Pikachu", "skill": "Thunderbolt", "skill_description": "Electric damage with chance to stun", "element": "Electric"},
            {"name": "Charizard", "skill": "Flamethrower", "skill_description": "Fire damage with burn effect", "element": "Fire"},
            {"name": "Blastoise", "skill": "Hydro Pump", "skill_description": "High damage water attack", "element": "Water"},
            {"name": "Venusaur", "skill": "Solar Beam", "skill_description": "Charge up for a powerful attack", "element": "Earth"},
            {"name": "Mewtwo", "skill": "Psychic", "skill_description": "Mental attack that lowers enemy stats", "element": "Light"},
            {"name": "Snorlax", "skill": "Rest", "skill_description": "Recover HP but skip a turn", "element": "Cute"},
            {"name": "Gengar", "skill": "Shadow Ball", "skill_description": "Ghost attack that ignores defense", "element": "Dark"},
            {"name": "Gyarados", "skill": "Hyper Beam", "skill_description": "Powerful attack but needs to recharge", "element": "Water"},
            {"name": "Dragonite", "skill": "Dragon Rush", "skill_description": "Powerful attack with stun chance", "element": "Air"},
            {"name": "Jigglypuff", "skill": "Sing", "skill_description": "Put enemy to sleep for 1-3 turns", "element": "Cute"},
        ]
    },
    "Jujutsu Kaisen": {
        "characters": [
            {"name": "Yuji Itadori", "skill": "Divergent Fist", "skill_description": "Follow-up attack after basic attack", "element": "Earth"},
            {"name": "Megumi Fushiguro", "skill": "Ten Shadows", "skill_description": "Summon a random shikigami to assist", "element": "Dark"},
            {"name": "Nobara Kugisaki", "skill": "Resonance", "skill_description": "Damage increases with consecutive hits", "element": "Earth"},
            {"name": "Satoru Gojo", "skill": "Infinity", "skill_description": "High chance to negate attacks", "element": "Star"},
            {"name": "Sukuna", "skill": "Dismantle", "skill_description": "Cut through any defense", "element": "Dark"},
            {"name": "Maki Zenin", "skill": "Cursed Tools", "skill_description": "Attack with different weapon each turn", "element": "Earth"},
            {"name": "Yuta Okkotsu", "skill": "Copy", "skill_description": "Use an enemy's skill against them", "element": "Dark"},
            {"name": "Toge Inumaki", "skill": "Cursed Speech", "skill_description": "Command enemies to perform actions", "element": "Air"},
            {"name": "Kento Nanami", "skill": "Ratio Technique", "skill_description": "Find weak points for critical hits", "element": "Light"},
            {"name": "Aoi Todo", "skill": "Boogie Woogie", "skill_description": "Switch positions with ally or enemy", "element": "Electric"},
        ]
    },
    "Sailor Moon": {
        "characters": [
            {"name": "Sailor Moon", "skill": "Moon Tiara Action", "skill_description": "Purify and damage enemies", "element": "Light"},
            {"name": "Sailor Mercury", "skill": "Shine Aqua Illusion", "skill_description": "Freeze enemies and reduce speed", "element": "Water"},
            {"name": "Sailor Mars", "skill": "Fire Soul", "skill_description": "Burn enemies with sacred fire", "element": "Fire"},
            {"name": "Sailor Jupiter", "skill": "Supreme Thunder", "skill_description": "Electric damage to all enemies", "element": "Electric"},
            {"name": "Sailor Venus", "skill": "Love Chain", "skill_description": "Bind enemy and prevent escape", "element": "Light"},
            {"name": "Tuxedo Mask", "skill": "Rose Throw", "skill_description": "Distract enemy and increase dodge", "element": "Earth"},
            {"name": "Sailor Saturn", "skill": "Silence Glaive", "skill_description": "Massive damage at HP cost", "element": "Dark"},
            {"name": "Sailor Pluto", "skill": "Time Stop", "skill_description": "Skip enemy turn but high MP cost", "element": "Dark"},
            {"name": "Sailor Uranus", "skill": "World Shaking", "skill_description": "Earth-based area damage", "element": "Earth"},
            {"name": "Sailor Neptune", "skill": "Deep Submerge", "skill_description": "Water-based area damage", "element": "Water"},
        ]
    },
    "Fullmetal Alchemist": {
        "characters": [
            {"name": "Edward Elric", "skill": "Alchemy", "skill_description": "Transform battlefield for advantage", "element": "Earth"},
            {"name": "Alphonse Elric", "skill": "Soul Armor", "skill_description": "High defense and counterattack", "element": "Earth"},
            {"name": "Roy Mustang", "skill": "Flame Alchemy", "skill_description": "Precise fire attack with burn effect", "element": "Fire"},
            {"name": "Riza Hawkeye", "skill": "Hawk's Eye", "skill_description": "Never miss an attack", "element": "Air"},
            {"name": "Alex Armstrong", "skill": "Artistic Alchemy", "skill_description": "Area damage with stun chance", "element": "Earth"},
            {"name": "Olivier Armstrong", "skill": "Northern Wall", "skill_description": "Increase party defense", "element": "Ice"},
            {"name": "Ling Yao", "skill": "Chi Sensing", "skill_description": "Increase dodge and counter chance", "element": "Light"},
            {"name": "King Bradley", "skill": "Ultimate Eye", "skill_description": "Multiple precision strikes", "element": "Dark"},
            {"name": "Scar", "skill": "Destruction Alchemy", "skill_description": "Destroy enemy equipment or barriers", "element": "Earth"},
            {"name": "Greed", "skill": "Ultimate Shield", "skill_description": "Activate shield that absorbs damage", "element": "Dark"},
        ]
    },
}

def get_stat_range(rarity):
    """Return base stat ranges based on card rarity."""
    base_ranges = {
        "Common": {"min": 20, "max": 40},
        "Uncommon": {"min": 35, "max": 55},
        "Rare": {"min": 50, "max": 70},
        "Epic": {"min": 65, "max": 85},
        "Legendary": {"min": 80, "max": 100}
    }
    return base_ranges.get(rarity, {"min": 20, "max": 40})

def generate_anime_cards(cursor):
    """Generate cards for all anime series and insert into database."""
    # Check if table exists and has data
    try:
        cursor.execute("SELECT COUNT(*) FROM api_cards")
        card_count = cursor.fetchone()[0]
    except Exception as e:
        print(f"Error checking card count: {e}")
        # Table might not exist yet
        card_count = 0
    
    if card_count > 0:
        print(f"Database already has {card_count} cards. Skipping initialization.")
        return 0
    
    print("Generating anime cards for the database...")
    cards_added = 0
    
    # Generate cards for each anime series
    for series, data in ANIME_SERIES.items():
        for character in data["characters"]:
            # Create each character in multiple rarities
            for rarity in RARITIES:
                card_name = f"{character['name']} ({rarity})"
                
                # Generate stats based on rarity
                stat_range = get_stat_range(rarity)
                attack = random.randint(stat_range["min"], stat_range["max"])
                defense = random.randint(stat_range["min"], stat_range["max"])
                speed = random.randint(stat_range["min"], stat_range["max"])
                
                # Adjust MP cost based on rarity
                mp_cost = 5 + (RARITIES.index(rarity) * 5)  # 5, 10, 15, 20, 25
                
                # Insert card into database
                cursor.execute('''
                INSERT INTO api_cards (
                    name, rarity, attack, defense, speed, element, skill, 
                    skill_description, anime_series, mp_cost, evo_stage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 5)
                ''', (
                    card_name, rarity, attack, defense, speed, 
                    character["element"], character["skill"],
                    character["skill_description"], series, mp_cost
                ))
                
                cards_added += 1
    
    print(f"Added {cards_added} anime character cards to the database.")
    return cards_added


def initialize_db():
    """Initialize the database with anime cards if not already present."""
    try:
        conn = sqlite3.connect("database/sparks.db")
        cursor = conn.cursor()
        
        # Some database operation
        conn.commit()

        return True  # ✅ Correctly inside function

    except Exception as e:  
        print(f"Error initializing database: {e}")
        return False  # ✅ Correctly inside function

    finally:
        conn.close()  # ✅ Ensures connection is closed

if __name__ == "__main__":
    initialize_db()