import discord
from discord.ext import commands
import asyncio
import time

class Trading(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.active_trades = {}  # {trade_id: {offerer_id, receiver_id, offer_card_id, request_card_id}}
    
    def get_trade_id(self, offerer_id, receiver_id):
        """Generates a unique trade ID from the two users."""
        return f"{offerer_id}-{receiver_id}-{int(time.time())}"
    
    def get_user_card(self, user_id, card_id):
        """Gets card information for a user's card."""
        self.cursor.execute("""
            SELECT id, name, rarity, level, equipped, evolution_stage
            FROM usercards
            WHERE user_id = ? AND id = ?
        """, (user_id, card_id))
        
        return self.cursor.fetchone()
    
    def get_pending_trades(self, user_id):
        """Gets all pending trades for a user."""
        self.cursor.execute("""
            SELECT t.id, 
                   t.offerer_id, t.receiver_id, 
                   t.offer_card_id, t.request_card_id,
                   o.name AS offer_card_name, r.name AS request_card_name,
                   o.rarity AS offer_rarity, r.rarity AS request_rarity,
                   o.level AS offer_level, r.level AS request_level
            FROM trades t
            JOIN usercards o ON t.offer_card_id = o.id
            JOIN usercards r ON t.request_card_id = r.id
            WHERE (t.offerer_id = ? OR t.receiver_id = ?) AND t.status = 'pending'
        """, (user_id, user_id))
        
        return self.cursor.fetchall()
    
    @commands.command(name="trade")
    async def trade_command(self, ctx, member: discord.Member, your_card_id: int, their_card_id: int):
        """Offer a trade to another player"""
        if member.id == ctx.author.id:
            await ctx.send(f"{ctx.author.mention}, you cannot trade with yourself!")
            return
        
        if member.bot:
            await ctx.send(f"{ctx.author.mention}, you cannot trade with a bot!")
            return
        
        offerer_id = ctx.author.id
        receiver_id = member.id
        
        # Check if both users exist in database
        self.cursor.execute("SELECT user_id FROM players WHERE user_id IN (?, ?)", (offerer_id, receiver_id))
        users = self.cursor.fetchall()
        
        if len(users) < 2:
            await ctx.send(f"{ctx.author.mention}, both users must have started their journey with `!start`!")
            return
        
        # Verify the offerer owns their card
        your_card = self.get_user_card(offerer_id, your_card_id)
        
        if not your_card:
            await ctx.send(f"{ctx.author.mention}, you don't own a card with ID `{your_card_id}`!")
            return
        
        # Verify the receiver owns their card
        their_card = self.get_user_card(receiver_id, their_card_id)
        
        if not their_card:
            await ctx.send(f"{ctx.author.mention}, {member.display_name} doesn't own a card with ID `{their_card_id}`!")
            return
        
        # Unpack card data
        _, your_card_name, your_rarity, your_level, your_equipped, your_evo = your_card
        _, their_card_name, their_rarity, their_level, their_equipped, their_evo = their_card
        
        # Check if either card is equipped
        if your_equipped:
            await ctx.send(f"{ctx.author.mention}, you can't trade your equipped card! Use `!unequip` first.")
            return
        
        if their_equipped:
            await ctx.send(f"{ctx.author.mention}, you can't request {member.display_name}'s equipped card!")
            return
        
        # Check for existing pending trades between these users
        self.cursor.execute("""
            SELECT id FROM trades 
            WHERE ((offerer_id = ? AND receiver_id = ?) OR (offerer_id = ? AND receiver_id = ?))
            AND status = 'pending'
        """, (offerer_id, receiver_id, receiver_id, offerer_id))
        
        existing = self.cursor.fetchone()
        
        if existing:
            await ctx.send(f"{ctx.author.mention}, there's already an active trade between you and {member.display_name}! Use `!trades` to view it.")
            return
        
        # Create a new trade in the database
        trade_timestamp = int(time.time())
        
        self.cursor.execute("""
            INSERT INTO trades (offerer_id, receiver_id, offer_card_id, request_card_id, status, timestamp)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (offerer_id, receiver_id, your_card_id, their_card_id, trade_timestamp))
        
        self.db.conn.commit()
        trade_id = self.cursor.lastrowid
        
        # Create a trade offer embed
        embed = discord.Embed(
            title="📤 New Trade Offer",
            description=f"{ctx.author.mention} wants to trade with {member.mention}!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name=f"{ctx.author.display_name} offers:",
            value=f"**{your_card_name}** (ID: `{your_card_id}`)\n"
                  f"Level {your_level} {your_rarity}" + (f" • Evolution Stage {your_evo}" if your_evo > 0 else ""),
            inline=True
        )
        
        embed.add_field(
            name=f"In exchange for {member.display_name}'s:",
            value=f"**{their_card_name}** (ID: `{their_card_id}`)\n"
                  f"Level {their_level} {their_rarity}" + (f" • Evolution Stage {their_evo}" if their_evo > 0 else ""),
            inline=True
        )
        
        embed.set_footer(text=f"Trade ID: {trade_id} • To accept: !accept {trade_id} • To decline: !decline {trade_id}")
        
        await ctx.send(embed=embed)
        
        # Also DM the trade receiver if they're not in the current channel
        try:
            dm_embed = embed.copy()
            dm_embed.description = f"{ctx.author.display_name} wants to trade with you!"
            
            await member.send(f"You received a trade offer from {ctx.author.display_name}!", embed=dm_embed)
        except discord.HTTPException:
            # Can't DM the user, just continue
            pass
    
    @commands.command(name="accept")
    async def accept_trade(self, ctx, trade_id: int):
        """Accept a pending trade offer"""
        user_id = ctx.author.id
        
        # Verify the trade exists and the user is the receiver
        self.cursor.execute("""
            SELECT t.offerer_id, t.receiver_id, t.offer_card_id, t.request_card_id,
                   o.name AS offer_name, r.name AS request_name,
                   o.user_id AS o_user_id, r.user_id AS r_user_id,
                   o.equipped AS o_equipped, r.equipped AS r_equipped
            FROM trades t
            JOIN usercards o ON t.offer_card_id = o.id
            JOIN usercards r ON t.request_card_id = r.id
            WHERE t.id = ? AND t.status = 'pending'
        """, (trade_id,))
        
        trade = self.cursor.fetchone()
        
        if not trade:
            await ctx.send(f"{ctx.author.mention}, that trade doesn't exist or has already been completed!")
            return
        
        offerer_id, receiver_id, offer_card_id, request_card_id, offer_name, request_name, o_user_id, r_user_id, o_equipped, r_equipped = trade
        
        # Verify the user is the receiver
        if user_id != receiver_id:
            await ctx.send(f"{ctx.author.mention}, this trade offer was not sent to you!")
            return
        
        # Double-check card ownership hasn't changed
        if o_user_id != offerer_id or r_user_id != receiver_id:
            # Update trade status
            self.cursor.execute("UPDATE trades SET status = 'cancelled' WHERE id = ?", (trade_id,))
            self.db.conn.commit()
            
            await ctx.send(f"{ctx.author.mention}, this trade is no longer valid because card ownership has changed!")
            return
        
        # Check if cards are still unequipped
        if o_equipped or r_equipped:
            # Update trade status
            self.cursor.execute("UPDATE trades SET status = 'cancelled' WHERE id = ?", (trade_id,))
            self.db.conn.commit()
            
            await ctx.send(f"{ctx.author.mention}, this trade is no longer valid because one of the cards is now equipped!")
            return
        
        # Perform the trade by swapping user_id fields
        self.cursor.execute("UPDATE usercards SET user_id = ? WHERE id = ?", (receiver_id, offer_card_id))
        self.cursor.execute("UPDATE usercards SET user_id = ? WHERE id = ?", (offerer_id, request_card_id))
        
        # Update trade status
        self.cursor.execute("UPDATE trades SET status = 'accepted' WHERE id = ?", (trade_id,))
        self.db.conn.commit()
        
        # Get the offerer user
        offerer = self.bot.get_user(offerer_id)
        offerer_name = offerer.display_name if offerer else f"User {offerer_id}"
        
        # Create success embed
        embed = discord.Embed(
            title="🔄 Trade Completed",
            description=f"The trade between {offerer_name} and {ctx.author.display_name} has been completed!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name=f"{offerer_name} received:",
            value=f"**{request_name}** (ID: `{request_card_id}`)",
            inline=True
        )
        
        embed.add_field(
            name=f"{ctx.author.display_name} received:",
            value=f"**{offer_name}** (ID: `{offer_card_id}`)",
            inline=True
        )
        
        embed.set_footer(text=f"Trade ID: {trade_id}")
        
        await ctx.send(embed=embed)
        
        # Notify the offerer if possible
        if offerer:
            try:
                await offerer.send(f"{ctx.author.display_name} accepted your trade offer!", embed=embed)
            except discord.HTTPException:
                # Can't DM, just continue
                pass
    
    @commands.command(name="decline")
    async def decline_trade(self, ctx, trade_id: int):
        """Decline a pending trade offer"""
        user_id = ctx.author.id
        
        # Verify the trade exists and the user is involved
        self.cursor.execute("""
            SELECT offerer_id, receiver_id, offer_card_id, request_card_id
            FROM trades
            WHERE id = ? AND status = 'pending' AND (offerer_id = ? OR receiver_id = ?)
        """, (trade_id, user_id, user_id))
        
        trade = self.cursor.fetchone()
        
        if not trade:
            await ctx.send(f"{ctx.author.mention}, that trade doesn't exist, has already been completed, or you're not involved in it!")
            return
        
        offerer_id, receiver_id, offer_card_id, request_card_id = trade
        
        # Update trade status
        self.cursor.execute("UPDATE trades SET status = 'rejected' WHERE id = ?", (trade_id,))
        self.db.conn.commit()
        
        # Get the other user
        other_id = offerer_id if user_id == receiver_id else receiver_id
        other_user = self.bot.get_user(other_id)
        other_name = other_user.display_name if other_user else f"User {other_id}"
        
        # Create decline embed
        embed = discord.Embed(
            title="❌ Trade Declined",
            description=f"The trade (ID: `{trade_id}`) has been declined by {ctx.author.display_name}.",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
        
        # Notify the other user if possible
        if other_user:
            try:
                await other_user.send(f"{ctx.author.display_name} declined your trade offer!", embed=embed)
            except discord.HTTPException:
                # Can't DM, just continue
                pass
    
    @commands.command(name="trades")
    async def view_trades(self, ctx):
        """View your pending trades"""
        user_id = ctx.author.id
        
        # Get all pending trades for this user
        trades = self.get_pending_trades(user_id)
        
        if not trades:
            await ctx.send(f"{ctx.author.mention}, you have no pending trades!")
            return
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Pending Trades",
            color=discord.Color.blue()
        )
        
        # Add each trade to the embed
        for trade in trades:
            trade_id, offerer_id, receiver_id, offer_card_id, request_card_id, offer_name, request_name, offer_rarity, request_rarity, offer_level, request_level = trade
            
            # Determine if this user is the offerer or receiver
            is_offerer = offerer_id == user_id
            
            other_id = receiver_id if is_offerer else offerer_id
            other_user = self.bot.get_user(other_id)
            other_name = other_user.display_name if other_user else f"User {other_id}"
            
            if is_offerer:
                trade_desc = f"You offered **{offer_name}** (Lvl {offer_level}, {offer_rarity})\n" \
                             f"For {other_name}'s **{request_name}** (Lvl {request_level}, {request_rarity})"
                trade_status = "Waiting for response"
            else:
                trade_desc = f"{other_name} offered **{offer_name}** (Lvl {offer_level}, {offer_rarity})\n" \
                             f"For your **{request_name}** (Lvl {request_level}, {request_rarity})"
                trade_status = f"Use `!accept {trade_id}` or `!decline {trade_id}`"
            
            embed.add_field(
                name=f"Trade ID: {trade_id}",
                value=f"{trade_desc}\n**Status:** {trade_status}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="tradehistory", aliases=["th"])
    async def trade_history(self, ctx, limit: int = 5):
        """View your trade history"""
        user_id = ctx.author.id
        
        if limit > 10:
            limit = 10
        elif limit < 1:
            limit = 1
        
        # Get completed trades for this user
        self.cursor.execute("""
            SELECT t.id, t.offerer_id, t.receiver_id, t.status, t.timestamp,
                   o.name AS offer_name, r.name AS request_name
            FROM trades t
            JOIN usercards o ON t.offer_card_id = o.id
            JOIN usercards r ON t.request_card_id = r.id
            WHERE (t.offerer_id = ? OR t.receiver_id = ?) AND t.status != 'pending'
            ORDER BY t.timestamp DESC
            LIMIT ?
        """, (user_id, user_id, limit))
        
        history = self.cursor.fetchall()
        
        if not history:
            await ctx.send(f"{ctx.author.mention}, you have no trade history!")
            return
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Trade History",
            description=f"Showing the last {len(history)} trades",
            color=discord.Color.gold()
        )
        
        # Add each trade to the embed
        for trade in history:
            trade_id, offerer_id, receiver_id, status, timestamp, offer_name, request_name = trade
            
            # Determine if this user is the offerer or receiver
            is_offerer = offerer_id == user_id
            
            other_id = receiver_id if is_offerer else offerer_id
            other_user = self.bot.get_user(other_id)
            other_name = other_user.display_name if other_user else f"User {other_id}"
            
            # Format timestamp
            import datetime
            trade_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            
            # Format status with emoji
            if status == "accepted":
                status_text = "✅ Accepted"
            elif status == "rejected":
                status_text = "❌ Declined"
            else:  # cancelled
                status_text = "🚫 Cancelled"
            
            if is_offerer:
                trade_desc = f"You offered **{offer_name}**\n" \
                             f"For {other_name}'s **{request_name}**"
            else:
                trade_desc = f"{other_name} offered **{offer_name}**\n" \
                             f"For your **{request_name}**"
            
            embed.add_field(
                name=f"Trade ID: {trade_id} ({trade_time})",
                value=f"{trade_desc}\n**Status:** {status_text}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Trading(bot))
