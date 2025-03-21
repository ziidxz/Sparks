# Sanrio and kawaii character cards
cards_list = [
    {
        "name": "Hello Kitty",
        "attack": 120,
        "defense": 80,
        "speed": 65,
        "element": "Cute",
        "rarity": "Legendary",
        "skill": "Kitty Charm",
        "skill_description": "Charms opponents, reducing their attack by 30% for 2 turns.",
        "skill_mp_cost": 30,
        "skill_cooldown": 3,
        "critical_rate": 10.0,
        "dodge_rate": 8.0,
        "lore": "A beloved icon who spreads happiness and friendship everywhere she goes.",
        "image_url": "https://cdn.discordapp.com/attachments/1352297041643966584/1352297100133793802/illust_128109944_20250320_220439.png",
        "evolvable": 1
    },
    {
        "name": "My Melody",
        "attack": 100,
        "defense": 90,
        "speed": 80,
        "element": "Sweet",
        "rarity": "Epic",
        "skill": "Melodic Heal",
        "skill_description": "Heals 25% of max HP and increases defense by 20% for 2 turns.",
        "skill_mp_cost": 35,
        "skill_cooldown": 3,
        "critical_rate": 7.0,
        "dodge_rate": 12.0,
        "lore": "A kind and gentle rabbit who heals allies with her songs of compassion.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/mymelody.png",
        "evolvable": 1
    },
    {
        "name": "Kuromi",
        "attack": 140,
        "defense": 70,
        "speed": 85,
        "element": "Dark",
        "rarity": "Epic",
        "skill": "Rebel Strike",
        "skill_description": "Deals damage with a 40% chance to stun the opponent for 1 turn.",
        "skill_mp_cost": 25,
        "skill_cooldown": 3,
        "critical_rate": 15.0,
        "dodge_rate": 7.0,
        "lore": "A mischievous rival of My Melody with a punk attitude and rebellious spirit.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/kuromi.png",
        "evolvable": 1
    },
    {
        "name": "Cinnamoroll",
        "attack": 110,
        "defense": 100,
        "speed": 95,
        "element": "Air",
        "rarity": "Rare",
        "skill": "Cloud Ride",
        "skill_description": "Soars into the air, increasing dodge rate by 50% for 2 turns.",
        "skill_mp_cost": 20,
        "skill_cooldown": 3,
        "critical_rate": 8.0,
        "dodge_rate": 15.0,
        "lore": "A fluffy white puppy who can fly using his large ears and loves cinnamon rolls.",
        "image_url": "https://cdn.discordapp.com/attachments/1352297041643966584/1352297100133793802/illust_128109944_20250320_220439.png",
        "evolvable": 1
    },
    {
        "name": "Pompompurin",
        "attack": 130,
        "defense": 85,
        "speed": 60,
        "element": "Earth",
        "rarity": "Rare",
        "skill": "Golden Slam",
        "skill_description": "Slams into opponents with 30% chance to break their defense.",
        "skill_mp_cost": 25,
        "skill_cooldown": 3,
        "critical_rate": 12.0,
        "dodge_rate": 5.0,
        "lore": "A golden retriever who loves pudding and taking naps. Don't be fooled by his cuteness!",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/pompompurin.png",
        "evolvable": 1
    },
    {
        "name": "Keroppi",
        "attack": 90,
        "defense": 110,
        "speed": 100,
        "element": "Water",
        "rarity": "Uncommon",
        "skill": "Lily Pad Leap",
        "skill_description": "Jumps swiftly to avoid attacks and counterattack with increased speed.",
        "skill_mp_cost": 20,
        "skill_cooldown": 2,
        "critical_rate": 7.0,
        "dodge_rate": 18.0,
        "lore": "A cheerful frog who lives in Donut Pond and loves adventures with his friends.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/keroppi.png",
        "evolvable": 1
    },
    {
        "name": "Tuxedosam",
        "attack": 100,
        "defense": 95,
        "speed": 75,
        "element": "Ice",
        "rarity": "Uncommon",
        "skill": "Penguin Slide",
        "skill_description": "Slides on ice to deal damage and slow down opponents by 30%.",
        "skill_mp_cost": 20,
        "skill_cooldown": 3,
        "critical_rate": 8.0,
        "dodge_rate": 10.0,
        "lore": "A dapper penguin who glides effortlessly on ice and always dresses formally.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/tuxedosam.png",
        "evolvable": 1
    },
    {
        "name": "Badtz-Maru",
        "attack": 125,
        "defense": 75,
        "speed": 80,
        "element": "Dark",
        "rarity": "Rare",
        "skill": "Attitude Punch",
        "skill_description": "Unleashes a powerful punch with attitude, dealing extra damage to Light elements.",
        "skill_mp_cost": 25,
        "skill_cooldown": 3,
        "critical_rate": 15.0,
        "dodge_rate": 8.0,
        "lore": "A rebellious penguin with a knack for causing trouble and a signature sassy attitude.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/badtzmaru.png",
        "evolvable": 1
    },
    {
        "name": "Chococat",
        "attack": 115,
        "defense": 85,
        "speed": 90,
        "element": "Electric",
        "rarity": "Uncommon",
        "skill": "Static Fur",
        "skill_description": "Charges fur with electricity, dealing damage and potentially paralyzing opponents.",
        "skill_mp_cost": 25,
        "skill_cooldown": 3,
        "critical_rate": 10.0,
        "dodge_rate": 10.0,
        "lore": "A tech-savvy cat whose whiskers can sense things from miles away.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/chococat.png",
        "evolvable": 1
    },
    {
        "name": "Little Twin Stars - Kiki",
        "attack": 105,
        "defense": 95,
        "speed": 85,
        "element": "Star",
        "rarity": "Epic",
        "skill": "Star Shine",
        "skill_description": "Calls upon the stars to deal damage to all opponents and boost attack.",
        "skill_mp_cost": 30,
        "skill_cooldown": 4,
        "critical_rate": 12.0,
        "dodge_rate": 7.0,
        "lore": "A celestial being who descended from the stars to fulfill his dream of becoming a poet.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/kiki.png",
        "evolvable": 1
    },
    {
        "name": "Little Twin Stars - Lala",
        "attack": 95,
        "defense": 105,
        "speed": 85,
        "element": "Star",
        "rarity": "Epic",
        "skill": "Moonlight Wish",
        "skill_description": "Bathes allies in moonlight, healing and removing negative status effects.",
        "skill_mp_cost": 35,
        "skill_cooldown": 4,
        "critical_rate": 7.0,
        "dodge_rate": 12.0,
        "lore": "A kind-hearted celestial being who loves to play the piano and bring sweet dreams.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/lala.png",
        "evolvable": 1
    },
    {
        "name": "Gudetama",
        "attack": 70,
        "defense": 130,
        "speed": 40,
        "element": "Lazy",
        "rarity": "Rare",
        "skill": "Lethargy Shield",
        "skill_description": "Creates a shield of laziness that absorbs 70% of incoming damage for 3 turns.",
        "skill_mp_cost": 20,
        "skill_cooldown": 5,
        "critical_rate": 3.0,
        "dodge_rate": 20.0,
        "lore": "A lazy egg who refuses to fight, but is surprisingly hard to defeat due to apathy.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/gudetama.png",
        "evolvable": 1
    },
    {
        "name": "Aggretsuko",
        "attack": 150,
        "defense": 60,
        "speed": 70,
        "element": "Fire",
        "rarity": "Rare",
        "skill": "Death Metal Rage",
        "skill_description": "Unleashes inner rage through death metal, dealing massive fire damage to opponents.",
        "skill_mp_cost": 35,
        "skill_cooldown": 4,
        "critical_rate": 20.0,
        "dodge_rate": 5.0,
        "lore": "An office worker red panda who releases stress through death metal karaoke.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/aggretsuko.png",
        "evolvable": 1
    },
    {
        "name": "Pochacco",
        "attack": 100,
        "defense": 90,
        "speed": 120,
        "element": "Air",
        "rarity": "Uncommon",
        "skill": "Sporty Dash",
        "skill_description": "Dashes with incredible speed, striking first and potentially dodging the next attack.",
        "skill_mp_cost": 20,
        "skill_cooldown": 3,
        "critical_rate": 10.0,
        "dodge_rate": 15.0,
        "lore": "An athletic puppy who loves sports and is always full of energy.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/pochacco.png",
        "evolvable": 1
    },
    {
        "name": "Jewelpet Ruby",
        "attack": 110,
        "defense": 85,
        "speed": 90,
        "element": "Fire",
        "rarity": "Uncommon",
        "skill": "Ruby Flame",
        "skill_description": "Summons flames that burn opponents for 3 turns, dealing damage over time.",
        "skill_mp_cost": 25,
        "skill_cooldown": 3,
        "critical_rate": 12.0,
        "dodge_rate": 8.0,
        "lore": "A white rabbit with ruby eyes who can cast magic spells related to luck and courage.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/jewelpet_ruby.png",
        "evolvable": 1
    },
    {
        "name": "Cinnamoroll - Alpha Flight",
        "attack": 140,
        "defense": 120,
        "speed": 150,
        "element": "Air",
        "rarity": "Legendary",
        "skill": "Stratosphere Dive",
        "skill_description": "Soars to extreme heights then dives at supersonic speed, dealing massive damage with 40% stun chance.",
        "skill_mp_cost": 40,
        "skill_cooldown": 5,
        "critical_rate": 15.0,
        "dodge_rate": 20.0,
        "lore": "The ultimate evolved form of Cinnamoroll, capable of flying at supersonic speeds and creating cyclones.",
        "image_url": "https://media.discordapp.net/attachments/1352297041643966584/1352300505627492413/illust_125255189_20250320_221910.png",
        "evolvable": 0
    }
]

