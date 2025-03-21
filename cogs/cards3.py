# One Piece and Dragon Ball character cards
cards_list = [
    # One Piece Characters
    {
        "name": "Monkey D. Luffy",
        "attack": 150,
        "defense": 120,
        "speed": 130,
        "element": "Fire",
        "rarity": "Legendary",
        "skill": "Gear Fourth: Boundman",
        "skill_description": "Activates Gear Fourth, greatly increasing attack power and speed for 3 turns.",
        "skill_mp_cost": 40,
        "skill_cooldown": 5,
        "critical_rate": 15.0,
        "dodge_rate": 12.0,
        "lore": "Captain of the Straw Hat Pirates and user of the Gomu Gomu no Mi, seeking to become King of the Pirates.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/luffy.png",
        "evolvable": 1
    },
    {
        "name": "Roronoa Zoro",
        "attack": 160,
        "defense": 100,
        "speed": 110,
        "element": "Air",
        "rarity": "Epic",
        "skill": "Three Sword Style: Onigiri",
        "skill_description": "Uses all three swords to deliver a powerful slash that can cut through defenses.",
        "skill_mp_cost": 30,
        "skill_cooldown": 3,
        "critical_rate": 20.0,
        "dodge_rate": 8.0,
        "lore": "First mate of the Straw Hat Pirates, master swordsman aiming to become the world's greatest.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/zoro.png",
        "evolvable": 1
    },
    {
        "name": "Nami",
        "attack": 90,
        "defense": 70,
        "speed": 100,
        "element": "Electric",
        "rarity": "Rare",
        "skill": "Thunderbolt Tempo",
        "skill_description": "Uses Clima-Tact to create thunderclouds that strike opponents with lightning.",
        "skill_mp_cost": 25,
        "skill_cooldown": 3,
        "critical_rate": 10.0,
        "dodge_rate": 15.0,
        "lore": "Navigator of the Straw Hat Pirates with a talent for meteorology and stealing.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/nami.png",
        "evolvable": 1
    },
    {
        "name": "Sanji",
        "attack": 140,
        "defense": 90,
        "speed": 150,
        "element": "Fire",
        "rarity": "Epic",
        "skill": "Diable Jambe",
        "skill_description": "Heats leg with friction to deliver flaming kicks that burn opponents for 3 turns.",
        "skill_mp_cost": 30,
        "skill_cooldown": 3,
        "critical_rate": 15.0,
        "dodge_rate": 15.0,
        "lore": "Chef of the Straw Hat Pirates, using only kicks in battle to keep his hands safe for cooking.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/sanji.png",
        "evolvable": 1
    },
    {
        "name": "Nico Robin",
        "attack": 100,
        "defense": 110,
        "speed": 90,
        "element": "Dark",
        "rarity": "Epic",
        "skill": "Cien Fleur: Wing",
        "skill_description": "Sprouts multiple arms to immobilize opponents and deal damage from multiple angles.",
        "skill_mp_cost": 25,
        "skill_cooldown": 3,
        "critical_rate": 12.0,
        "dodge_rate": 10.0,
        "lore": "Archaeologist of the Straw Hat Pirates who ate the Hana Hana no Mi, allowing her to sprout limbs.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/robin.png",
        "evolvable": 1
    },
    {
        "name": "Tony Tony Chopper",
        "attack": 80,
        "defense": 100,
        "speed": 85,
        "element": "Earth",
        "rarity": "Rare",
        "skill": "Monster Point",
        "skill_description": "Transforms into a monster, greatly increasing all stats but losing control for 2 turns.",
        "skill_mp_cost": 35,
        "skill_cooldown": 5,
        "critical_rate": 8.0,
        "dodge_rate": 7.0,
        "lore": "Doctor of the Straw Hat Pirates, a reindeer who ate the Hito Hito no Mi (Human Human Fruit).",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/chopper.png",
        "evolvable": 1
    },
    {
        "name": "Trafalgar Law",
        "attack": 135,
        "defense": 95,
        "speed": 120,
        "element": "Dark",
        "rarity": "Epic",
        "skill": "ROOM: Shambles",
        "skill_description": "Creates a spherical space where he can manipulate anything, swapping opponents' stats.",
        "skill_mp_cost": 35,
        "skill_cooldown": 4,
        "critical_rate": 15.0,
        "dodge_rate": 12.0,
        "lore": "Captain of the Heart Pirates and user of the Ope Ope no Mi, a former Shichibukai and member of the Worst Generation.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/law.png",
        "evolvable": 1
    },
    {
        "name": "Portgas D. Ace",
        "attack": 145,
        "defense": 90,
        "speed": 125,
        "element": "Fire",
        "rarity": "Epic",
        "skill": "Hiken (Fire Fist)",
        "skill_description": "Transforms arm into fire to deliver a powerful flame attack that burns for 3 turns.",
        "skill_mp_cost": 30,
        "skill_cooldown": 3,
        "critical_rate": 15.0,
        "dodge_rate": 10.0,
        "lore": "Son of Gol D. Roger, Luffy's sworn brother, and commander of the Whitebeard Pirates' 2nd Division.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/ace.png",
        "evolvable": 1
    },
    
    # Dragon Ball Characters
    {
        "name": "Goku",
        "attack": 160,
        "defense": 130,
        "speed": 140,
        "element": "Light",
        "rarity": "Legendary",
        "skill": "Kamehameha",
        "skill_description": "Concentrates ki into a powerful beam that deals massive damage to opponents.",
        "skill_mp_cost": 35,
        "skill_cooldown": 3,
        "critical_rate": 15.0,
        "dodge_rate": 10.0,
        "lore": "A Saiyan raised on Earth who constantly trains to be the strongest fighter in the universe.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/goku.png",
        "evolvable": 1
    },
    {
        "name": "Vegeta",
        "attack": 155,
        "defense": 120,
        "speed": 130,
        "element": "Fire",
        "rarity": "Legendary",
        "skill": "Final Flash",
        "skill_description": "Gathers enormous energy to unleash a devastating blast with high critical rate.",
        "skill_mp_cost": 40,
        "skill_cooldown": 4,
        "critical_rate": 20.0,
        "dodge_rate": 8.0,
        "lore": "The Prince of Saiyans who initially came to Earth as an enemy but became one of its greatest defenders.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/vegeta.png",
        "evolvable": 1
    },
    {
        "name": "Gohan",
        "attack": 140,
        "defense": 125,
        "speed": 120,
        "element": "Light",
        "rarity": "Epic",
        "skill": "Father-Son Kamehameha",
        "skill_description": "Channels both his and his father's energy for a powerful Kamehameha that deals massive damage.",
        "skill_mp_cost": 45,
        "skill_cooldown": 5,
        "critical_rate": 15.0,
        "dodge_rate": 10.0,
        "lore": "Son of Goku who possesses incredible hidden potential that surpasses even his father's.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/gohan.png",
        "evolvable": 1
    },
    {
        "name": "Piccolo",
        "attack": 120,
        "defense": 140,
        "speed": 110,
        "element": "Earth",
        "rarity": "Epic",
        "skill": "Special Beam Cannon",
        "skill_description": "Concentrates energy into fingertips to fire a piercing beam that ignores defense.",
        "skill_mp_cost": 35,
        "skill_cooldown": 3,
        "critical_rate": 15.0,
        "dodge_rate": 12.0,
        "lore": "A Namekian who was initially Goku's enemy but became a mentor to Gohan and a defender of Earth.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/piccolo.png",
        "evolvable": 1
    },
    {
        "name": "Frieza",
        "attack": 150,
        "defense": 110,
        "speed": 125,
        "element": "Dark",
        "rarity": "Epic",
        "skill": "Death Ball",
        "skill_description": "Creates a concentrated ball of energy capable of destroying planets and dealing massive damage.",
        "skill_mp_cost": 40,
        "skill_cooldown": 4,
        "critical_rate": 15.0,
        "dodge_rate": 10.0,
        "lore": "The tyrannical emperor of the universe who feared the legend of the Super Saiyan.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/frieza.png",
        "evolvable": 1
    },
    {
        "name": "Cell",
        "attack": 145,
        "defense": 135,
        "speed": 120,
        "element": "Dark",
        "rarity": "Epic",
        "skill": "Solar Kamehameha",
        "skill_description": "Unleashes an extremely powerful Kamehameha that deals massive damage and reduces defense.",
        "skill_mp_cost": 45,
        "skill_cooldown": 4,
        "critical_rate": 15.0,
        "dodge_rate": 12.0,
        "lore": "A bio-android created by Dr. Gero from the cells of the greatest fighters to achieve perfection.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/cell.png",
        "evolvable": 1
    },
    {
        "name": "Beerus",
        "attack": 180,
        "defense": 150,
        "speed": 170,
        "element": "Star",
        "rarity": "Legendary",
        "skill": "Hakai (Destruction)",
        "skill_description": "Uses the power of destruction to potentially eliminate opponents instantly.",
        "skill_mp_cost": 60,
        "skill_cooldown": 6,
        "critical_rate": 25.0,
        "dodge_rate": 20.0,
        "lore": "The God of Destruction of Universe 7 who maintains the balance by destroying when necessary.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/beerus.png",
        "evolvable": 1
    },
    {
        "name": "Jiren",
        "attack": 190,
        "defense": 170,
        "speed": 160,
        "element": "Earth",
        "rarity": "Legendary",
        "skill": "Power Impact",
        "skill_description": "Unleashes a powerful ki blast that can break through almost any defense.",
        "skill_mp_cost": 50,
        "skill_cooldown": 5,
        "critical_rate": 20.0,
        "dodge_rate": 15.0,
        "lore": "The strongest member of the Pride Troopers and the most powerful mortal in Universe 11.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/jiren.png",
        "evolvable": 1
    },
    {
        "name": "Goku Ultra Instinct",
        "attack": 210,
        "defense": 180,
        "speed": 230,
        "element": "Light",
        "rarity": "Legendary",
        "skill": "Autonomous Ultra Instinct",
        "skill_description": "Reaches a state where the body moves on its own, guaranteeing dodges and critical hits for 3 turns.",
        "skill_mp_cost": 80,
        "skill_cooldown": 7,
        "critical_rate": 40.0,
        "dodge_rate": 50.0,
        "lore": "Goku's ultimate form where he taps into the power of the gods, allowing his body to react without thinking.",
        "image_url": "https://cdn.discordapp.com/attachments/123456789/123456789/ultrainstinct.png",
        "evolvable": 0
    }
]

