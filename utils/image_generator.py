"""
Image generator for battle visuals and card images.
Creates dynamic HP/MP bars and card battle animations.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import io
import base64
import discord
import asyncio

class ImageGenerator:
    def __init__(self):
        # Create static directory if it doesn't exist
        os.makedirs('static/images/battle', exist_ok=True)
        
        # Initialize fonts
        self.font_dir = "static/fonts"
        os.makedirs(self.font_dir, exist_ok=True)
        
        # Default sizes
        self.bar_width = 300
        self.bar_height = 30
        self.padding = 5
        
        # Colors
        self.hp_color = (65, 209, 82)  # Green
        self.hp_bg_color = (40, 40, 40)  # Dark gray
        self.mp_color = (72, 118, 255)  # Blue
        self.mp_bg_color = (40, 40, 40)  # Dark gray
        self.text_color = (255, 255, 255)  # White
        
    def generate_resource_bar(self, current, maximum, is_hp=True, save_path=None):
        """
        Generate an HP or MP bar image
        
        Args:
            current (int): Current value
            maximum (int): Maximum value
            is_hp (bool): True for HP bar, False for MP bar
            save_path (str, optional): Path to save the image
            
        Returns:
            discord.File: Discord file object containing the image
        """
        # Create a new image
        img = Image.new('RGBA', (self.bar_width, self.bar_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate fill width
        fill_ratio = max(0, min(1, current / maximum))
        fill_width = int((self.bar_width - 2 * self.padding) * fill_ratio)
        
        # Colors based on bar type
        if is_hp:
            fill_color = self.hp_color
            bg_color = self.hp_bg_color
            label = "HP"
        else:
            fill_color = self.mp_color
            bg_color = self.mp_bg_color
            label = "MP"
        
        # Draw background
        draw.rectangle(
            [(self.padding, self.padding), 
             (self.bar_width - self.padding, self.bar_height - self.padding)],
            fill=bg_color,
            outline=(255, 255, 255)
        )
        
        # Draw filled portion
        if fill_width > 0:
            draw.rectangle(
                [(self.padding + 2, self.padding + 2), 
                 (self.padding + fill_width, self.bar_height - self.padding - 2)],
                fill=fill_color
            )
        
        # Try to add text using a basic font
        try:
            # Create a default font
            font = ImageFont.load_default()
            
            # Draw text
            text = f"{label}: {current}/{maximum}"
            
            # Calculate text size and position
            text_width = draw.textlength(text, font)
            text_x = (self.bar_width - text_width) // 2
            text_y = (self.bar_height - font.size) // 2
            
            # Draw text with outline
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((text_x + dx, text_y + dy), text, fill=(0, 0, 0), font=font)
            draw.text((text_x, text_y), text, fill=self.text_color, font=font)
            
        except Exception as e:
            print(f"Error adding text to bar: {e}")
        
        # Save the image if path provided
        if save_path:
            img.save(save_path, format="PNG")
        
        # Convert to bytes for Discord
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Create a Discord file
        return discord.File(buffer, filename=f"{label.lower()}_bar.png")
    
    def generate_battle_scene(self, player_card, enemy_card, player_hp, player_max_hp, 
                             player_mp, player_max_mp, enemy_hp, enemy_max_hp, 
                             enemy_mp, enemy_max_mp, save_path=None):
        """
        Generate a complete battle scene with both combatants
        
        Args:
            player_card (dict): Player card data
            enemy_card (dict): Enemy card data
            player_hp, player_max_hp (int): Player HP values
            player_mp, player_max_mp (int): Player MP values
            enemy_hp, enemy_max_hp (int): Enemy HP values
            enemy_mp, enemy_max_mp (int): Enemy MP values
            save_path (str, optional): Path to save the image
            
        Returns:
            discord.File: Discord file object containing the scene
        """
        # Create a new image (landscape orientation)
        width, height = 800, 400
        img = Image.new('RGBA', (width, height), (20, 20, 30, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw background (simple gradient)
        for y in range(height):
            # Create a simple gradient background
            color = (20, 20, 30 + int(y * 40 / height))
            draw.line([(0, y), (width, y)], fill=color)
        
        # Draw dividing line
        draw.line([(width // 2, 0), (width // 2, height)], fill=(100, 100, 100), width=2)
        
        # Generate HP/MP bars for player
        player_hp_bar = self.generate_resource_bar_image(player_hp, player_max_hp, True)
        player_mp_bar = self.generate_resource_bar_image(player_mp, player_max_mp, False)
        
        # Generate HP/MP bars for enemy
        enemy_hp_bar = self.generate_resource_bar_image(enemy_hp, enemy_max_hp, True)
        enemy_mp_bar = self.generate_resource_bar_image(enemy_mp, enemy_max_mp, False)
        
        # Calculate positions (player on left, enemy on right)
        player_section_width = width // 2
        enemy_section_width = width // 2
        
        # Player area (left side)
        player_area_top = 50  # Leave space for labels
        player_area_left = 50
        
        # Enemy area (right side)
        enemy_area_top = 50
        enemy_area_left = width // 2 + 50
        
        # Add player information
        try:
            font = ImageFont.load_default()
            
            # Player name and card
            player_text = f"{player_card['name']} (Lv.{player_card['level']} {player_card['rarity']})"
            draw.text((player_area_left, 20), player_text, fill=(255, 255, 255), font=font)
            
            # Enemy name and level
            enemy_text = f"{enemy_card['name']} (Lv.{enemy_card['level']} {enemy_card['rarity']})"
            draw.text((enemy_area_left, 20), enemy_text, fill=(255, 255, 255), font=font)
            
            # Player stats
            stats_text = f"ATK: {player_card['attack']} | DEF: {player_card['defense']} | SPD: {player_card['speed']}"
            draw.text((player_area_left, player_area_top + 30), stats_text, fill=(220, 220, 220), font=font)
            
            # Enemy stats
            enemy_stats_text = f"ATK: {enemy_card['attack']} | DEF: {enemy_card['defense']} | SPD: {enemy_card['speed']}"
            draw.text((enemy_area_left, enemy_area_top + 30), enemy_stats_text, fill=(220, 220, 220), font=font)
            
            # Add skill info
            player_skill_text = f"Skill: {player_card['skill']} (MP: {player_card['mp_cost']})"
            draw.text((player_area_left, player_area_top + 60), player_skill_text, fill=(180, 180, 255), font=font)
            
            enemy_skill_text = f"Skill: {enemy_card['skill']} (MP: {enemy_card['mp_cost']})"
            draw.text((enemy_area_left, enemy_area_top + 60), enemy_skill_text, fill=(180, 180, 255), font=font)
            
        except Exception as e:
            print(f"Error adding text to battle scene: {e}")
        
        # Paste player bars
        img.paste(player_hp_bar, (player_area_left, player_area_top + 90), player_hp_bar)
        img.paste(player_mp_bar, (player_area_left, player_area_top + 130), player_mp_bar)
        
        # Paste enemy bars
        img.paste(enemy_hp_bar, (enemy_area_left, enemy_area_top + 90), enemy_hp_bar)
        img.paste(enemy_mp_bar, (enemy_area_left, enemy_area_top + 130), enemy_mp_bar)
        
        # Draw character placeholder if no images
        player_image_area = (player_area_left, player_area_top + 170, 
                            player_area_left + 200, player_area_top + 370)
        enemy_image_area = (enemy_area_left, enemy_area_top + 170,
                           enemy_area_left + 200, enemy_area_top + 370)
        
        # Draw character placeholders
        draw.rectangle(player_image_area, outline=(200, 200, 200), width=2)
        draw.rectangle(enemy_image_area, outline=(200, 200, 200), width=2)
        
        # Save the image if path provided
        if save_path:
            img.save(save_path, format="PNG")
        
        # Convert to bytes for Discord
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Create a Discord file
        return discord.File(buffer, filename="battle_scene.png")
    
    def generate_resource_bar_image(self, current, maximum, is_hp=True):
        """
        Generate an HP or MP bar as PIL Image object for compositing
        
        Args:
            current (int): Current value
            maximum (int): Maximum value
            is_hp (bool): True for HP bar, False for MP bar
            
        Returns:
            PIL.Image: Image object with the bar
        """
        # Create a new image
        img = Image.new('RGBA', (self.bar_width, self.bar_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate fill width
        fill_ratio = max(0, min(1, current / maximum))
        fill_width = int((self.bar_width - 2 * self.padding) * fill_ratio)
        
        # Colors based on bar type
        if is_hp:
            fill_color = self.hp_color
            bg_color = self.hp_bg_color
            label = "HP"
        else:
            fill_color = self.mp_color
            bg_color = self.mp_bg_color
            label = "MP"
        
        # Draw background
        draw.rectangle(
            [(self.padding, self.padding), 
             (self.bar_width - self.padding, self.bar_height - self.padding)],
            fill=bg_color,
            outline=(255, 255, 255)
        )
        
        # Draw filled portion
        if fill_width > 0:
            draw.rectangle(
                [(self.padding + 2, self.padding + 2), 
                 (self.padding + fill_width, self.bar_height - self.padding - 2)],
                fill=fill_color
            )
        
        # Try to add text using a basic font
        try:
            # Create a default font
            font = ImageFont.load_default()
            
            # Draw text
            text = f"{label}: {current}/{maximum}"
            
            # Calculate text size and position
            text_width = draw.textlength(text, font)
            text_x = (self.bar_width - text_width) // 2
            text_y = (self.bar_height - font.size) // 2
            
            # Draw text with outline
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((text_x + dx, text_y + dy), text, fill=(0, 0, 0), font=font)
            draw.text((text_x, text_y), text, fill=self.text_color, font=font)
            
        except Exception as e:
            print(f"Error adding text to bar: {e}")
        
        return img
    
    def generate_card_image(self, card_data, save_path=None):
        """
        Generate a visual card image
        
        Args:
            card_data (dict): Card data
            save_path (str, optional): Path to save the image
            
        Returns:
            discord.File: Discord file object containing the card image
        """
        # Card dimensions
        width, height = 300, 420
        
        # Create a new image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Rarity colors
        rarity_colors = {
            "Common": (150, 150, 150),      # Gray
            "Uncommon": (0, 200, 0),        # Green
            "Rare": (0, 112, 221),          # Blue
            "Epic": (163, 53, 238),         # Purple
            "Legendary": (255, 215, 0)      # Gold
        }
        
        # Element colors
        element_colors = {
            "Fire": (255, 50, 50),
            "Water": (50, 150, 255),
            "Earth": (139, 69, 19),
            "Air": (200, 200, 200),
            "Electric": (255, 255, 0),
            "Ice": (173, 216, 230),
            "Light": (255, 255, 200),
            "Dark": (75, 0, 130),
            "Cute": (255, 182, 193),
            "Sweet": (255, 105, 180),
            "Star": (255, 223, 0)
        }
        
        # Get colors
        rarity_color = rarity_colors.get(card_data.get('rarity', 'Common'), (150, 150, 150))
        element_color = element_colors.get(card_data.get('element', 'Earth'), (139, 69, 19))
        
        # Draw card border with rarity color
        border_width = 5
        draw.rectangle([(0, 0), (width, height)], fill=(30, 30, 30), outline=rarity_color, width=border_width)
        
        # Draw card header
        header_height = 50
        draw.rectangle([(border_width, border_width), (width - border_width, header_height)], 
                      fill=rarity_color)
        
        # Draw element symbol in corner
        element_square_size = 40
        draw.rectangle(
            [(width - element_square_size - border_width, border_width), 
             (width - border_width, element_square_size + border_width)], 
            fill=element_color
        )
        
        # Add card info
        try:
            font = ImageFont.load_default()
            big_font_size = 16
            
            # Card name
            name = card_data.get('name', 'Unknown Card')
            draw.text((border_width + 5, border_width + 5), name, fill=(255, 255, 255), font=font)
            
            # Element symbol
            element = card_data.get('element', 'Earth')
            draw.text((width - element_square_size - border_width + 5, border_width + 5), 
                      element[0], fill=(255, 255, 255), font=font)
            
            # Image area placeholder
            image_area_top = header_height + 5
            image_area_height = 150
            draw.rectangle(
                [(border_width, image_area_top), 
                 (width - border_width, image_area_top + image_area_height)],
                outline=(100, 100, 100)
            )
            
            # Stats area
            stats_top = image_area_top + image_area_height + 10
            
            # Stats
            attack = card_data.get('attack', 0)
            defense = card_data.get('defense', 0)
            speed = card_data.get('speed', 0)
            
            draw.text((border_width + 10, stats_top), f"ATK: {attack}", fill=(255, 100, 100), font=font)
            draw.text((border_width + 10, stats_top + 20), f"DEF: {defense}", fill=(100, 100, 255), font=font)
            draw.text((border_width + 10, stats_top + 40), f"SPD: {speed}", fill=(100, 255, 100), font=font)
            
            # Level
            level = card_data.get('level', 1)
            evo_stage = card_data.get('evo_stage', 1)
            
            level_text = f"Lv.{level} (Evo {evo_stage})"
            draw.text((width - 100, stats_top + 20), level_text, fill=(255, 255, 255), font=font)
            
            # Skill area
            skill_top = stats_top + 70
            skill_name = card_data.get('skill', 'Unknown Skill')
            skill_desc = card_data.get('skill_description', 'No description')
            mp_cost = card_data.get('mp_cost', 10)
            
            # Add skill box
            draw.rectangle(
                [(border_width, skill_top), 
                 (width - border_width, height - border_width)],
                fill=(50, 50, 60),
                outline=(100, 100, 100)
            )
            
            # Add skill info
            draw.text((border_width + 5, skill_top + 5), 
                      f"Skill: {skill_name} (MP: {mp_cost})", 
                      fill=(180, 180, 255), font=font)
            
            # Wrap skill description
            desc_top = skill_top + 30
            desc_width = width - (2 * border_width) - 10
            
            # Simple text wrapping
            words = skill_desc.split()
            line = ""
            y_offset = 0
            
            for word in words:
                test_line = line + word + " "
                test_width = draw.textlength(test_line, font)
                
                if test_width > desc_width:
                    draw.text((border_width + 5, desc_top + y_offset), line, fill=(255, 255, 255), font=font)
                    line = word + " "
                    y_offset += 20
                else:
                    line = test_line
            
            # Draw remaining text
            if line:
                draw.text((border_width + 5, desc_top + y_offset), line, fill=(255, 255, 255), font=font)
            
            # Add anime series
            anime_series = card_data.get('anime_series', '')
            if anime_series:
                draw.text(
                    (border_width + 5, height - border_width - 20), 
                    f"Series: {anime_series}", 
                    fill=(200, 200, 200), 
                    font=font
                )
            
        except Exception as e:
            print(f"Error adding text to card: {e}")
        
        # Save the image if path provided
        if save_path:
            img.save(save_path, format="PNG")
        
        # Convert to bytes for Discord
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Create a Discord file
        return discord.File(buffer, filename=f"card_{card_data.get('id', 'unknown')}.png")

# Singleton instance
image_generator = ImageGenerator()