# Store evolution data
evolution_data = {
    # Base cards that can evolve, with their evolution requirements and results
    "Cinnamoroll": {
        "base_card_id": 4,  # Matches the position in cards_list (0-indexed)
        "stages": {
            # Stage 0 to 1 evolution
            0: {
                "materials": [
                    {"material_id": 9, "quantity": 2},  # Elemental Core: Air
                    {"material_id": 3, "quantity": 3}   # Star Fragment
                ],
                "gold_cost": 2000,
                "result": {
                    "new_name": "Nimbus Cinnamoroll",
                    "attack_boost": 15,
                    "defense_boost": 10,
                    "speed_boost": 20,
                    "new_skill": "Nimbus Dash",
                    "new_skill_description": "Rides on clouds to strike with increased speed and create a protective mist that reduces damage.",
                    "new_image_url": None
                }
            },
            # Stage 1 to 2 evolution
            1: {
                "materials": [
                    {"material_id": 9, "quantity": 5},  # Elemental Core: Air
                    {"material_id": 4, "quantity": 2},  # Dragon Scale
                    {"material_id": 5, "quantity": 1}   # Cosmic Dust
                ],
                "gold_cost": 5000,
                "result": {
                    "new_name": "Cinnamoroll - Alpha Flight",
                    "attack_boost": 30,
                    "defense_boost": 20,
                    "speed_boost": 55,
                    "new_skill": "Stratosphere Dive",
                    "new_skill_description": "Soars to extreme heights then dives at supersonic speed, dealing massive damage with 40% stun chance.",
                    "new_image_url": "https://media.discordapp.net/attachments/1352297041643966584/1352300505627492413/illust_125255189_20250320_221910.png"
                }
            }
        }
    },
    "Hello Kitty": {
        "base_card_id": 1,
        "stages": {
            0: {
                "materials": [
                    {"material_id": 2, "quantity": 5},  # Magical Essence
                    {"material_id": 3, "quantity": 3}   # Star Fragment
                ],
                "gold_cost": 3000,
                "result": {
                    "new_name": "Hello Kitty - Pink Champion",
                    "attack_boost": 20,
                    "defense_boost": 15,
                    "speed_boost": 10,
                    "new_skill": "Pink Power Wave",
                    "new_skill_description": "Unleashes a wave of pink energy that damages enemies and boosts allies' morale.",
                    "new_image_url": None
                }
            }
        }
    },
    "Kuromi": {
        "base_card_id": 3,
        "stages": {
            0: {
                "materials": [
                    {"material_id": 11, "quantity": 4},  # Elemental Core: Dark
                    {"material_id": 3, "quantity": 5}    # Star Fragment
                ],
                "gold_cost": 2500,
                "result": {
                    "new_name": "Shadow Kuromi",
                    "attack_boost": 25,
                    "defense_boost": 10,
                    "speed_boost": 15,
                    "new_skill": "Dark Rebellion",
                    "new_skill_description": "Calls upon the power of darkness to deal heavy damage and potentially curse opponents.",
                    "new_image_url": None
                }
            }
        }
    },
    "Gudetama": {
        "base_card_id": 12,
        "stages": {
            0: {
                "materials": [
                    {"material_id": 1, "quantity": 10},  # Crystal Shard
                    {"material_id": 2, "quantity": 3}    # Magical Essence
                ],
                "gold_cost": 1500,
                "result": {
                    "new_name": "Gudetama - Maximum Laziness",
                    "attack_boost": 5,
                    "defense_boost": 50,
                    "speed_boost": -10,  # Actually gets slower!
                    "new_skill": "Ultimate Apathy",
                    "new_skill_description": "Reaches peak laziness, creating an impenetrable shield that reduces all damage by 90% for 2 turns.",
                    "new_image_url": None
                }
            }
        }
    }
}