# Store evolution data
evolution_data = {
    "Monkey D. Luffy": {
        "base_card_id": 1,  # Matches the position in cards_list (0-indexed)
        "stages": {
            # Stage 0 to 1 evolution
            0: {
                "materials": [
                    {"material_id": 6, "quantity": 3},  # Elemental Core: Fire
                    {"material_id": 3, "quantity": 5}   # Star Fragment
                ],
                "gold_cost": 3000,
                "result": {
                    "new_name": "Monkey D. Luffy - Gear Second",
                    "attack_boost": 20,
                    "defense_boost": 10,
                    "speed_boost": 40,
                    "new_skill": "Jet Gatling",
                    "new_skill_description": "Pumps blood faster to increase speed, delivering a barrage of rapid punches that hit multiple times.",
                    "new_image_url": None
                }
            },
            # Stage 1 to 2 evolution
            1: {
                "materials": [
                    {"material_id": 6, "quantity": 5},  # Elemental Core: Fire
                    {"material_id": 9, "quantity": 3},  # Elemental Core: Air
                    {"material_id": 5, "quantity": 1}   # Cosmic Dust
                ],
                "gold_cost": 8000,
                "result": {
                    "new_name": "Monkey D. Luffy - Gear Fifth",
                    "attack_boost": 60,
                    "defense_boost": 50,
                    "speed_boost": 40,
                    "new_skill": "Bajrang Gun",
                    "new_skill_description": "Transforms into the embodiment of the Sun God Nika, delivering a gigantic fist that deals massive damage and ignores defense.",
                    "new_image_url": None
                }
            }
        }
    },
    "Goku": {
        "base_card_id": 9,
        "stages": {
            0: {
                "materials": [
                    {"material_id": 10, "quantity": 3},  # Elemental Core: Light
                    {"material_id": 3, "quantity": 5}    # Star Fragment
                ],
                "gold_cost": 3000,
                "result": {
                    "new_name": "Goku - Super Saiyan",
                    "attack_boost": 30,
                    "defense_boost": 20,
                    "speed_boost": 20,
                    "new_skill": "Super Kamehameha",
                    "new_skill_description": "A more powerful version of the Kamehameha that deals massive damage with increased critical rate.",
                    "new_image_url": None
                }
            },
            1: {
                "materials": [
                    {"material_id": 10, "quantity": 5},  # Elemental Core: Light
                    {"material_id": 4, "quantity": 3},   # Dragon Scale
                    {"material_id": 5, "quantity": 2}    # Cosmic Dust
                ],
                "gold_cost": 10000,
                "result": {
                    "new_name": "Goku Ultra Instinct",
                    "attack_boost": 50,
                    "defense_boost": 50,
                    "speed_boost": 90,
                    "new_skill": "Autonomous Ultra Instinct",
                    "new_skill_description": "Reaches a state where the body moves on its own, guaranteeing dodges and critical hits for 3 turns.",
                    "new_image_url": None
                }
            }
        }
    },
    "Vegeta": {
        "base_card_id": 10,
        "stages": {
            0: {
                "materials": [
                    {"material_id": 6, "quantity": 3},   # Elemental Core: Fire
                    {"material_id": 3, "quantity": 5}    # Star Fragment
                ],
                "gold_cost": 3000,
                "result": {
                    "new_name": "Vegeta - Super Saiyan",
                    "attack_boost": 35,
                    "defense_boost": 15,
                    "speed_boost": 20,
                    "new_skill": "Big Bang Attack",
                    "new_skill_description": "Concentrates ki into a single point and releases it as a powerful explosion with high critical damage.",
                    "new_image_url": None
                }
            },
            1: {
                "materials": [
                    {"material_id": 6, "quantity": 5},  # Elemental Core: Fire
                    {"material_id": 4, "quantity": 3},  # Dragon Scale
                    {"material_id": 5, "quantity": 2}   # Cosmic Dust
                ],
                "gold_cost": 10000,
                "result": {
                    "new_name": "Vegeta - Ultra Ego",
                    "attack_boost": 70,
                    "defense_boost": 60,
                    "speed_boost": 40,
                    "new_skill": "Hakai-infused Final Flash",
                    "new_skill_description": "Combines the power of destruction with his signature attack, dealing devastating damage that increases based on damage taken.",
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
            base_card_id = evo_data["base_card_id"] + 32  # Adjust for 1-indexed database and offset (16 cards in cards1.py + 16 in cards2.py)
            
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
    for i, card in enumerate(cards_list, 33):  # Start from 33 (after cards1.py and cards2.py)
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
