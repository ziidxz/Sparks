import discord
from discord.ext import commands
import math

class Materials(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.cursor = self.db.conn.cursor()
        self.materials_per_page = 10
    
    def get_user_materials(self, user_id):
        """Get all materials owned by a user."""
        self.cursor.execute("""
            SELECT m.id, m.name, m.description, m.rarity, m.image_url, um.quantity
            FROM materials m
            JOIN user_materials um ON m.id = um.material_id
            WHERE um.user_id = ? AND um.quantity > 0
            ORDER BY m.rarity DESC, m.name ASC
        """, (user_id,))
        
        return self.cursor.fetchall()
    
    def get_material_details(self, material_id):
        """Get detailed information about a specific material."""
        self.cursor.execute("""
            SELECT id, name, description, rarity, image_url
            FROM materials
            WHERE id = ?
        """, (material_id,))
        
        return self.cursor.fetchone()
    
    def get_cards_using_material(self, material_id):
        """Get cards that use this material for evolution."""
        self.cursor.execute("""
            SELECT er.base_card_id, er.evolution_stage, er.quantity, c.name
            FROM evolution_requirements er
            JOIN cards c ON er.base_card_id = c.id
            WHERE er.material_id = ?
            ORDER BY c.rarity DESC, c.name ASC
        """, (material_id,))
        
        return self.cursor.fetchall()
    
    @commands.command(name="materials", aliases=["mats"])
    async def materials_list(self, ctx, page: int = 1):
        """View your evolution materials and their quantities"""
        user_id = ctx.author.id
        
        # Get user's materials
        materials = self.get_user_materials(user_id)
        
        if not materials:
            await ctx.send(f"{ctx.author.mention}, you don't have any materials yet! Defeat bosses to earn materials.")
            return
        
        # Calculate total pages
        total_pages = math.ceil(len(materials) / self.materials_per_page)
        
        # Validate page number
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        # Calculate range for current page
        start_idx = (page - 1) * self.materials_per_page
        end_idx = start_idx + self.materials_per_page
        current_page_materials = materials[start_idx:end_idx]
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Materials",
            description=f"Page {page}/{total_pages} · Total Materials: {len(materials)}",
            color=discord.Color.dark_gold()
        )
        
        # Group by rarity
        rarities = {}
        for mat_id, name, desc, rarity, image_url, quantity in current_page_materials:
            if rarity not in rarities:
                rarities[rarity] = []
            
            rarities[rarity].append((mat_id, name, desc, quantity, image_url))
        
        # Add materials by rarity
        for rarity in ["Legendary", "Epic", "Rare", "Uncommon", "Common"]:
            if rarity in rarities:
                mats_text = ""
                for mat_id, name, desc, quantity, _ in rarities[rarity]:
                    mats_text += f"**{name}** (x{quantity})\n"
                    mats_text += f"*{desc[:50]}{'...' if len(desc) > 50 else ''}*\n\n"
                
                embed.add_field(
                    name=f"{rarity} Materials",
                    value=mats_text,
                    inline=False
                )
        
        # Add navigation instructions
        embed.set_footer(text=f"Use !materials {page-1} or !materials {page+1} to navigate pages · !matinfo [name] for details")
        
        # Set thumbnail
        if current_page_materials and current_page_materials[0][4]:  # If first material has image
            embed.set_thumbnail(url=current_page_materials[0][4])
        
        await ctx.send(embed=embed)
    
    @commands.command(name="matinfo", aliases=["materialinfo"])
    async def material_info(self, ctx, *, material_name: str):
        """View detailed information about a specific material"""
        user_id = ctx.author.id
        
        # Find material by name (case insensitive)
        self.cursor.execute("""
            SELECT m.id, m.name, m.description, m.rarity, m.image_url, um.quantity
            FROM materials m
            LEFT JOIN user_materials um ON m.id = um.material_id AND um.user_id = ?
            WHERE LOWER(m.name) LIKE ?
        """, (user_id, f"%{material_name.lower()}%"))
        
        materials = self.cursor.fetchall()
        
        if not materials:
            await ctx.send(f"{ctx.author.mention}, couldn't find a material matching '{material_name}'.")
            return
        
        # Select the best match (exact match or first result)
        selected_material = None
        for material in materials:
            if material[1].lower() == material_name.lower():
                selected_material = material
                break
        
        if not selected_material:
            selected_material = materials[0]
        
        mat_id, name, desc, rarity, image_url, quantity = selected_material
        quantity = quantity or 0  # Handle case where user doesn't have the material
        
        # Get cards that use this material
        cards_using = self.get_cards_using_material(mat_id)
        
        # Create embed
        from cogs.colorembed import ColorEmbed
        embed = discord.Embed(
            title=f"Material: {name}",
            description=desc,
            color=discord.Color.gold() if rarity == "Legendary" else
                  discord.Color.purple() if rarity == "Epic" else
                  discord.Color.blue() if rarity == "Rare" else
                  discord.Color.green() if rarity == "Uncommon" else
                  discord.Color.light_grey()
        )
        
        # Material stats
        embed.add_field(
            name="Details",
            value=f"**Rarity:** {rarity}\n"
                  f"**You own:** {quantity}",
            inline=False
        )
        
        # Used for evolution
        if cards_using:
            cards_text = ""
            for base_id, evo_stage, mat_qty, card_name in cards_using[:5]:  # Limit to 5 cards
                cards_text += f"**{card_name}** - Stage {evo_stage} to {evo_stage+1} (x{mat_qty} needed)\n"
            
            if len(cards_using) > 5:
                cards_text += f"*...and {len(cards_using) - 5} more cards*"
            
            embed.add_field(
                name="Used for Evolution",
                value=cards_text,
                inline=False
            )
        else:
            embed.add_field(
                name="Used for Evolution",
                value="Not currently used for any card evolutions in your collection.",
                inline=False
            )
        
        # How to obtain
        sources = []
        
        # Check if it drops from bosses
        self.cursor.execute("""
            SELECT b.name, bd.drop_rate, bd.min_quantity, bd.max_quantity
            FROM boss_drops bd
            JOIN bosses b ON bd.boss_id = b.id
            WHERE bd.material_id = ?
            ORDER BY b.level ASC
        """, (mat_id,))
        
        boss_drops = self.cursor.fetchall()
        
        if boss_drops:
            boss_text = ""
            for boss_name, drop_rate, min_qty, max_qty in boss_drops:
                drop_percent = drop_rate * 100
                boss_text += f"**{boss_name}** - {drop_percent:.1f}% chance ({min_qty}-{max_qty})\n"
            
            sources.append(("Boss Drops", boss_text))
        
        # Other sources (could be expanded later)
        if not sources:
            sources.append(("Sources", "This material can be obtained through special events or shop purchases."))
        
        for source_name, source_text in sources:
            embed.add_field(
                name=source_name,
                value=source_text,
                inline=False
            )
        
        # Set image
        if image_url:
            embed.set_thumbnail(url=image_url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="matgift", aliases=["giftml", "givemat"])
    @commands.has_permissions(administrator=True)
    async def gift_material(self, ctx, member: discord.Member, material_name: str, quantity: int = 1):
        """[Admin] Gift materials to a user"""
        if quantity < 1:
            await ctx.send("Quantity must be at least 1.")
            return
        
        target_id = member.id
        
        # Find material by name (case insensitive)
        self.cursor.execute("""
            SELECT id, name, rarity
            FROM materials
            WHERE LOWER(name) LIKE ?
        """, (f"%{material_name.lower()}%",))
        
        materials = self.cursor.fetchall()
        
        if not materials:
            await ctx.send(f"Couldn't find a material matching '{material_name}'.")
            return
        
        # Select the best match (exact match or first result)
        selected_material = None
        for material in materials:
            if material[1].lower() == material_name.lower():
                selected_material = material
                break
        
        if not selected_material:
            selected_material = materials[0]
        
        mat_id, name, rarity = selected_material
        
        # Check if user already has this material
        self.cursor.execute("""
            SELECT id, quantity
            FROM user_materials
            WHERE user_id = ? AND material_id = ?
        """, (target_id, mat_id))
        
        existing = self.cursor.fetchone()
        
        if existing:
            # Update quantity
            self.cursor.execute("""
                UPDATE user_materials
                SET quantity = quantity + ?
                WHERE id = ?
            """, (quantity, existing[0]))
        else:
            # Add new entry
            self.cursor.execute("""
                INSERT INTO user_materials (user_id, material_id, quantity)
                VALUES (?, ?, ?)
            """, (target_id, mat_id, quantity))
        
        self.db.conn.commit()
        
        # Create success embed
        embed = discord.Embed(
            title="Material Gifted",
            description=f"Gifted **{quantity}x {name}** to {member.mention}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Material Details",
            value=f"**Name:** {name}\n"
                  f"**Rarity:** {rarity}\n"
                  f"**Quantity:** {quantity}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="matstats")
    async def material_stats(self, ctx):
        """View statistics about your material collection"""
        user_id = ctx.author.id
        
        # Get user's materials
        materials = self.get_user_materials(user_id)
        
        if not materials:
            await ctx.send(f"{ctx.author.mention}, you don't have any materials yet! Defeat bosses to earn materials.")
            return
        
        # Count by rarity
        rarity_counts = {
            "Legendary": 0,
            "Epic": 0,
            "Rare": 0,
            "Uncommon": 0,
            "Common": 0
        }
        
        total_materials = 0
        
        for _, _, _, rarity, _, quantity in materials:
            rarity_counts[rarity] += quantity
            total_materials += quantity
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Material Statistics",
            description=f"Total Materials: {total_materials}",
            color=discord.Color.gold()
        )
        
        # Rarity breakdown
        rarity_text = ""
        for rarity, count in rarity_counts.items():
            if count > 0:
                emoji = "✨" if rarity == "Legendary" else "🔥" if rarity == "Epic" else "💫" if rarity == "Rare" else "⭐" if rarity == "Uncommon" else "🔹"
                rarity_text += f"{emoji} **{rarity}:** {count} ({count/total_materials*100:.1f}%)\n"
        
        embed.add_field(
            name="Material Breakdown",
            value=rarity_text,
            inline=False
        )
        
        # Evolution potential
        self.cursor.execute("""
            SELECT c.id, c.name, c.rarity, c.evolution_stage
            FROM usercards c
            WHERE c.user_id = ? AND c.base_card_id IN (
                SELECT DISTINCT er.base_card_id
                FROM evolution_requirements er
            )
            ORDER BY c.rarity DESC, c.level DESC
        """, (user_id,))
        
        evolvable_cards = self.cursor.fetchall()
        
        if evolvable_cards:
            evolution_text = ""
            cards_checked = 0
            
            for card_id, card_name, card_rarity, evo_stage in evolvable_cards:
                # Get materials needed for this card's evolution
                self.cursor.execute("""
                    SELECT er.material_id, er.quantity, m.name
                    FROM evolution_requirements er
                    JOIN materials m ON er.material_id = m.id
                    WHERE er.base_card_id = ? AND er.evolution_stage = ?
                """, (card_id, evo_stage))
                
                req_materials = self.cursor.fetchall()
                
                if not req_materials:
                    continue
                
                # Check if user has all materials
                can_evolve = True
                missing_mats = []
                
                for mat_id, req_qty, mat_name in req_materials:
                    # Get user's quantity
                    self.cursor.execute("""
                        SELECT quantity
                        FROM user_materials
                        WHERE user_id = ? AND material_id = ?
                    """, (user_id, mat_id))
                    
                    user_qty = self.cursor.fetchone()
                    user_qty = user_qty[0] if user_qty else 0
                    
                    if user_qty < req_qty:
                        can_evolve = False
                        missing_mats.append((mat_name, user_qty, req_qty))
                
                # Add to text if we haven't checked too many cards yet
                if cards_checked < 3:
                    if can_evolve:
                        evolution_text += f"✅ **{card_name}** - Ready to evolve!\n"
                    else:
                        evolution_text += f"❌ **{card_name}** - Missing materials:\n"
                        for mat_name, user_qty, req_qty in missing_mats[:2]:  # Limit to 2 materials
                            evolution_text += f"  • {mat_name}: {user_qty}/{req_qty}\n"
                        
                        if len(missing_mats) > 2:
                            evolution_text += f"  • *and {len(missing_mats) - 2} more...*\n"
                
                cards_checked += 1
            
            if evolution_text:
                if cards_checked > 3:
                    evolution_text += f"\n*...and {cards_checked - 3} more cards*"
                
                embed.add_field(
                    name="Evolution Potential",
                    value=evolution_text,
                    inline=False
                )
        
        # Add tips
        tips = [
            "Defeat bosses to earn rare materials!",
            "Higher level bosses drop rarer materials.",
            "Some materials are only available from specific bosses.",
            "Save your legendary materials for your best cards.",
            "Check which cards can evolve with !evolist"
        ]
        
        embed.add_field(
            name="Tips",
            value="• " + "\n• ".join(random.sample(tips, 2)),
            inline=False
        )
        
        embed.set_footer(text="Use !materials to view all materials • !matinfo [name] for details")
        
        await ctx.send(embed=embed)

async def setup(bot):
    import random  # Import here to avoid circular import
    await bot.add_cog(Materials(bot))
