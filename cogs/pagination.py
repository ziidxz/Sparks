import discord
from discord.ext import commands
from discord import ui

class PaginationView(ui.View):
    """A reusable pagination view for Discord embeds with next/previous buttons."""
    
    def __init__(self, embeds, author_id, timeout=60):
        """
        Initialize the pagination view.
        
        Args:
            embeds (list): List of discord.Embed objects to paginate through
            author_id (int): Discord ID of the user who can interact with the buttons
            timeout (int): Time in seconds before the view times out
        """
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0
        self.total_pages = len(embeds)
        
        # Update the footer of each embed to show page numbers
        for i, embed in enumerate(self.embeds):
            if embed.footer.text:
                embed.set_footer(text=f"{embed.footer.text} • Page {i+1}/{self.total_pages}")
            else:
                embed.set_footer(text=f"Page {i+1}/{self.total_pages}")
        
        # Disable/enable buttons based on initial page
        self._update_buttons()
    
    async def interaction_check(self, interaction):
        """Check if the interaction is from the original command author."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        return True
    
    def _update_buttons(self):
        """Update button states based on current page."""
        # First page - disable previous button
        if self.current_page == 0:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            
        # Last page - disable next button
        if self.current_page == self.total_pages - 1:
            self.next_button.disabled = True
            self.last_page_button.disabled = True
        else:
            self.next_button.disabled = False
            self.last_page_button.disabled = False
    
    @ui.button(emoji="⏮️", style=discord.ButtonStyle.blurple)
    async def first_page_button(self, interaction, button):
        """Go to the first page."""
        self.current_page = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction, button):
        """Go to the previous page."""
        self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction, button):
        """Go to the next page."""
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def last_page_button(self, interaction, button):
        """Go to the last page."""
        self.current_page = self.total_pages - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

class ConfirmView(ui.View):
    """A simple confirmation dialog with Yes/No buttons."""
    
    def __init__(self, author_id, timeout=30):
        """
        Initialize the confirmation view.
        
        Args:
            author_id (int): Discord ID of the user who can interact with the buttons
            timeout (int): Time in seconds before the view times out
        """
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value = None  # Will be set to True or False when a button is pressed
    
    async def interaction_check(self, interaction):
        """Check if the interaction is from the original command author."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        return True
    
    @ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction, button):
        """Confirm button - sets value to True."""
        self.value = True
        self.stop()
        await interaction.response.edit_message(view=None)
    
    @ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction, button):
        """Cancel button - sets value to False."""
        self.value = False
        self.stop()
        await interaction.response.edit_message(view=None)

class Pagination(commands.Cog):
    """Provides pagination utilities for other cogs."""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def paginate(self, ctx, embeds):
        """
        Send a paginated message with the provided embeds.
        
        Args:
            ctx (commands.Context): The command context
            embeds (list): List of discord.Embed objects to paginate
        """
        if not embeds:
            return await ctx.send("No content to display.")
        
        if len(embeds) == 1:
            # If there's only one page, just send the embed without buttons
            return await ctx.send(embed=embeds[0])
        
        # Create and send the pagination view
        view = PaginationView(embeds, ctx.author.id)
        await ctx.send(embed=embeds[0], view=view)
    
    async def confirm(self, ctx, message):
        """
        Send a confirmation dialog and wait for user response.
        
        Args:
            ctx (commands.Context): The command context
            message (str): The confirmation message to display
            
        Returns:
            bool: True if confirmed, False if canceled, None if timed out
        """
        # Create and send the confirmation dialog
        embed = discord.Embed(
            title="Confirmation",
            description=message,
            color=discord.Color.yellow()
        )
        
        view = ConfirmView(ctx.author.id)
        msg = await ctx.send(embed=embed, view=view)
        
        # Wait for the view to stop (button press or timeout)
        await view.wait()
        
        # Return the value (True, False, or None if timed out)
        return view.value

async def setup(bot):
    await bot.add_cog(Pagination(bot))
    print("Pagination cog loaded")