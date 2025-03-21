import discord
from discord.ext import commands
import time
import math

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()

    @commands.command(name="profile")
    async def profile_command(self, ctx, member: discord.Member = None):
        """📜 View your own or another user's profile"""
        user = member or ctx.author
        user_id = user.id

        # Get player data
        self.cursor.execute("""
            SELECT gold, diamonds, level, xp, stamina, max_stamina, mp, max_mp, about,
                   wins, losses, pvp_wins, pvp_losses, boss_wins
            FROM players WHERE user_id = ?
        """, (user_id,))
        
        player = self.cursor.fetchone()

        if not player:
            if member:
                await ctx.send(f"{user.mention} has not started their journey yet!")
            else:
                await ctx.send(f"{user.mention}, you need to use `!start` to create your profile!")
            return

        gold, diamonds, level, xp, stamina, max_stamina, mp, max_mp, about, wins, losses, pvp_wins, pvp_losses, boss_wins = player
        
        # Default values for null columns
        gold = gold or 0
        diamonds = diamonds or 0
        xp = xp or 0
        about = about or "No description set."
        wins = wins or 0
        losses = losses or 0
        pvp_wins = pvp_wins or 0
        pvp_losses = pvp_losses or 0
        boss_wins = boss_wins or 0

        # Calculate XP progress
        xp_needed = int(150 * (1.5 ** (level - 1)))
        progress = min(1.0, xp / xp_needed)
        bar_length = 10
        filled_length = int(bar_length * progress)
        xp_bar = '█' * filled_length + '░' * (bar_length - filled_length)

        # Get equipped card
        self.cursor.execute("""
            SELECT id, name, level, rarity, attack, defense, image_url 
            FROM usercards 
            WHERE user_id = ? AND equipped = 1
        """, (user_id,))
        
        card_data = self.cursor.fetchone()
        
        # Create the embed
        embed = discord.Embed(
            title=f"{user.display_name}'s Profile",
            description=about,
            color=discord.Color.blue()
        )
        
        # Set user avatar as thumbnail
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Player stats
        embed.add_field(
            name="Level",
            value=f"{level}",
            inline=True
        )
        
        embed.add_field(
            name="Experience",
            value=f"**`{xp_bar}`** {xp}/{xp_needed}",
            inline=True
        )
        
        # Resources
        embed.add_field(
            name="Resources",
            value=f"💰 Gold: {gold}\n💎 Diamonds: {diamonds}",
            inline=False
        )
        
        # Battle stats
        total_battles = wins + losses
        win_rate = (wins / total_battles * 100) if total_battles > 0 else 0
        
        total_pvp = pvp_wins + pvp_losses
        pvp_win_rate = (pvp_wins / total_pvp * 100) if total_pvp > 0 else 0
        
        embed.add_field(
            name="Battle Stats",
            value=f"**PvE:** {wins} Wins / {losses} Losses ({win_rate:.1f}%)\n"
                  f"**PvP:** {pvp_wins} Wins / {pvp_losses} Losses ({pvp_win_rate:.1f}%)\n"
                  f"**Boss Wins:** {boss_wins}",
            inline=False
        )
        
        # Energy stats
        embed.add_field(
            name="⚡ Stamina",
            value=f"{stamina}/{max_stamina}",
            inline=True
        )
        
        embed.add_field(
            name="🔷 MP",
            value=f"{mp}/{max_mp}",
            inline=True
        )
        
        # Equipped card
        if card_data:
            card_id, card_name, card_level, card_rarity, card_attack, card_defense, card_image = card_data
            
            embed.add_field(
                name="🎮 Equipped Card",
                value=f"**{card_name}** (Lvl {card_level} {card_rarity})\n"
                      f"ATK: {card_attack} · DEF: {card_defense}",
                inline=False
            )
            
            if card_image:
                embed.set_image(url=card_image)
        else:
            embed.add_field(
                name="🎮 Equipped Card",
                value="None",
                inline=False
            )
        
        # Footer with commands
        footer_text = "!start to create profile · !cards to view collection · !daily for rewards"
        embed.set_footer(text=footer_text)
        
        await ctx.send(embed=embed)

    @commands.command(name="start")
    async def start_command(self, ctx):
        """🌟 Start your journey and create a profile"""
        user_id = ctx.author.id

        # Check if the user already exists
        self.cursor.execute("SELECT user_id FROM players WHERE user_id = ?", (user_id,))
        existing_user = self.cursor.fetchone()

        if existing_user:
            await ctx.send(f"{ctx.author.mention}, you already have a profile! Use `!profile` to view it.")
            return

        # Insert new player data
        self.cursor.execute("""
            INSERT INTO players (
                user_id, gold, diamonds, level, xp, stamina, max_stamina,
                mp, max_mp, about, last_daily, last_vote
            ) VALUES (?, 1000, 0, 1, 0, 10, 10, 100, 100, 'No description set.', 0, 0)
        """, (user_id,))
        
        self.db.conn.commit()
        
        # Give the player a starter pack
        self.cursor.execute("SELECT id FROM items WHERE name = 'Card Pack: Basic'")
        basic_pack = self.cursor.fetchone()
        
        if basic_pack:
            # Add 3 starter packs
            self.cursor.execute("""
                INSERT INTO user_items (user_id, item_id, quantity)
                VALUES (?, ?, 3)
            """, (user_id, basic_pack[0]))
            
        self.db.conn.commit()
        
        # Create success embed
        embed = discord.Embed(
            title="🌟 Journey Begun!",
            description="Your adventure in the world of anime card battling begins now!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Starter Resources",
            value="💰 1000 Gold\n⚡ 10/10 Stamina\n🔷 100/100 MP",
            inline=False
        )
        
        embed.add_field(
            name="Starter Bonus",
            value="You received 3 Basic Card Packs! Use `!gacha basic` to open them.",
            inline=False
        )
        
        embed.add_field(
            name="Next Steps",
            value="1. `!gacha basic` - Open your starter packs\n"
                  "2. `!equip [card_id]` - Equip your best card\n"
                  "3. `!battle` - Start battling to earn gold & experience\n"
                  "4. `!daily` - Collect daily rewards",
            inline=False
        )
        
        embed.set_footer(text="Use !help to see all available commands")
        
        await ctx.send(f"🌟 {ctx.author.mention}, your journey has begun!", embed=embed)

    @commands.command(name="setabout", aliases=["bio"])
    async def set_about_command(self, ctx, *, about_text: str):
        """✍️ Set your profile description"""
        user_id = ctx.author.id

        # Check if profile exists
        self.cursor.execute("SELECT user_id FROM players WHERE user_id = ?", (user_id,))
        if not self.cursor.fetchone():
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return

        # Validate text length
        if len(about_text) > 200:
            await ctx.send("⚠️ Your profile description is too long! Keep it under 200 characters.")
            return

        # Update description
        self.cursor.execute("UPDATE players SET about = ? WHERE user_id = ?", (about_text, user_id))
        self.db.conn.commit()

        await ctx.send(f"✅ {ctx.author.mention}, your profile description has been updated!")

    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard_command(self, ctx, category: str = "level"):
        """View the global leaderboard"""
        valid_categories = ["level", "gold", "wins", "pvp", "boss"]
        
        if category.lower() not in valid_categories:
            await ctx.send(f"{ctx.author.mention}, valid categories are: {', '.join(valid_categories)}")
            return
            
        # Create embeds for each category
        embeds = []
        
        for current_category in valid_categories:
            # Define query based on category
            if current_category == "level":
                query = """
                    SELECT user_id, level, xp
                    FROM players
                    ORDER BY level DESC, xp DESC
                    LIMIT 10
                """
                title = "Top Players by Level"
                format_str = lambda row: f"Level {row[1]} · XP: {row[2]}"
                
            elif current_category == "gold":
                query = """
                    SELECT user_id, gold
                    FROM players
                    ORDER BY gold DESC
                    LIMIT 10
                """
                title = "Richest Players"
                format_str = lambda row: f"{row[1]} Gold"
                
            elif current_category == "wins":
                query = """
                    SELECT user_id, wins, losses
                    FROM players
                    ORDER BY wins DESC
                    LIMIT 10
                """
                title = "Top PvE Battle Winners"
                format_str = lambda row: f"{row[1]} Wins · {row[2]} Losses"
                
            elif current_category == "pvp":
                query = """
                    SELECT user_id, pvp_wins, pvp_losses
                    FROM players
                    ORDER BY pvp_wins DESC
                    LIMIT 10
                """
                title = "Top PvP Battle Winners"
                format_str = lambda row: f"{row[1]} Wins · {row[2]} Losses"
                
            else:  # boss
                query = """
                    SELECT user_id, boss_wins
                    FROM players
                    ORDER BY boss_wins DESC
                    LIMIT 10
                """
                title = "Top Boss Slayers"
                format_str = lambda row: f"{row[1]} Boss Wins"
            
            # Execute query
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            # Create embed
            embed = discord.Embed(
                title=f"🏆 {title}",
                color=discord.Color.gold()
            )
            
            if results:
                # Fetch and add user data
                for i, row in enumerate(results, 1):
                    user_id = row[0]
                    
                    # Try to get user from guild
                    user = ctx.guild.get_member(user_id)
                    name = user.display_name if user else f"User {user_id}"
                    
                    # Add medal emoji for top 3
                    prefix = ""
                    if i == 1:
                        prefix = "🥇 "
                    elif i == 2:
                        prefix = "🥈 "
                    elif i == 3:
                        prefix = "🥉 "
                    else:
                        prefix = f"{i}. "
                    
                    embed.add_field(
                        name=f"{prefix}{name}",
                        value=format_str(row),
                        inline=False
                    )
            else:
                # No data available for this category
                embed.add_field(
                    name="No Data",
                    value="No players found for this leaderboard category yet!",
                    inline=False
                )
            
            # Add footer
            embed.set_footer(text=f"Use the buttons below to view different rankings")
            embeds.append(embed)
        
        # Reorder embeds so the requested category is first
        category_index = valid_categories.index(category.lower())
        embeds = embeds[category_index:] + embeds[:category_index]
        
        # Use the pagination system
        pagination_cog = self.bot.get_cog("Pagination")
        if pagination_cog:
            await pagination_cog.paginate(ctx, embeds)
        else:
            # Fallback if pagination cog isn't loaded
            await ctx.send(embed=embeds[0])

    @commands.command(name="stamina")
    async def stamina_command(self, ctx):
        """⚡ Check your stamina and regeneration time"""
        user_id = ctx.author.id
        
        # Get stamina data
        self.cursor.execute("SELECT stamina, max_stamina FROM players WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        
        if not result:
            await ctx.send(f"{ctx.author.mention}, you need to use `!start` first!")
            return
        
        stamina, max_stamina = result
        
        # Calculate time until full stamina
        minutes_per_stamina = 10  # One stamina every 10 minutes
        minutes_to_full = (max_stamina - stamina) * minutes_per_stamina
        
        hours = minutes_to_full // 60
        minutes = minutes_to_full % 60
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Stamina",
            color=discord.Color.blue()
        )
        
        # Create stamina bar
        bar_length = 10
        filled_length = int(bar_length * (stamina / max_stamina))
        stamina_bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        embed.add_field(
            name="Current Stamina",
            value=f"**`{stamina_bar}`** {stamina}/{max_stamina}",
            inline=False
        )
        
        if stamina < max_stamina:
            embed.add_field(
                name="Time to Full",
                value=f"{hours}h {minutes}m",
                inline=False
            )
            
            embed.add_field(
                name="Next Stamina",
                value=f"{minutes_per_stamina} minutes",
                inline=False
            )
        else:
            embed.add_field(
                name="Status",
                value="Stamina is full!",
                inline=False
            )
        
        embed.set_footer(text="Stamina is used for battles · Buy stamina potions in the shop")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Player(bot))
