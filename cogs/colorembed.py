import discord
from discord.ext import commands

class ColorEmbed(commands.Cog):
    """Handles embed colors for different card rarities."""

    RARITY_COLORS = {
        "Legendary": discord.Color.gold(),
        "Epic": discord.Color.purple(),
        "Rare": discord.Color.blue(),
        "Uncommon": discord.Color.green(),
        "Common": discord.Color.light_grey(),
    }

    ELEMENT_COLORS = {
        "Fire": discord.Color.red(),
        "Water": discord.Color.blue(),
        "Earth": discord.Color.dark_green(),
        "Air": discord.Color.light_grey(),
        "Electric": discord.Color.gold(),
        "Ice": discord.Color.teal(),
        "Light": discord.Color(0xFAFAFA),  # Almost white
        "Dark": discord.Color.dark_purple(),
        "Cute": discord.Color.magenta(),
        "Sweet": discord.Color.dark_magenta(),
        "Star": discord.Color(0xFFD700),  # Gold for stars
    }

    @classmethod
    def get_color(cls, rarity):
        """Returns the embed color based on rarity."""
        return cls.RARITY_COLORS.get(rarity, discord.Color.default())
    
    @classmethod
    def get_element_color(cls, element):
        """Returns the embed color based on element."""
        return cls.ELEMENT_COLORS.get(element, discord.Color.default())
    
    @classmethod
    def get_combined_color(cls, rarity, element):
        """Returns a color that combines rarity and element (prioritizes rarity)."""
        rarity_color = cls.get_color(rarity)
        element_color = cls.get_element_color(element)
        
        # For legendary cards, always use gold
        if rarity == "Legendary":
            return rarity_color
        
        # For other rarities, use element color
        return element_color if element in cls.ELEMENT_COLORS else rarity_color

async def setup(bot):
    await bot.add_cog(ColorEmbed(bot))
