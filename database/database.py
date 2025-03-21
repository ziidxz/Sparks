import sqlite3
import os
import logging

logger = logging.getLogger('bot.database')

class Database:
    def __init__(self):
        # Ensure database directory exists
        if not os.path.exists("database"):
            os.makedirs("database")
            
        self.db_path = "database/sparks.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Enable foreign keys
        self.cursor.execute("PRAGMA foreign_keys = ON")
        
        self.create_tables()
        logger.info(f"Database initialized: {self.db_path}")

    def create_tables(self):
        """Creates all necessary tables for the bot's functionality."""
        
        # Player table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                gold INTEGER DEFAULT 1000,
                diamonds INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                stamina INTEGER DEFAULT 10,
                max_stamina INTEGER DEFAULT 10,
                mp INTEGER DEFAULT 100,
                max_mp INTEGER DEFAULT 100,
                about TEXT DEFAULT '',
                last_daily INTEGER DEFAULT 0,
                last_vote INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                pvp_wins INTEGER DEFAULT 0,
                pvp_losses INTEGER DEFAULT 0,
                boss_wins INTEGER DEFAULT 0
            )
        """)
        
        # Cards base table - template for all available cards
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rarity TEXT NOT NULL CHECK (rarity IN ('Common', 'Uncommon', 'Rare', 'Epic', 'Legendary')),
                attack INTEGER DEFAULT 0,
                defense INTEGER DEFAULT 0,
                speed INTEGER DEFAULT 0,
                element TEXT NOT NULL,
                skill TEXT NOT NULL,
                skill_description TEXT NOT NULL,
                skill_mp_cost INTEGER DEFAULT 10,
                skill_cooldown INTEGER DEFAULT 1,
                critical_rate REAL DEFAULT 5.0,
                dodge_rate REAL DEFAULT 5.0,
                lore TEXT NOT NULL,
                image_url TEXT DEFAULT NULL,
                evolvable INTEGER DEFAULT 0  -- 0=false, 1=true
            )
        """)
        
        # User's owned cards
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usercards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                base_card_id INTEGER,  -- Links to the original card type in cards table
                name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                attack INTEGER DEFAULT 0,
                defense INTEGER DEFAULT 0,
                speed INTEGER DEFAULT 0,
                element TEXT NOT NULL,
                skill TEXT NOT NULL,
                skill_description TEXT NOT NULL,
                skill_mp_cost INTEGER DEFAULT 10,
                skill_cooldown INTEGER DEFAULT 1,
                critical_rate REAL DEFAULT 5.0,
                dodge_rate REAL DEFAULT 5.0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                equipped INTEGER DEFAULT 0,  -- 0=false, 1=true
                evolution_stage INTEGER DEFAULT 0,  -- 0=base, 1=evolved once, etc.
                image_url TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES players(user_id),
                FOREIGN KEY (base_card_id) REFERENCES cards(id)
            )
        """)
        
        # Materials for card evolution and crafting
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                rarity TEXT NOT NULL,
                image_url TEXT DEFAULT NULL
            )
        """)
        
        # User's owned materials
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                material_id INTEGER,
                quantity INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES players(user_id),
                FOREIGN KEY (material_id) REFERENCES materials(id)
            )
        """)
        
        # Evolution requirements
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_card_id INTEGER,
                evolution_stage INTEGER,  -- 0->1, 1->2, etc.
                material_id INTEGER,
                quantity INTEGER,
                gold_cost INTEGER,
                FOREIGN KEY (base_card_id) REFERENCES cards(id),
                FOREIGN KEY (material_id) REFERENCES materials(id)
            )
        """)
        
        # Evolution results - what a card evolves into
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_card_id INTEGER,
                evolution_stage INTEGER,
                new_name TEXT NOT NULL,
                attack_boost INTEGER,
                defense_boost INTEGER,
                speed_boost INTEGER,
                new_skill TEXT,
                new_skill_description TEXT,
                new_image_url TEXT,
                FOREIGN KEY (base_card_id) REFERENCES cards(id)
            )
        """)
        
        # Items table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                type TEXT NOT NULL,  -- potion, boost, etc.
                effect TEXT NOT NULL,  -- what the item does
                cost INTEGER DEFAULT 0,
                image_url TEXT DEFAULT NULL
            )
        """)
        
        # User's owned items
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES players(user_id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)
        
        # Boss table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bosses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                hp INTEGER DEFAULT 1000,
                attack INTEGER DEFAULT 100,
                defense INTEGER DEFAULT 100,
                speed INTEGER DEFAULT 50,
                element TEXT NOT NULL,
                skill TEXT NOT NULL,
                skill_description TEXT NOT NULL,
                image_url TEXT DEFAULT NULL,
                lore TEXT NOT NULL,
                min_player_level INTEGER DEFAULT 1,  -- Minimum player level to challenge
                reward_gold INTEGER DEFAULT 100,
                reward_xp INTEGER DEFAULT 50
            )
        """)
        
        # Boss drops
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS boss_drops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boss_id INTEGER,
                material_id INTEGER,
                drop_rate REAL DEFAULT 0.1,  -- 0.1 = 10% chance
                min_quantity INTEGER DEFAULT 1,
                max_quantity INTEGER DEFAULT 1,
                FOREIGN KEY (boss_id) REFERENCES bosses(id),
                FOREIGN KEY (material_id) REFERENCES materials(id)
            )
        """)
        
        # Trading table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offerer_id INTEGER,
                receiver_id INTEGER,
                offer_card_id INTEGER,
                request_card_id INTEGER,
                status TEXT DEFAULT 'pending',  -- pending, accepted, rejected, cancelled
                timestamp INTEGER,
                FOREIGN KEY (offerer_id) REFERENCES players(user_id),
                FOREIGN KEY (receiver_id) REFERENCES players(user_id),
                FOREIGN KEY (offer_card_id) REFERENCES usercards(id),
                FOREIGN KEY (request_card_id) REFERENCES usercards(id)
            )
        """)
        
        # Battle history
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                player_card INTEGER,  -- Card name for historical reference
                enemy_card INTEGER,   -- Card/boss name
                turns INTEGER,
                result TEXT,          -- Win or Loss
                timestamp INTEGER DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        """)
        
        # PvP battle history
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pvp_battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER,
                player2_id INTEGER,
                player1_card INTEGER,  -- Card ID
                player2_card INTEGER,  -- Card ID
                winner_id INTEGER,
                turns INTEGER,
                timestamp INTEGER DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (player1_id) REFERENCES players(user_id),
                FOREIGN KEY (player2_id) REFERENCES players(user_id)
            )
        """)
        
        # Complete the transaction
        self.conn.commit()
        logger.info("All database tables created or verified")
        
        # Initialize basic data if database is new
        self.initialize_data()
    
    def initialize_data(self):
        """Initialize basic data if not already present."""
        # Check if items table has data
        self.cursor.execute("SELECT COUNT(*) FROM items")
        items_count = self.cursor.fetchone()[0]
        
        if items_count == 0:
            # Add basic items
            items = [
                (1, "Stamina Potion", "Restores 5 stamina points", "potion", "stamina", 100, None),
                (2, "MP Potion", "Restores 50 MP", "potion", "mp", 150, None),
                (3, "EXP Boost", "Increases EXP gain by 50% for 1 hour", "boost", "exp", 300, None),
                (4, "Gold Boost", "Increases gold drops by 50% for 1 hour", "boost", "gold", 250, None),
                (5, "Card Pack: Basic", "Contains 1 random card (Common-Rare)", "pack", "basic", 100, None),
                (6, "Card Pack: Premium", "Contains 1 random card (Uncommon-Epic)", "pack", "premium", 500, None),
                (7, "Card Pack: Legendary", "Contains 1 random card (Rare-Legendary)", "pack", "legendary", 2000, None)
            ]
            
            self.cursor.executemany("""
                INSERT OR IGNORE INTO items (id, name, description, type, effect, cost, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, items)
            
            logger.info("Basic items added to database")
        
        # Check if materials table has data
        self.cursor.execute("SELECT COUNT(*) FROM materials")
        materials_count = self.cursor.fetchone()[0]
        
        if materials_count == 0:
            # Add basic materials
            materials = [
                (1, "Crystal Shard", "A basic crafting material for card evolution", "Common", None),
                (2, "Magical Essence", "Enhances a card's magical properties", "Uncommon", None),
                (3, "Star Fragment", "A rare material that boosts card stats", "Rare", None),
                (4, "Dragon Scale", "A powerful material for high-tier evolutions", "Epic", None),
                (5, "Cosmic Dust", "The rarest material, essential for legendary evolutions", "Legendary", None),
                (6, "Elemental Core: Fire", "Core material for Fire element cards", "Rare", None),
                (7, "Elemental Core: Water", "Core material for Water element cards", "Rare", None),
                (8, "Elemental Core: Earth", "Core material for Earth element cards", "Rare", None),
                (9, "Elemental Core: Air", "Core material for Air element cards", "Rare", None),
                (10, "Elemental Core: Light", "Core material for Light element cards", "Epic", None),
                (11, "Elemental Core: Dark", "Core material for Dark element cards", "Epic", None),
            ]
            
            self.cursor.executemany("""
                INSERT OR IGNORE INTO materials (id, name, description, rarity, image_url)
                VALUES (?, ?, ?, ?, ?)
            """, materials)
            
            logger.info("Basic materials added to database")
            
        # Check if bosses table has data
        self.cursor.execute("SELECT COUNT(*) FROM bosses")
        bosses_count = self.cursor.fetchone()[0]
        
        if bosses_count == 0:
            # Add starter bosses
            bosses = [
                (1, "Training Dummy", 1, 500, 50, 50, 20, "None", "None", "Does nothing special", 
                 None, "A basic training dummy for novice card battlers.", 1, 50, 25),
                
                (2, "Forest Guardian", 5, 1000, 100, 80, 40, "Earth", "Nature's Wrath", 
                 "Summons vines to entangle opponents, reducing their speed", 
                 None, "A protective spirit that guards the ancient forest.", 3, 150, 75),
                
                (3, "Shadow Ninja", 10, 1500, 150, 100, 80, "Dark", "Shadow Strike", 
                 "Attacks from the shadows with increased critical rate", 
                 None, "A mysterious ninja who harnesses the power of darkness.", 5, 300, 150),
                
                (4, "Dragon King", 20, 3000, 250, 200, 60, "Fire", "Dragon's Breath", 
                 "Breathes fire, dealing damage over time", 
                 None, "The mighty ruler of all dragons, with scales harder than steel.", 10, 800, 400),
                
                (5, "Cosmic Entity", 30, 5000, 350, 300, 100, "Star", "Supernova", 
                 "Creates a massive explosion, dealing heavy damage to all opponents", 
                 None, "A being from beyond the stars, wielding unimaginable cosmic power.", 20, 1500, 750)
            ]
            
            self.cursor.executemany("""
                INSERT OR IGNORE INTO bosses (id, name, level, hp, attack, defense, speed, element, skill, 
                                             skill_description, image_url, lore, min_player_level, 
                                             reward_gold, reward_xp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, bosses)
            
            # Add boss drops
            boss_drops = [
                (1, 1, 1, 0.5, 1, 3),  # Training Dummy has 50% chance to drop 1-3 Crystal Shards
                (2, 1, 1, 0.3, 2, 5),  # Forest Guardian has 30% chance to drop 2-5 Crystal Shards
                (3, 2, 2, 0.4, 1, 3),  # Forest Guardian has 40% chance to drop 1-3 Magical Essence
                (4, 3, 3, 0.2, 1, 2),  # Shadow Ninja has 20% chance to drop 1-2 Star Fragments
                (5, 3, 11, 0.3, 1, 2), # Shadow Ninja has 30% chance to drop 1-2 Dark Elemental Cores
                (6, 4, 4, 0.1, 1, 1),  # Dragon King has 10% chance to drop a Dragon Scale
                (7, 4, 6, 0.3, 1, 3),  # Dragon King has 30% chance to drop 1-3 Fire Elemental Cores
                (8, 5, 5, 0.05, 1, 1), # Cosmic Entity has 5% chance to drop Cosmic Dust
                (9, 5, 10, 0.2, 1, 2)  # Cosmic Entity has 20% chance to drop 1-2 Light Elemental Cores
            ]
            
            self.cursor.executemany("""
                INSERT OR IGNORE INTO boss_drops (id, boss_id, material_id, drop_rate, min_quantity, max_quantity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, boss_drops)
            
            logger.info("Basic bosses and their drops added to database")
        
        self.conn.commit()

    def backup_database(self):
        """Creates a backup copy of the database."""
        import shutil
        from datetime import datetime
        
        backup_dir = "database/backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/sparks_backup_{timestamp}.db"
        
        # Ensure all changes are committed
        self.conn.commit()
        
        # Close connection temporarily
        self.conn.close()
        
        # Copy the database file
        shutil.copy2(self.db_path, backup_path)
        
        # Reopen connection
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        logger.info(f"Database backed up to {backup_path}")
        return backup_path
        
    def close(self):
        """Safely closes the database connection."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            logger.info("Database connection closed")
