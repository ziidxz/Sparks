import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Check if the script is run directly 
if __name__ == "__main__":
    # Determine if this is the Flask app or Discord bot
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        # Import the Flask app
        try:
            # Import app from app.py
            from app import app
        except ImportError:
            logging.error("Could not import Flask app from app.py")
            sys.exit(1)
    else:
        # Run the Discord bot
        import discord
        from discord.ext import commands
        from dotenv import load_dotenv
        from database.database import Database
        import asyncio
        
        logger = logging.getLogger('bot')
        
        # ✅ Load environment variables
        load_dotenv()
        
        # ✅ Create bot with help command disabled
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True  # Enable member intents for user lookups
        bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
        
        # ✅ Attach the database from the separate file
        bot.db = Database()
        
        # ✅ Ensure directories exist
        COGS_DIR = "./cogs"
        if not os.path.exists(COGS_DIR):
            os.makedirs(COGS_DIR)
        
        DATABASE_DIR = "./database"
        if not os.path.exists(DATABASE_DIR):
            os.makedirs(DATABASE_DIR)
        
        # List of all cogs to load
        COGS = [
            "pagination",    # Button-based UI pagination system
            "help",          # Core commands
            "player",        # Player profile and progression
            "card_exp",      # Card experience system
            "inventory",     # Card inventory management
            "equip_card",    # Card equipping system
            "battle",        # PvE battle system
            "battle_system", # Enhanced battle system with MP
            "dungeon_system",# Anime-themed dungeon system
            "pvp",           # PvP battle system
            "shop",          # Shop for items and packs
            "buy",           # Purchase system
            # Choose either original or enhanced version, not both
            # "gacha",         # Original card acquisition system
            "gacha_system",  # Enhanced gacha with chest system
            # Choose either original or enhanced version, not both
            # "trading",       # Card trading between players
            # Choose either original or enhanced version, not both  
            # "evolution",     # Basic card evolution system
            "evolution_system",  # Enhanced evolution system with materials
            "daily",         # Daily rewards and activities
            "hourly",        # Hourly stamina recharge
            "vote",          # Vote rewards system
            "boss",          # Boss battle system
            "skill",         # Card skill system
            "colorembed",    # Embed color utility
            # "materials",     # Materials and crafting system - conflicts with evolution_system
        ]
        
        # ✅ Setup and load cogs
        async def setup_hook():
            bot.remove_command("help")  # 🚀 Prevent conflicts with built-in help
        
            cogs_loaded = 0
            cogs_failed = 0
        
            # Load all cogs
            for cog in COGS:
                try:
                    await bot.load_extension(f"cogs.{cog}")
                    logger.info(f"📥 Loaded cog: {cog}")
                    cogs_loaded += 1
                except Exception as e:
                    logger.error(f"⚠️ Error loading {cog}: {e}")
                    cogs_failed += 1
        
            # Load card data
            try:
                await bot.load_extension("cogs.cards1")
                await bot.load_extension("cogs.cards2")
                await bot.load_extension("cogs.cards3")
                logger.info("📥 Loaded card data modules")
                cogs_loaded += 3
            except Exception as e:
                logger.error(f"⚠️ Error loading card data: {e}")
                cogs_failed += 1
        
            # Final connection summary
            logger.info("\n🔹 Bot Startup Summary")
            logger.info(f"✅ {cogs_loaded} cogs loaded successfully.")
            if cogs_failed > 0:
                logger.info(f"⚠️ {cogs_failed} cogs failed to load due to errors.\n")
            else:
                logger.info("✅ All cogs loaded without issues.\n")
        
        bot.setup_hook = setup_hook
        
        # Event: Bot is ready
        @bot.event
        async def on_ready():
            logger.info(f"🌟 {bot.user.name} has connected to Discord!")
            
            # Set bot presence
            activity = discord.Activity(
                type=discord.ActivityType.playing, 
                name="ㅗ | !help"
            )
            await bot.change_presence(activity=activity)
            
            # Initialize the anime card database
            try:
                from database.init_anime_cards import initialize_db
                
                logger.info("Initializing anime card database...")
                result = initialize_db()
                
                if result:
                    logger.info("✅ Anime card database initialized successfully.")
                else:
                    logger.warning("⚠️ Failed to initialize anime card database.")
            except Exception as e:
                logger.error(f"❌ Error initializing anime card database: {e}")
        
        # Event: Handle command errors gracefully
        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send(f"❌ Command not found. Try `!help` to see available commands.")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ Missing required argument: {error.param.name}. Try `!help {ctx.command.name}` for proper usage.")
            elif isinstance(error, commands.BadArgument):
                await ctx.send(f"❌ Invalid argument provided. Try `!help {ctx.command.name}` for proper usage.")
            elif isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.2f} seconds.")
            else:
                logger.error(f"Unhandled error in command {ctx.command.name if ctx.command else 'unknown'}: {error}")
                await ctx.send(f"❌ An error occurred: {error}")
        
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

bot.run(os.getenv("DISCORD_TOKEN"))

# For Gunicorn to find the Flask app
from app import app
