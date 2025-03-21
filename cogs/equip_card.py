import discord
from discord.ext import commands

class EquipCard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()

    @commands.command(name="equip")
    async def equip_command(self, ctx, card_id: int = None):
        """Equip a card from your collection"""
        user_id = ctx.author.id

        # Check if the user provided a card ID
        if card_id is None:
            await ctx.send(f"{ctx.author.mention}, please provide a card ID! Example: `!equip 1`")
            return

        # Check if the card exists and belongs to the user
        self.cursor.execute("""
            SELECT id, name, rarity, level, attack, defense, speed 
            FROM usercards 
            WHERE id = ? AND user_id = ?
        """, (card_id, user_id))
        
        card = self.cursor.fetchone()

        if not card:
            await ctx.send(f"{ctx.author.mention}, you don't own a card with ID `{card_id}`!")
            return
        
        card_id, card_name, rarity, level, attack, defense, speed = card

        # Unequip any previously equipped card
        self.cursor.execute("UPDATE usercards SET equipped = 0 WHERE user_id = ?", (user_id,))

        # Equip the selected card
        self.cursor.execute("UPDATE usercards SET equipped = 1 WHERE id = ? AND user_id = ?", (card_id, user_id))
        self.db.conn.commit()

        # Create embed with card info
        from cogs.colorembed import ColorEmbed
        embed = discord.Embed(
            title=f"Card Equipped: {card_name}",
            description=f"Level {level} {rarity} Card",
            color=ColorEmbed.get_color(rarity)
        )
        
        embed.add_field(name="Attack", value=str(attack), inline=True)
        embed.add_field(name="Defense", value=str(defense), inline=True)
        embed.add_field(name="Speed", value=str(speed), inline=True)
        
        # Get card image if available
        self.cursor.execute("SELECT image_url FROM usercards WHERE id = ?", (card_id,))
        image_data = self.cursor.fetchone()
        
        if image_data and image_data[0]:
            embed.set_thumbnail(url=image_data[0])
        
        await ctx.send(f"✅ {ctx.author.mention} equipped `{card_name}`!", embed=embed)

    @commands.command(name="unequip")
    async def unequip_command(self, ctx):
        """Unequip your currently equipped card"""
        user_id = ctx.author.id

        # Check if user has an equipped card
        self.cursor.execute("SELECT name FROM usercards WHERE user_id = ? AND equipped = 1", (user_id,))
        card = self.cursor.fetchone()

        if not card:
            await ctx.send(f"{ctx.author.mention}, you don't have any card equipped!")
            return

        # Unequip the card
        self.cursor.execute("UPDATE usercards SET equipped = 0 WHERE user_id = ? AND equipped = 1", (user_id,))
        self.db.conn.commit()

        await ctx.send(f"{ctx.author.mention}, you unequipped `{card[0]}`.")

    @commands.command(name="equipped")
    async def equipped_command(self, ctx):
        """View your currently equipped card"""
        user_id = ctx.author.id

        # Check if user has an equipped card
        self.cursor.execute("""
            SELECT id, name, rarity, level, attack, defense, speed, element, 
                   skill, skill_description, skill_mp_cost, critical_rate, 
                   dodge_rate, image_url
            FROM usercards 
            WHERE user_id = ? AND equipped = 1
        """, (user_id,))
        
        card = self.cursor.fetchone()

        if not card:
            await ctx.send(f"{ctx.author.mention}, you don't have any card equipped!")
            return

        # Unpack card data
        card_id, name, rarity, level, attack, defense, speed, element, skill, skill_desc, skill_mp, crit_rate, dodge_rate, image_url = card

        # Create embed with card info
        from cogs.colorembed import ColorEmbed
        embed = discord.Embed(
            title=f"Equipped Card: {name}",
            description=f"Level {level} {rarity} Card",
            color=ColorEmbed.get_color(rarity)
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
        
        # Set image if available
        if image_url:
            embed.set_thumbnail(url=image_url)
        
        embed.set_footer(text=f"Card ID: {card_id}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EquipCard(bot))
