"""
Comprehensive anime card database with characters from popular anime series.
Each character has unique skills based on their characteristics in the anime.
"""

import sqlite3
import random
import os

RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
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
        ]
    },
    "Death Note": {
        "characters": [
            {"name": "Light Yagami", "skill": "Death Note", "skill_description": "Chance to instantly defeat non-boss enemy", "element": "Dark"},
            {"name": "L", "skill": "Deduction", "skill_description": "Reveal enemy weakness", "element": "Light"},
            {"name": "Ryuk", "skill": "Shinigami Eyes", "skill_description": "See enemy remaining HP", "element": "Dark"},
            {"name": "Misa Amane", "skill": "Second Kira", "skill_description": "Support attack with death chance", "element": "Dark"},
            {"name": "Near", "skill": "Puzzle Master", "skill_description": "Predict and counter enemy moves", "element": "Light"},
            {"name": "Mello", "skill": "Criminal Network", "skill_description": "Call allies for support attacks", "element": "Dark"},
            {"name": "Watari", "skill": "Resources", "skill_description": "Provide random buff or item", "element": "Light"},
            {"name": "Soichiro Yagami", "skill": "Justice", "skill_description": "Sacrifice HP for powerful attack", "element": "Light"},
        ]
    },
    "Your Lie in April": {
        "characters": [
            {"name": "Kousei Arima", "skill": "Piano Prodigy", "skill_description": "Heal party and remove debuffs", "element": "Water"},
            {"name": "Kaori Miyazono", "skill": "Vibrant Violin", "skill_description": "Boost party stats with music", "element": "Light"},
            {"name": "Tsubaki Sawabe", "skill": "Unwavering Support", "skill_description": "Take damage for allies", "element": "Earth"},
            {"name": "Ryota Watari", "skill": "Soccer Star", "skill_description": "Quick attack with high accuracy", "element": "Air"},
            {"name": "Emi Igawa", "skill": "Competitive Spirit", "skill_description": "Damage increases when HP is low", "element": "Fire"},
            {"name": "Takeshi Aiza", "skill": "Piano Rival", "skill_description": "Copy enemy buffs", "element": "Water"},
            {"name": "Nagi Aiza", "skill": "Young Talent", "skill_description": "Unpredictable attack pattern", "element": "Cute"},
            {"name": "Hiroko Seto", "skill": "Mentor's Guidance", "skill_description": "Boost a random ally's stats", "element": "Light"},
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
    # First, clear existing cards if needed
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_cards'")
    if cursor.fetchone():
        print("Generating anime cards for the database...")
    else:
        # Create cards table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rarity TEXT NOT NULL,
            attack INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            speed INTEGER NOT NULL,
            element TEXT NOT NULL,
            skill TEXT NOT NULL,
            skill_description TEXT NOT NULL,
            image_url TEXT,
            anime_series TEXT NOT NULL,
            mp_cost INTEGER DEFAULT 10,
            evo_stage INTEGER DEFAULT 1,
            max_evo INTEGER DEFAULT 5
        )
        ''')
    
    # Keep track of inserted cards to avoid duplicates
    cursor.execute("SELECT name, rarity FROM api_cards")
    existing_cards = {(name, rarity) for name, rarity in cursor.fetchall()}
    
    card_count = 0
    
    # Generate cards for each anime series
    for series, data in ANIME_SERIES.items():
        for character in data["characters"]:
            # Create each character in multiple rarities
            for rarity in RARITIES:
                card_name = f"{character['name']} ({rarity})"
                
                # Skip if this exact card name and rarity already exists
                if (card_name, rarity) in existing_cards:
                    continue
                
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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    card_name, rarity, attack, defense, speed, 
                    character["element"], character["skill"],
                    character["skill_description"], series, mp_cost
                ))
                
                card_count += 1
    
    print(f"Added {card_count} anime character cards to the database.")
    return card_count

def initialize_card_database(db_path='database/sparks.db'):
    """Initialize the card database with anime characters."""
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Generate cards
    cards_added = generate_anime_cards(cursor)
    
    # Commit changes and close
    conn.commit()
    conn.close()
    
    return cards_added

if __name__ == "__main__":
    # This can be run directly to initialize the database
    initialize_card_database()