# Function to be called when module is initialized
async def setup(bot):
    # Access the database to set up evolutions
    db = bot.db
    cursor = db.conn.cursor()
    
    # Function to process all defined evolutions
    def process_evolutions():
        for card_name, evo_data in evolution_data.items():
            base_card_id = evo_data["base_card_id"] + 1  # Adjust for 1-indexed database
            
            # Mark the card as evolvable in the cards table
            cursor.execute("""
                UPDATE cards SET evolvable = 1 WHERE id = ?
            """, (base_card_id,))
            
            # Process each stage's requirements and results
            for stage, stage_data in evo_data["stages"].items():
                # Add evolution requirements
                for material in stage_data["materials"]:
                    cursor.execute("""
                        INSERT OR REPLACE INTO evolution_requirements
                        (base_card_id, evolution_stage, material_id, quantity, gold_cost)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        base_card_id,
                        stage,
                        material["material_id"],
                        material["quantity"],
                        stage_data["gold_cost"]
                    ))
                
                # Add evolution results
                result = stage_data["result"]
                cursor.execute("""
                    INSERT OR REPLACE INTO evolution_results
                    (base_card_id, evolution_stage, new_name, attack_boost, defense_boost, 
                     speed_boost, new_skill, new_skill_description, new_image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    base_card_id,
                    stage,
                    result["new_name"],
                    result["attack_boost"],
                    result["defense_boost"],
                    result["speed_boost"],
                    result["new_skill"],
                    result["new_skill_description"],
                    result["new_image_url"]
                ))
    
    # Insert cards into database if they don't exist
    for i, card in enumerate(cards_list, 1):  # Start from 1 for database ID
        cursor.execute("""
            INSERT OR IGNORE INTO cards
            (id, name, rarity, attack, defense, speed, element, skill, skill_description,
             skill_mp_cost, skill_cooldown, critical_rate, dodge_rate, lore, image_url, evolvable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i,
            card["name"],
            card["rarity"],
            card["attack"],
            card["defense"],
            card["speed"],
            card["element"],
            card["skill"],
            card["skill_description"],
            card["skill_mp_cost"],
            card["skill_cooldown"],
            card["critical_rate"],
            card["dodge_rate"],
            card["lore"],
            card["image_url"],
            card["evolvable"]
        ))
    
    # Process all evolutions
    process_evolutions()
    
    # Commit changes
    db.conn.commit()
