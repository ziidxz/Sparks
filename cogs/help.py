import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_categories = {
            "General": ["help", "profile", "start", "setabout", "leaderboard", "stamina"],
            "Cards": ["cards", "view", "search", "cardexp", "equip", "unequip", "equipped"],
            "Battles": ["battle", "pvp", "boss", "pvpstats", "bossstats"],
            "Card Collection": ["gacha", "multidraw", "evolve", "evorequire", "evolist"],
            "Economy": ["shop", "market", "buy", "use", "inventory", "boosts", "daily", "materials"],
            "Trading": ["trade", "accept", "decline", "trades", "tradehistory"],
            "Skills": ["skill", "skillinfo", "skills"]
        }
    
    @commands.command(name="help")
    async def help_command(self, ctx, command_name: str = None):
        """Shows help for all commands or a specific command"""
        if command_name:
            # Help for a specific command
            command = self.bot.get_command(command_name.lower())
            
            if not command:
                await ctx.send(f"{ctx.author.mention}, that command doesn't exist! Use `!help` to see all commands.")
                return
            
            embed = discord.Embed(
                title=f"Command: !{command.name}",
                description=command.help or "No description available.",
                color=discord.Color.blue()
            )
            
            # Aliases if any
            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join([f"`!{alias}`" for alias in command.aliases]),
                    inline=False
                )
            
            # Usage
            usage = f"!{command.name}"
            if command.signature:
                usage += f" {command.signature}"
            
            embed.add_field(
                name="Usage",
                value=f"`{usage}`",
                inline=False
            )
            
            # Example usage based on command
            if command.name == "gacha":
                embed.add_field(
                    name="Example",
                    value="`!gacha basic`\n`!gacha premium`\n`!gacha legendary`",
                    inline=False
                )
            elif command.name == "trade":
                embed.add_field(
                    name="Example",
                    value="`!trade @user 1 2`\nOffers your card with ID 1 for their card with ID 2",
                    inline=False
                )
            elif command.name == "evolve":
                embed.add_field(
                    name="Example",
                    value="`!evolve 5`\nEvolves your card with ID 5 to the next stage",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        else:
            # General help menu
            embed = discord.Embed(
                title="📌 Card Battle Game Help",
                description="Use `!help [command]` for detailed help on a specific command.",
                color=discord.Color.blue()
            )
            
            # Add each category
            for category, commands_list in self.command_categories.items():
                # Format command list
                commands_formatted = ", ".join([f"`!{cmd}`" for cmd in commands_list])
                
                embed.add_field(
                    name=category,
                    value=commands_formatted,
                    inline=False
                )
            
            # Main game flow
            embed.add_field(
                name="🌟 Getting Started",
                value="1. `!start` to create your profile\n"
                      "2. `!gacha basic` to get your first card\n"
                      "3. `!equip [card_id]` to equip a card\n"
                      "4. `!battle` to start fighting\n"
                      "5. `!daily` for daily rewards",
                inline=False
            )
            
            # Footer
            embed.set_footer(text="Use !profile to check your progress • !cards to see your collection")
            
            await ctx.send(embed=embed)
    
    @commands.command(name="guide")
    async def guide_command(self, ctx):
        """Shows a detailed guide for new players"""
        embed = discord.Embed(
            title="🌟 Anime Card Battle - Player Guide",
            description="Welcome to the world of anime card battles! This guide will help you get started.",
            color=discord.Color.gold()
        )
        
        # Getting Started
        embed.add_field(
            name="📝 Getting Started",
            value="1. Use `!start` to create your profile\n"
                  "2. Open card packs with `!gacha basic`\n"
                  "3. View your cards with `!cards`\n"
                  "4. Equip your best card with `!equip [card_id]`\n"
                  "5. Battle to earn gold and XP with `!battle`",
            inline=False
        )
        
        # Card Collection
        embed.add_field(
            name="🎴 Card Collection",
            value="• Cards have rarities from Common to Legendary\n"
                  "• Each card has unique stats and skills\n"
                  "• Cards gain XP and level up through battles\n"
                  "• Evolve cards to make them stronger with `!evolve`\n"
                  "• Trade cards with other players using `!trade`",
            inline=False
        )
        
        # Battle System
        embed.add_field(
            name="⚔️ Battle System",
            value="• PvE: Battle AI opponents with `!battle`\n"
                  "• PvP: Challenge other players with `!pvp @user`\n"
                  "• Boss: Fight powerful bosses with `!boss`\n"
                  "• Each battle costs 3 stamina\n"
                  "• Win to earn gold, materials, and XP",
            inline=False
        )
        
        # Economy & Resources
        embed.add_field(
            name="💰 Economy & Resources",
            value="• Gold: Used to buy items and evolve cards\n"
                  "• Stamina: Regenerates over time, used for battles\n"
                  "• MP: Used for special skills during battles\n"
                  "• Materials: Collected for card evolution\n"
                  "• Visit the shop with `!shop` to buy items",
            inline=False
        )
        
        # Daily Activities
        embed.add_field(
            name="📆 Daily Activities",
            value="• Collect daily rewards with `!daily`\n"
                  "• Check the market for special offers with `!market`\n"
                  "• Complete battles to earn resources\n"
                  "• Trade with other players to complete your collection",
            inline=False
        )
        
        # Tips & Tricks
        embed.add_field(
            name="💡 Tips & Tricks",
            value="• Focus on evolving one strong card first\n"
                  "• Save materials for high-rarity card evolution\n"
                  "• Use potions when needed from your `!inventory`\n"
                  "• Check `!cardexp` to see how close cards are to leveling up\n"
                  "• Balance your team with different elements for PvP",
            inline=False
        )
        
        embed.set_footer(text="Use !help for a list of all commands • Have fun playing!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
