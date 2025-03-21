import discord
from discord.ext import commands
import math

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.cards_per_page = 5  # Number of cards to display per page

    @commands.command(name="cards")
    async def cards_command(self, ctx, page: int = 1):
        """Lists all owned cards with their stats"""
        user_id = ctx.author.id

        # Get total count of user's cards
        self.cursor.execute("SELECT COUNT(*) FROM usercards WHERE user_id = ?", (user_id,))
        total_cards = self.cursor.fetchone()[0]

        if total_cards == 0:
            await ctx.send(f"{ctx.author.mention}, you have no cards in your collection!")
            return

        # Calculate total pages
        total_pages = math.ceil(total_cards / self.cards_per_page)
        
        # Generate all page embeds
        embeds = []
        for current_page in range(1, total_pages + 1):
            # Calculate offset
            offset = (current_page - 1) * self.cards_per_page

            # Get cards for the current page
            self.cursor.execute("""
                SELECT id, name, rarity, level, attack, defense, speed, equipped
                FROM usercards
                WHERE user_id = ?
                ORDER BY level DESC, rarity DESC, id ASC
                LIMIT ? OFFSET ?
            """, (user_id, self.cards_per_page, offset))
            
            cards = self.cursor.fetchall()

            # Create embed for this page
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s Card Collection",
                description=f"Total Cards: {total_cards}",
                color=discord.Color.purple()
            )

            # Add cards to embed
            for card_id, name, rarity, level, attack, defense, speed, equipped in cards:
                # Add an indicator for equipped card
                equipped_text = "🎮 EQUIPPED" if equipped else ""
                
                embed.add_field(
                    name=f"#{card_id}: {name} {equipped_text}",
                    value=f"**Rarity:** {rarity}\n"
                          f"**Level:** {level}\n"
                          f"**ATK:** {attack} · **DEF:** {defense} · **SPD:** {speed}",
                    inline=False
                )
            
            # Add instruction for viewing details
            embed.set_footer(text=f"Use !view [card_id] to see detailed information")
            
            embeds.append(embed)
        
        # Use the pagination system
        pagination_cog = self.bot.get_cog("Pagination")
        if pagination_cog:
            await pagination_cog.paginate(ctx, embeds)
        else:
            # Fallback if pagination cog isn't loaded
            if embeds:
                await ctx.send(embed=embeds[0])

    @commands.command(name="view")
    async def view_card_command(self, ctx, card_id: int):
        """View detailed information about a specific card"""
        user_id = ctx.author.id

        # Get card details
        self.cursor.execute("""
            SELECT name, rarity, level, xp, attack, defense, speed, element,
                   skill, skill_description, skill_mp_cost, critical_rate,
                   dodge_rate, equipped, evolution_stage, image_url
            FROM usercards
            WHERE id = ? AND user_id = ?
        """, (card_id, user_id))
        
        card = self.cursor.fetchone()

        if not card:
            await ctx.send(f"{ctx.author.mention}, you don't own a card with ID `{card_id}`!")
            return

        # Unpack card data
        name, rarity, level, xp, attack, defense, speed, element, skill, skill_desc, skill_mp, crit_rate, dodge_rate, equipped, evo_stage, image_url = card

        # Calculate XP needed for next level
        from cogs.card_exp import CardExp
        card_exp = CardExp(self.bot)
        xp_needed = card_exp.get_required_xp(level, rarity)
        
        # Create progress bar for XP
        progress = min(1.0, xp / xp_needed)
        bar_length = 10
        filled_length = int(bar_length * progress)
        xp_bar = '█' * filled_length + '░' * (bar_length - filled_length)

        # Create embed
        from cogs.colorembed import ColorEmbed
        embed = discord.Embed(
            title=f"{name}",
            description=f"Level {level} {rarity} Card",
            color=ColorEmbed.get_color(rarity)
        )
        
        # Card status
        status_parts = []
        if equipped:
            status_parts.append("🎮 EQUIPPED")
        if evo_stage > 0:
            status_parts.append(f"✨ EVO STAGE {evo_stage}")
        
        if status_parts:
            embed.add_field(name="Status", value=" · ".join(status_parts), inline=False)
        
        # Experience
        embed.add_field(
            name="Experience", 
            value=f"**`{xp_bar}`** {xp}/{xp_needed}", 
            inline=False
        )
        
        # Basic stats
        embed.add_field(name="Attack", value=str(attack), inline=True)
        embed.add_field(name="Defense", value=str(defense), inline=True)
        embed.add_field(name="Speed", value=str(speed), inline=True)
        
        # Additional stats
        embed.add_field(name="Element", value=element, inline=True)
        embed.add_field(name="Critical Rate", value=f"{crit_rate}%", inline=True)
        embed.add_field(name="Dodge Rate", value=f"{dodge_rate}%", inline=True)
        
        # Skill info
        embed.add_field(
            name=f"Skill: {skill}", 
            value=f"{skill_desc}\nMP Cost: {skill_mp}",
            inline=False
        )
        
        # Check if card is evolvable
        self.cursor.execute("""
            SELECT base_card_id FROM usercards WHERE id = ?
        """, (card_id,))
        base_card_id = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT COUNT(*) FROM evolution_requirements
            WHERE base_card_id = ? AND evolution_stage = ?
        """, (base_card_id, evo_stage))
        
        can_evolve = self.cursor.fetchone()[0] > 0
        
        if can_evolve:
            embed.add_field(
                name="Evolution",
                value="This card can evolve! Use `!evolve " + str(card_id) + "` to evolve it.",
                inline=False
            )
        
        # Set image if available
        if image_url:
            embed.set_thumbnail(url=image_url)
        
        embed.set_footer(text=f"Card ID: {card_id}")
        
        await ctx.send(embed=embed)

    @commands.command(name="search")
    async def search_command(self, ctx, *, search_term: str):
        """Search for cards in your collection by name or rarity"""
        user_id = ctx.author.id
        search_term = search_term.lower()

        # Search for cards matching the term
        self.cursor.execute("""
            SELECT id, name, rarity, level, attack, defense, speed, element, equipped
            FROM usercards
            WHERE user_id = ? AND (LOWER(name) LIKE ? OR LOWER(rarity) LIKE ? OR LOWER(element) LIKE ?)
            ORDER BY level DESC, rarity DESC, id ASC
        """, (user_id, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        
        cards = self.cursor.fetchall()

        if not cards:
            await ctx.send(f"{ctx.author.mention}, no cards found matching `{search_term}`!")
            return

        # Pagination settings
        cards_per_page = 5
        pages = []
        
        # Split cards into pages
        for i in range(0, len(cards), cards_per_page):
            page_cards = cards[i:i+cards_per_page]
            
            # Create embed for this page
            embed = discord.Embed(
                title=f"Search Results for '{search_term}'",
                description=f"Found {len(cards)} cards in your collection",
                color=discord.Color.blue()
            )
            
            # Add cards to embed
            for card_id, name, rarity, level, attack, defense, speed, element, equipped in page_cards:
                # Add an indicator for equipped card
                equipped_text = "🎮 EQUIPPED" if equipped else ""
                
                embed.add_field(
                    name=f"#{card_id}: {name} {equipped_text}",
                    value=f"**Rarity:** {rarity} · **Level:** {level}\n"
                          f"**ATK:** {attack} · **DEF:** {defense} · **SPD:** {speed}\n"
                          f"**Element:** {element}",
                    inline=False
                )
            
            embed.set_footer(text="Use !view [card_id] to see full details")
            pages.append(embed)
        
        # Use the pagination system if we have more than one page
        if len(pages) > 1:
            pagination_cog = self.bot.get_cog("Pagination")
            if pagination_cog:
                await pagination_cog.paginate(ctx, pages)
            else:
                await ctx.send(embed=pages[0])
        else:
            await ctx.send(embed=pages[0])

async def setup(bot):
    await bot.add_cog(Inventory(bot))
