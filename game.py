import pygame as pg
import sys
import gi
import random
from enum import Enum
import time
import math
from abc import ABC, abstractmethod
from gettext import gettext as _
from player import Player
from player import Bot
from player import Difficulty
from animation import Animation
from particle import Particle   
from config import Theme

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

WIDTH, HEIGHT = 1200, 800
FPS = 60

class GameMode(Enum):
    VS_BOT = 1
    LOCAL_MULTIPLAYER = 2

class Game(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.running = True
        self.game_mode = GameMode.VS_BOT
        self.difficulty = Difficulty.MEDIUM
        self.canvas = None
        self.show_help = False
        self.clock = None
        self.theme = Theme.LIGHT
        self.animations = []
        self.particles = []
        self.move_history = []
        self.show_menu = True
        self.bot = Bot(self.difficulty)
        self.bot_thinking = False
        self.bot_start_time = 0
        self.bot_move_delay = 1
        self.squares = {}
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        self.hover_effects = {}
        self.button_animations = {}
        self.transition_alpha = 0
        self.transition_target = 0
        self.last_frame_time = time.time()
        self.screen = None
        self.reset_game()
        
        self.font_small = None
        self.font = None
        self.font_large = None
        self.title_font = None
        
        self.bot_avatar = None
        self.bot_thinking_animation = 0

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.theme == Theme.LIGHT:
            self.theme = Theme.DARK
        else:
            self.theme = Theme.LIGHT
        
        for _ in range(20):
            x = random.randint(100, self.screen_width - 100)
            y = random.randint(100, self.screen_height - 100)
            self.create_particles(x, y, 1, self.theme['PRIMARY'])

    def set_canvas(self, canvas):
        self.canvas = canvas
        if self.screen:
            pg.display.set_caption(_("Euclid's Game"))

    def toggle_help(self):
        self.show_help = not self.show_help

    def run(self):
        pg.init()
        pg.font.init()
        
        self.clock = pg.time.Clock()
        
        self.screen = pg.display.get_surface()
        
        if self.screen:
            self.screen_width = self.screen.get_width()
            self.screen_height = self.screen.get_height()
        else:
            self.screen_width = WIDTH
            self.screen_height = HEIGHT
            self.screen = pg.display.set_mode((WIDTH, HEIGHT))
            pg.display.set_caption("Euclid's Game")
        
        self.font_small = pg.font.Font(None, 24)
        self.font = pg.font.Font(None, 36)
        self.font_large = pg.font.Font(None, 48)
        self.title_font = pg.font.Font(None, 72)
        
        self.bot_avatar = self.create_enhanced_bot_avatar()
        
        self.setup_squares()

        while self.running:
            while Gtk.events_pending():
                Gtk.main_iteration()

            self.handle_events()
            
            current_time = time.time()
            dt = current_time - self.last_frame_time
            self.last_frame_time = current_time
            
            self.update(dt)
            self.draw()
            self.clock.tick(FPS)

        pg.quit()
        sys.exit(0)

    def setup_squares(self):
        available_width = self.screen_width - 100
        available_height = self.screen_height - 250
        
        square_size = min((available_width // 10) - 8, (available_height // 10) - 8, 65)
        margin = 8
        
        grid_width = 10 * (square_size + margin) - margin
        grid_height = 10 * (square_size + margin) - margin
        grid_start_x = (self.screen_width - grid_width) // 2
        grid_start_y = (self.screen_height - grid_height) // 2 + 60
        
        for i in range(100):
            row = i // 10
            col = i % 10
            x = grid_start_x + col * (square_size + margin)
            y = grid_start_y + row * (square_size + margin)
            self.squares[i + 1] = pg.Rect(x, y, square_size, square_size)

    def create_enhanced_bot_avatar(self):
        image_path = "assets/robot.png" 
        
        try:
            avatar_image = pg.image.load(image_path)
            
            original_rect = avatar_image.get_rect()
            
            scale_factor = min(120 / original_rect.width, 120 / original_rect.height)
            new_width = int(original_rect.width * scale_factor)
            new_height = int(original_rect.height * scale_factor)
            
            avatar_image = pg.transform.smoothscale(avatar_image, (new_width, new_height))
            
            surface = pg.Surface((120, 120), pg.SRCALPHA)
            x = (120 - new_width) // 2
            y = (120 - new_height) // 2
            surface.blit(avatar_image, (x, y))
            
            return surface
            
        except Exception as e:
            print(f"Error loading bot avatar: {e}")
            return self.create_fallback_bot_avatar()

    def draw_rounded_rect_gradient(self, surface, rect, colors, radius):
        """Draw a rounded rectangle with gradient effect"""
        temp_surface = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
        
        for i in range(rect.height):
            ratio = i / rect.height
            color = [
                int(colors[0][j] * (1 - ratio) + colors[1][j] * ratio)
                for j in range(3)
            ]
            pg.draw.line(temp_surface, color, (0, i), (rect.width, i))
        
        mask_surface = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
        pg.draw.rect(mask_surface, (255, 255, 255, 255), 
                    (0, 0, rect.width, rect.height), border_radius=radius)
        
        temp_surface.blit(mask_surface, (0, 0), special_flags=pg.BLEND_ALPHA_SDL2)
        surface.blit(temp_surface, rect.topleft)

    def draw_gradient_background(self, surface, rect, colors):
        """Draw a smooth gradient background"""
        temp_surface = pg.Surface((rect.width, rect.height))
        for i in range(rect.height):
            ratio = i / rect.height
            color = [
                int(colors[0][j] * (1 - ratio) + colors[1][j] * ratio)
                for j in range(3)
            ]
            pg.draw.line(temp_surface, color, (0, i), (rect.width, i))
        surface.blit(temp_surface, rect.topleft)

    def create_particles(self, x, y, count=10, color=(59, 130, 246)):
        """Create particle effects for visual feedback"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            self.particles.append(
                Particle(x, y, color, velocity, random.uniform(2, 5), random.uniform(0.5, 1.5))
            )

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.handle_click(event.pos)
            elif event.type == pg.MOUSEMOTION:
                self.handle_hover(event.pos)
                
    def handle_hover(self, mouse_pos):
        """Handle hover effects for interactive elements"""
        current_time = time.time()
        
        for num, rect in self.squares.items():
            if rect.collidepoint(mouse_pos) and num in self.active_numbers:
                if num not in self.hover_effects:
                    self.hover_effects[num] = current_time
            else:
                if num in self.hover_effects:
                    del self.hover_effects[num]

    def handle_click(self, mouse_pos):
        if self.show_help:
            self.show_help = False
            return
        
        if self.show_menu:
            self.handle_menu_click(mouse_pos)
        elif not self.game_over:
            self.handle_game_click(mouse_pos)
        else:
            self.handle_game_over_click(mouse_pos)

    def handle_menu_click(self, mouse_pos):
        """Handle clicks in the menu screen - FIXED version"""
        menu_width = 600
        menu_height = 500
        menu_x = (self.screen_width - menu_width) // 2
        menu_y = (self.screen_height - menu_height) // 2 + 30
        
        button_width = 200
        button_height = 60
        button_y = menu_y + 120 
        
        bot_rect = pg.Rect(menu_x + menu_width // 2 - button_width - 20, button_y, 
                        button_width, button_height)
        if bot_rect.collidepoint(mouse_pos):
            self.game_mode = GameMode.VS_BOT
            return
        
        multi_rect = pg.Rect(menu_x + menu_width // 2 + 20, button_y, 
                            button_width, button_height)
        if multi_rect.collidepoint(mouse_pos):
            self.game_mode = GameMode.LOCAL_MULTIPLAYER
            return
        
        if self.game_mode == GameMode.VS_BOT:
            difficulties = [
                (Difficulty.EASY, "Easy"),
                (Difficulty.MEDIUM, "Medium"),
                (Difficulty.EXPERT, "Expert")
            ]
            
            diff_button_width = 400
            diff_button_height = 45
            diff_y = button_y + 140 
            
            for i, (diff, _) in enumerate(difficulties):
                diff_rect = pg.Rect(menu_x + menu_width // 2 - diff_button_width // 2,
                                diff_y + i * (diff_button_height + 10),
                                diff_button_width, diff_button_height)
                if diff_rect.collidepoint(mouse_pos):
                    self.set_difficulty(diff)
                    return
        
        start_rect = pg.Rect(menu_x + menu_width // 2 -130, menu_y + menu_height - 70, 250, 50)
        if start_rect.collidepoint(mouse_pos):
            self.show_menu = False
            self.reset_game()
            return
        
        theme_rect = pg.Rect(menu_x + menu_width - 50, menu_y + 15, 35, 35)
        if theme_rect.collidepoint(mouse_pos):
            self.toggle_theme()
            return
        
        help_rect = pg.Rect(menu_x + 15, menu_y + 15, 35, 35)
        if help_rect.collidepoint(mouse_pos):
            self.show_help = True
            return
    
    def handle_game_click(self, mouse_pos):
        if self.current_player == 1 or self.game_mode == GameMode.LOCAL_MULTIPLAYER:
            for num, rect in self.squares.items():
                if rect.collidepoint(mouse_pos):
                    if self.select_number(num):
                        self.create_particles(rect.centerx, rect.centery, 8)
                        
                        if len(self.selected_numbers) == 2:
                            if self.make_move():
                                self.check_game_over()

    def handle_game_over_click(self, mouse_pos):
        button_rect = pg.Rect(self.screen_width // 2 - 100, self.screen_height // 2 + 50, 200, 60)
        self.show_menu = True

    def update(self, dt):
        current_time = time.time()
        
        for anim in self.animations[:]:
            if not anim.active:
                self.animations.remove(anim)
        
        for particle in self.particles[:]:
            if not particle.update(dt):
                self.particles.remove(particle)
        
        if self.bot_thinking:
            self.bot_thinking_animation += dt * 4
        
        if self.transition_target != self.transition_alpha:
            diff = self.transition_target - self.transition_alpha
            self.transition_alpha += diff * dt * 5
            if abs(diff) < 0.1:
                self.transition_alpha = self.transition_target
        
        for num in list(self.hover_effects.keys()):
            if num not in self.active_numbers:
                del self.hover_effects[num]
        
        if (self.current_player == 2 and not self.game_over and 
            self.game_mode == GameMode.VS_BOT and not self.show_menu):
            if not self.bot_thinking:
                self.bot_thinking = True
                self.bot_start_time = current_time
                self.create_bot_thinking_particles()
            elif current_time - self.bot_start_time >= self.bot_move_delay:
                if self.bot_move():
                    if len(self.selected_numbers) == 2:
                        self.create_bot_move_animation()
                        
                        if self.make_move():
                            self.check_game_over()
                self.bot_thinking = False

    def create_bot_thinking_particles(self):
        """Create particles to show bot is thinking"""
        if self.game_mode == GameMode.VS_BOT and self.current_player == 2:
            bot_x = self.screen_width - 250
            bot_y = 50
            
            for i in range(8):
                angle = (i / 8) * 2 * math.pi
                x = bot_x + 40 * math.cos(angle)
                y = bot_y + 40 * math.sin(angle)
                velocity = (
                    -20 * math.cos(angle),
                    -20 * math.sin(angle)
                )
                self.particles.append(
                    Particle(x, y, self.theme['WARNING'], velocity, 2, 1.5)
                )

    def create_bot_move_animation(self):
        """Create enhanced animation for bot moves"""
        if len(self.selected_numbers) == 2:
            num1, num2 = self.selected_numbers
            start_pos = self.squares[num1].center
            end_pos = self.squares[num2].center
            diff = abs(num1 - num2)
            
            self.create_beam_effect(start_pos, end_pos)
            
            mid_pos = ((start_pos[0] + end_pos[0]) // 2,
                    (start_pos[1] + end_pos[1]) // 2)
            
            if diff in self.squares:
                anim = Animation(mid_pos, self.squares[diff].center, 
                            duration=1.0, easing='ease_bounce')
                anim.number = diff
                self.animations.append(anim)
                
                dest = self.squares[diff].center
                for i in range(20):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 150)
                    velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                    self.particles.append(
                        Particle(dest[0], dest[1], self.theme['GOLD'], 
                            velocity, random.uniform(2, 5), random.uniform(1, 2))
                    )

    def create_beam_effect(self, start_pos, end_pos):
        """Create a beam effect between two positions"""
        distance = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
        steps = int(distance / 20)
        
        for i in range(steps):
            t = i / steps
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
            
            x += random.uniform(-5, 5)
            y += random.uniform(-5, 5)
            
            self.particles.append(
                Particle(x, y, self.theme['PRIMARY_BRIGHT'], 
                    (0, 0), 4, 0.5)
            )

    def draw(self):
        colors = self.theme
        
        self.draw_gradient_background(self.screen, self.screen.get_rect(), colors['BG_GRADIENT'])

        if self.show_help:
            self.draw_enhanced_help(self.screen)
        elif self.show_menu:
            self.draw_enhanced_menu(self.screen)
        else:
            self.draw_enhanced_game_ui(self.screen)
            if self.game_over:
                self.draw_enhanced_game_over(self.screen)

        for particle in self.particles:
            particle.draw(self.screen)

        pg.display.flip()

    def draw_enhanced_help(self, screen):
        colors = self.theme
        
        overlay = pg.Surface((self.screen_width, self.screen_height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        
        help_width = 800
        help_height = 600
        help_x = (self.screen_width - help_width) // 2
        help_y = (self.screen_height - help_height) // 2
        
        self.draw_glassmorphism_panel(screen, pg.Rect(help_x, help_y, help_width, help_height))
        
        title_text = self.title_font.render(_("How to Play"), True, colors['TEXT'])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, help_y + 50))
        screen.blit(title_text, title_rect)
        
        help_lines = [
            _("Euclid's Game Rules:"),
            "",
            _("1. Players take turns selecting two numbers from the board"),
            _("2. Calculate the absolute difference between the two numbers"),
            _("3. If the difference is not already on the board, add it"),
            _("4. The player who cannot make a valid move loses"),
            "",
            _("Strategy Tips:"),
            _("• Try to force your opponent into positions with no valid moves"),
            _("• Look for patterns in the numbers"),
            _("• Consider the GCD (Greatest Common Divisor) of all numbers"),
        ]
        
        y_offset = help_y + 100
        for line in help_lines:
            if line.strip():
                if line.endswith(":"):
                    text = self.font_large.render(line, True, colors['PRIMARY'])
                else:
                    text = self.font.render(line, True, colors['TEXT'])
                screen.blit(text, (help_x + 40, y_offset))
            y_offset += 35
        
    def draw_glassmorphism_panel(self, screen, rect, alpha=180):
        """Draw a glassmorphism-style panel"""
        colors = self.theme
        
        panel_surface = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
        panel_surface.fill((*colors['GLASS'][:3], alpha))
        
        pg.draw.rect(panel_surface, colors['GLASS_BORDER'], 
                    (0, 0, rect.width, rect.height), 2, border_radius=20)
        
        screen.blit(panel_surface, rect.topleft)

    def draw_enhanced_menu(self, screen):
        """Fixed menu drawing with proper title"""
        colors = self.theme
        current_time = time.time()
        
        self.draw_gradient_background(screen, screen.get_rect(), colors['BG_GRADIENT'])
        
        title_y = 80
        shadow_text = self.title_font.render("EUCLID'S GAME", True, (0, 0, 0, 100))
        shadow_rect = shadow_text.get_rect(center=(self.screen_width // 2 + 3, title_y + 3))
        screen.blit(shadow_text, shadow_rect)
        
        title_text = self.title_font.render("EUCLID'S GAME", True, colors['PRIMARY'])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, title_y))
        screen.blit(title_text, title_rect)
        
        subtitle_text = self.font.render("A Mathematical Strategy Game", True, colors['TEXT_LIGHT'])
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, 130))
        screen.blit(subtitle_text, subtitle_rect)
        
        menu_width = 600
        menu_height = 500
        menu_x = (self.screen_width - menu_width) // 2
        menu_y = (self.screen_height - menu_height) // 2 + 30
        
        panel_rect = pg.Rect(menu_x, menu_y, menu_width, menu_height)
        shadow_rect = panel_rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        pg.draw.rect(screen, colors['CARD_SHADOW'], shadow_rect, border_radius=20)
        
        pg.draw.rect(screen, colors['CARD_BG'], panel_rect, border_radius=20)
        pg.draw.rect(screen, colors['PRIMARY'], panel_rect, 3, border_radius=20)
        
        mode_text = self.font_large.render("Select Game Mode", True, colors['TEXT'])
        mode_rect = mode_text.get_rect(center=(self.screen_width // 2, menu_y + 60))
        screen.blit(mode_text, mode_rect)
        
        button_width = 200
        button_height = 60
        button_y = menu_y + 120
        
        bot_rect = pg.Rect(menu_x + menu_width // 2 - button_width - 20, button_y, 
                        button_width, button_height)
        self.draw_menu_button(screen, bot_rect, "VS Bot", 
                            self.game_mode == GameMode.VS_BOT, colors['PRIMARY'])
        
        multi_rect = pg.Rect(menu_x + menu_width // 2 + 20, button_y, 
                            button_width, button_height)
        self.draw_menu_button(screen, multi_rect, "Local 2P", 
                            self.game_mode == GameMode.LOCAL_MULTIPLAYER, colors['SECONDARY'])
        
        if self.game_mode == GameMode.VS_BOT:
            diff_text = self.font_large.render("Select Difficulty", True, colors['TEXT'])
            diff_rect = diff_text.get_rect(center=(self.screen_width // 2, button_y + 100))
            screen.blit(diff_text, diff_rect)
            
            difficulties = [
                (Difficulty.EASY, "Easy", "Quick random moves", colors['SUCCESS']),
                (Difficulty.MEDIUM, "Medium", "Strategic thinking", colors['WARNING']),
                (Difficulty.EXPERT, "Expert", "Optimal play", colors['ERROR'])
            ]
            
            diff_button_width = 400
            diff_button_height = 45
            diff_y = button_y + 140
            
            for i, (diff, name, desc, color) in enumerate(difficulties):
                diff_rect = pg.Rect(menu_x + menu_width // 2 - diff_button_width // 2,
                                diff_y + i * (diff_button_height + 10),
                                diff_button_width, diff_button_height)
                self.draw_difficulty_button(screen, diff_rect, name, desc, 
                                        self.difficulty == diff, color)
        
        start_rect = pg.Rect(menu_x + menu_width // 2 -130, menu_y + menu_height - 70, 250, 50)
        self.draw_menu_button(screen, start_rect, "START GAME", True, colors['ACCENT'])
        
    def draw_menu_button(self, screen, rect, text, selected, color):
        """Simplified button drawing"""
        colors = self.theme
        mouse_pos = pg.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)
        
        if selected:
            pg.draw.rect(screen, color, rect, border_radius=15)
            text_color = (255, 255, 255)
        else:
            pg.draw.rect(screen, colors['GRAY'], rect, border_radius=15)
            if is_hover:
                pg.draw.rect(screen, color, rect, 3, border_radius=15)
            else:
                pg.draw.rect(screen, color, rect, 2, border_radius=15)
            text_color = colors['TEXT']
        
        font = self.font_large if text == "START GAME" else self.font
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    def draw_game_mode_button(self, screen, rect, text, selected, color):
        """Draw game mode selection button"""
        colors = self.theme
        
        if selected:
            pg.draw.rect(screen, color, rect, border_radius=15)
            text_color = (255, 255, 255)
            
            glow_rect = rect.inflate(10, 10)
            glow_surface = pg.Surface((glow_rect.width, glow_rect.height), pg.SRCALPHA)
            pg.draw.rect(glow_surface, (*color[:3], 50), 
                        (0, 0, glow_rect.width, glow_rect.height), 
                        border_radius=18)
            screen.blit(glow_surface, glow_rect)
        else:
            pg.draw.rect(screen, colors['GRAY'], rect, border_radius=15)
            pg.draw.rect(screen, color, rect, 2, border_radius=15)
            text_color = colors['TEXT']
        
        icon_surface = pg.Surface((30, 30), pg.SRCALPHA)
        if text == "VS Bot":
            pg.draw.circle(icon_surface, text_color, (15, 10), 8)
            pg.draw.rect(icon_surface, text_color, (7, 15, 16, 10))
            pg.draw.circle(icon_surface, colors['PRIMARY'] if selected else color, (10, 10), 2)
            pg.draw.circle(icon_surface, colors['PRIMARY'] if selected else color, (20, 10), 2)
        else:
            pg.draw.circle(icon_surface, text_color, (10, 10), 6)
            pg.draw.circle(icon_surface, text_color, (20, 10), 6)
            pg.draw.rect(icon_surface, text_color, (4, 15, 22, 10))
        
        screen.blit(icon_surface, (rect.x + 15, rect.centery - 15))
        
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    def draw_difficulty_button(self, screen, rect, name, desc, selected, color):
        """Draw difficulty selection button"""
        colors = self.theme
        
        if selected:
            pg.draw.rect(screen, color, rect, border_radius=10)
            text_color = (255, 255, 255)
        else:
            pg.draw.rect(screen, colors['GRAY'], rect, border_radius=10)
            pg.draw.rect(screen, color, rect, 2, border_radius=10)
            text_color = colors['TEXT']
        
        indicator_x = rect.x + 15
        indicator_y = rect.centery
        
        if name == "Easy":
            pg.draw.rect(screen, text_color, (indicator_x, indicator_y - 8, 4, 16))
        elif name == "Medium":
            for i in range(2):
                pg.draw.rect(screen, text_color, (indicator_x + i * 6, indicator_y - 8, 4, 16))
        else:
            for i in range(3):
                pg.draw.rect(screen, text_color, (indicator_x + i * 6, indicator_y - 8, 4, 16))
        
        name_surface = self.font.render(name, True, text_color)
        screen.blit(name_surface, (rect.x + 40, rect.centery - 18))
        
        desc_surface = self.font_small.render(desc, True, colors['TEXT_MUTED'] if not selected else (200, 200, 200))
        screen.blit(desc_surface, (rect.x + 40, rect.centery + 2))

    def draw_start_button(self, screen, rect, text, color):
        """Draw the start game button"""
        colors = self.theme
        mouse_pos = pg.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)
        
        shadow_rect = rect.copy()
        shadow_rect.y += 3
        pg.draw.rect(screen, colors['CARD_SHADOW'], shadow_rect, border_radius=25)
        
        button_color = color if not is_hover else [min(255, c + 20) for c in color[:3]]
        pg.draw.rect(screen, button_color, rect, border_radius=25)
        
        text_surface = self.font_large.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)
        
        if is_hover:
            shine_surface = pg.Surface((rect.width, rect.height // 2), pg.SRCALPHA)
            shine_surface.fill((255, 255, 255, 30))
            screen.blit(shine_surface, (rect.x, rect.y))

    def draw_animated_background(self, screen, current_time):
        """Draw animated geometric pattern background"""
        colors = self.theme
        
        for i in range(5):
            x = (current_time * 20 + i * 200) % (self.screen_width + 200) - 100
            y = 200 + 100 * math.sin(current_time + i)
            size = 50 + 20 * math.sin(current_time * 0.5 + i)
            
            shape_surface = pg.Surface((size * 2, size * 2), pg.SRCALPHA)
            pg.draw.polygon(shape_surface, (*colors['PRIMARY'][:3], 20),
                        [(size, 0), (size * 2, size), (size, size * 2), (0, size)])
            screen.blit(shape_surface, (x, y))

    def draw_gradient_text(self, screen, text, font, gradient_colors, pos):
        """Draw text with gradient effect"""
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=pos)
        
        gradient_surface = pg.Surface((text_rect.width, text_rect.height), pg.SRCALPHA)
        for i in range(text_rect.height):
            ratio = i / text_rect.height
            color = [
                int(gradient_colors[0][j] * (1 - ratio) + gradient_colors[1][j] * ratio)
                for j in range(3)
            ]
            pg.draw.line(gradient_surface, color, (0, i), (text_rect.width, i))
        
        final_surface = pg.Surface((text_rect.width, text_rect.height), pg.SRCALPHA)
        final_surface.blit(gradient_surface, (0, 0))
        final_surface.blit(text_surface, (0, 0), special_flags=pg.BLEND_RGBA_MIN)
        
        screen.blit(final_surface, text_rect)

    def draw_enhanced_panel(self, screen, rect):
        """Draw a panel with gradient border and glass effect"""
        colors = self.theme
        
        panel_surface = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
        
        for i in range(rect.height):
            alpha = 180 + int(20 * math.sin(i / rect.height * math.pi))
            color = (*colors['CARD_BG'][:3], alpha)
            pg.draw.line(panel_surface, color, (0, i), (rect.width, i))
        
        border_width = 3
        for i in range(border_width):
            alpha = 255 - i * 50
            color = (*colors['PRIMARY'][:3], alpha)
            pg.draw.rect(panel_surface, color, 
                        (i, i, rect.width - 2*i, rect.height - 2*i), 
                        1, border_radius=20)
        
        screen.blit(panel_surface, rect.topleft)

    def draw_mode_selection(self, screen, x, y, width, current_time):
        """Draw game mode selection with icons"""
        colors = self.theme
        
        title_text = self.font_large.render("Select Game Mode", True, colors['TEXT'])
        title_rect = title_text.get_rect(center=(x + width // 2, y))
        screen.blit(title_text, title_rect)
        
        button_width = 220
        button_height = 80
        button_y = y + 60
        spacing = 40
        
        modes = [
            (GameMode.VS_BOT, "VS Bot", "🤖", colors['PRIMARY']),
            (GameMode.LOCAL_MULTIPLAYER, "Local 2P", "👥", colors['SECONDARY'])
        ]
        
        start_x = x + width // 2 - (button_width + spacing // 2)
        
        for i, (mode, label, icon, color) in enumerate(modes):
            button_x = start_x + i * (button_width + spacing)
            button_rect = pg.Rect(button_x, button_y, button_width, button_height)
            
            is_selected = self.game_mode == mode
            
            if is_selected:
                elevation = 5
                shadow_rect = pg.Rect(button_x, button_y + elevation, button_width, button_height)
                pg.draw.rect(screen, colors['CARD_SHADOW'], shadow_rect, border_radius=15)
            
            button_surface = pg.Surface((button_width, button_height), pg.SRCALPHA)
            
            if is_selected:
                for j in range(button_height):
                    ratio = j / button_height
                    grad_color = [
                        int(color[0] * (1 - ratio * 0.3)),
                        int(color[1] * (1 - ratio * 0.3)),
                        int(color[2] * (1 - ratio * 0.3))
                    ]
                    pg.draw.line(button_surface, grad_color, (0, j), (button_width, j))
                text_color = (255, 255, 255)
            else:
                button_surface.fill(colors['GLASS'])
                pg.draw.rect(button_surface, color, (0, 0, button_width, button_height), 2, border_radius=15)
                text_color = colors['TEXT']
            
            icon_font = pg.font.Font(None, 40)
            icon_surface = icon_font.render(icon, True, text_color)
            icon_rect = icon_surface.get_rect(center=(button_width // 2, button_height // 2 - 15))
            button_surface.blit(icon_surface, icon_rect)
            
            label_surface = self.font.render(label, True, text_color)
            label_rect = label_surface.get_rect(center=(button_width // 2, button_height // 2 + 20))
            button_surface.blit(label_surface, label_rect)
            
            mask = pg.Surface((button_width, button_height), pg.SRCALPHA)
            pg.draw.rect(mask, (255, 255, 255, 255), (0, 0, button_width, button_height), border_radius=15)
            button_surface.blit(mask, (0, 0), special_flags=pg.BLEND_RGBA_MIN)
            
            screen.blit(button_surface, button_rect)

    def draw_difficulty_selection(self, screen, x, y, width, current_time):
        """Draw difficulty selection with visual indicators"""
        colors = self.theme
        
        title_text = self.font_large.render("Select Difficulty", True, colors['TEXT'])
        title_rect = title_text.get_rect(center=(x + width // 2, y))
        screen.blit(title_text, title_rect)
        
        difficulties = [
            (Difficulty.EASY, "Easy", colors['SUCCESS'], "⚡", "Quick random moves"),
            (Difficulty.MEDIUM, "Medium", colors['WARNING'], "🧠", "Strategic thinking"),
            (Difficulty.EXPERT, "Expert", colors['ERROR'], "🏆", "Optimal play")
        ]
        
        button_width = 400
        button_height = 50
        button_y = y + 50
        
        for i, (diff, name, color, icon, desc) in enumerate(difficulties):
            button_rect = pg.Rect(x + width // 2 - button_width // 2,
                                button_y + i * (button_height + 15),
                                button_width, button_height)
            
            is_selected = self.difficulty == diff
            
            if is_selected:
                glow_rect = button_rect.inflate(10, 10)
                glow_surface = pg.Surface((glow_rect.width, glow_rect.height), pg.SRCALPHA)
                pg.draw.rect(glow_surface, (*color[:3], 50), (0, 0, glow_rect.width, glow_rect.height), border_radius=12)
                screen.blit(glow_surface, glow_rect)
                
                pg.draw.rect(screen, color, button_rect, border_radius=10)
                text_color = (255, 255, 255)
            else:
                pg.draw.rect(screen, colors['GLASS'], button_rect, border_radius=10)
                pg.draw.rect(screen, color, button_rect, 2, border_radius=10)
                text_color = colors['TEXT']
            
            icon_surface = self.font_large.render(icon, True, text_color)
            screen.blit(icon_surface, (button_rect.x + 20, button_rect.centery - 15))
            
            name_surface = self.font.render(name, True, text_color)
            screen.blit(name_surface, (button_rect.x + 70, button_rect.centery - 20))
            
            desc_surface = self.font_small.render(desc, True, colors['TEXT_MUTED'])
            screen.blit(desc_surface, (button_rect.x + 70, button_rect.centery + 5))

    def draw_enhanced_game_ui(self, screen):
        """Enhanced game UI with better visual hierarchy"""
        colors = self.theme
        
        self.draw_game_background(screen)
        
        self.draw_game_header(screen)
        
        self.draw_enhanced_board(screen)
        
        self.draw_info_panel(screen)
        self.draw_move_history_panel(screen)
        
        if self.selected_numbers:
            self.draw_selection_display(screen)
    
    def draw_game_background(self, screen):
        """Draw animated game background"""
        colors = self.theme
        current_time = time.time()
        
        self.draw_gradient_background(screen, screen.get_rect(), colors['BG_GRADIENT'])
        
        for i in range(3):
            x = self.screen_width // 2 + 300 * math.cos(current_time * 0.3 + i * 2.1)
            y = self.screen_height // 2 + 200 * math.sin(current_time * 0.3 + i * 2.1)
            
            pattern_surface = pg.Surface((200, 200), pg.SRCALPHA)
            pg.draw.circle(pattern_surface, (*colors['PRIMARY'][:3], 10), (100, 100), 80, 3)
            pg.draw.circle(pattern_surface, (*colors['SECONDARY'][:3], 10), (100, 100), 60, 2)
            pg.draw.circle(pattern_surface, (*colors['ACCENT'][:3], 10), (100, 100), 40, 1)
            
            screen.blit(pattern_surface, (x - 100, y - 100))

    def draw_game_header(self, screen):
        """Draw game header with player info and status"""
        colors = self.theme
        current_time = time.time()
        
        header_rect = pg.Rect(0, 0, self.screen_width, 100)
        header_surface = pg.Surface((header_rect.width, header_rect.height), pg.SRCALPHA)
        
        for i in range(header_rect.height):
            alpha = 200 - int(i / header_rect.height * 100)
            color = (*colors['CARD_BG'][:3], alpha)
            pg.draw.line(header_surface, color, (0, i), (header_rect.width, i))
        
        screen.blit(header_surface, header_rect)
        
        title_glow = self.font_large.render("Euclid's Game", True, colors['PRIMARY'])
        for i in range(3):
            glow_surface = pg.Surface(title_glow.get_size(), pg.SRCALPHA)
            glow_surface.blit(title_glow, (0, 0))
            glow_surface.set_alpha(50 - i * 15)
            screen.blit(glow_surface, (20 - i, 25 - i))
        
        title_surface = self.font_large.render("Euclid's Game", True, colors['TEXT'])
        screen.blit(title_surface, (20, 25))
        
        self.draw_turn_indicator(screen, header_rect, current_time)

    def draw_turn_indicator(self, screen, header_rect, current_time):
        """Draw animated turn indicator"""
        colors = self.theme
        
        indicator_x = self.screen_width - 300
        indicator_y = 30
        
        if self.game_mode == GameMode.VS_BOT:
            if self.current_player == 1:
                player_text = "Your Turn"
                player_color = colors['SUCCESS']
                icon = ""
            else:
                player_text = "Bot Thinking..."
                player_color = colors['WARNING']
                icon = "🤖"
        else:
            player_text = f"Player {self.current_player}'s Turn"
            player_color = colors['PRIMARY'] if self.current_player == 1 else colors['SECONDARY']
            icon = "P1" if self.current_player == 1 else "P2"
        
        bg_width = 250
        bg_height = 50
        bg_rect = pg.Rect(indicator_x - 20, indicator_y - 10, bg_width, bg_height)
        
        pulse = 1.0 + 0.1 * math.sin(current_time * 3)
        
        bg_surface = pg.Surface((bg_width, bg_height), pg.SRCALPHA)
        for i in range(bg_height):
            ratio = i / bg_height
            alpha = int(100 * (1 - ratio))
            color = (*player_color[:3], alpha)
            pg.draw.line(bg_surface, color, (0, i), (bg_width, i))
        
        pg.draw.rect(bg_surface, player_color, (0, 0, bg_width, bg_height), 2, border_radius=25)
        screen.blit(bg_surface, bg_rect)
        
        if self.current_player == 2 and self.game_mode == GameMode.VS_BOT:
            if self.bot_thinking:
                scale = 0.8 + 0.2 * math.sin(self.bot_thinking_animation)
                rotation = self.bot_thinking_animation * 30
                
                scaled_avatar = pg.transform.scale(self.bot_avatar, 
                                                (int(50 * scale), int(50 * scale)))
                rotated_avatar = pg.transform.rotate(scaled_avatar, rotation)
                
                avatar_rect = rotated_avatar.get_rect(center=(indicator_x + 10, indicator_y + 15))
                screen.blit(rotated_avatar, avatar_rect)
        else:
            icon_surface = self.font_large.render(icon, True, (255, 255, 255))
            icon_rect = icon_surface.get_rect(center=(indicator_x + 10, indicator_y + 15))
            screen.blit(icon_surface, icon_rect)
        
        text_surface = self.font.render(player_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(midleft=(indicator_x + 40, indicator_y + 15))
        screen.blit(text_surface, text_rect)

    def draw_info_panel(self, screen):
        """Draw information panel with game stats"""
        colors = self.theme
        
        panel_width = 250
        panel_height = 200
        panel_x = 20
        panel_y = 120
        
        panel_rect = pg.Rect(panel_x, panel_y, panel_width, panel_height)
        self.draw_glass_panel(screen, panel_rect, "Game Info", colors['PRIMARY'])
        
        # Stats
        y_offset = panel_y + 50
        stats = [
            ("Numbers in play:", len(self.active_numbers)),
            ("Moves made:", len(self.move_history)),
            ("Valid moves left:", self.count_valid_moves()),
        ]
        
        for label, value in stats:
            label_surface = self.font_small.render(label, True, colors['TEXT_MUTED'])
            screen.blit(label_surface, (panel_x + 20, y_offset))
            
            value_surface = self.font.render(str(value), True, colors['TEXT'])
            value_rect = value_surface.get_rect(right=panel_x + panel_width - 20, y=y_offset - 5)
            screen.blit(value_surface, value_rect)
            
            y_offset += 40

    def draw_selection_display(self, screen):
        """Draw selected numbers with calculation preview"""
        colors = self.theme
        
        if not self.selected_numbers:
            return
        
        display_y = self.screen_height - 120
        display_x = self.screen_width // 2
        
        panel_width = 400
        panel_height = 60
        panel_rect = pg.Rect(display_x - panel_width // 2, display_y, panel_width, panel_height)
        
        panel_surface = pg.Surface((panel_width, panel_height), pg.SRCALPHA)
        pg.draw.rect(panel_surface, (*colors['CARD_BG'][:3], 200), 
                    (0, 0, panel_width, panel_height), border_radius=30)
        pg.draw.rect(panel_surface, colors['PRIMARY'], 
                    (0, 0, panel_width, panel_height), 2, border_radius=30)
        screen.blit(panel_surface, panel_rect)
        
        if len(self.selected_numbers) == 1:
            text = f"Selected: {self.selected_numbers[0]}"
            text_color = colors['TEXT']
        else:
            num1, num2 = self.selected_numbers
            diff = abs(num1 - num2)
            is_valid = diff not in self.active_numbers
            
            text = f"{num1} - {num2} = {diff}"
            text_color = colors['SUCCESS'] if is_valid else colors['ERROR']
            
            status = "✓ Valid" if is_valid else "✗ Already exists"
            status_surface = self.font_small.render(status, True, text_color)
            status_rect = status_surface.get_rect(center=(display_x, display_y + 40))
            screen.blit(status_surface, status_rect)
        
        text_surface = self.font_large.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(display_x, display_y + 15))
        screen.blit(text_surface, text_rect)

    def draw_enhanced_board(self, screen):
        colors = self.theme
        current_time = time.time()
        
        self.draw_grid_pattern(screen)
        
        if len(self.selected_numbers) == 2:
            self.draw_selection_preview(screen)
        
        for num in range(1, 101):
            rect = self.squares[num]
            
            is_active = num in self.active_numbers
            is_selected = num in self.selected_numbers
            is_hovered = num in self.hover_effects
            
            if not is_active:
                continue
                
            scale = 1.0
            alpha = 255
            rotation = 0
            elevation = 0
            
            for anim in self.animations:
                if anim.number == num:
                    scale = anim.scale
                    alpha = anim.alpha
                    rotation = anim.rotation
                    break
            
            if is_hovered and is_active:
                hover_duration = current_time - self.hover_effects[num]
                scale = 1.05 + 0.05 * math.sin(hover_duration * 3)
                elevation = 5
            
            if elevation > 0:
                shadow_surface = pg.Surface((rect.width + elevation * 2, rect.height + elevation * 2), pg.SRCALPHA)
                pg.draw.rect(shadow_surface, (*colors['CARD_SHADOW'][:3], 80), 
                            (0, 0, rect.width + elevation * 2, rect.height + elevation * 2), 
                            border_radius=12)
                screen.blit(shadow_surface, (rect.x - elevation, rect.y - elevation + 2))
            
            square_size = int(rect.width * scale)
            square_surface = pg.Surface((square_size, square_size), pg.SRCALPHA)
            
            if is_selected:
                self.draw_rounded_rect_gradient(square_surface, 
                                            pg.Rect(0, 0, square_size, square_size),
                                            colors['SECONDARY_GRADIENT'], 12)
                text_color = (255, 255, 255)
                
                glow_alpha = int(100 + 50 * math.sin(current_time * 3))
                glow_surface = pg.Surface((square_size + 20, square_size + 20), pg.SRCALPHA)
                pg.draw.rect(glow_surface, (*colors['SECONDARY'][:3], glow_alpha), 
                            (0, 0, square_size + 20, square_size + 20), border_radius=16)
                screen.blit(glow_surface, (rect.centerx - (square_size + 20) // 2, 
                                        rect.centery - (square_size + 20) // 2))
            else:
                pg.draw.rect(square_surface, colors['CARD_BG'], 
                            (0, 0, square_size, square_size), border_radius=10)
                
                border_color = colors['PRIMARY'] if is_hovered else colors['GRAY_DARK']
                pg.draw.rect(square_surface, border_color, 
                            (0, 0, square_size, square_size), 2, border_radius=10)
                text_color = colors['TEXT']
            
            if rotation != 0:
                square_surface = pg.transform.rotate(square_surface, rotation)
            
            if alpha < 255:
                square_surface.set_alpha(alpha)
            
            square_rect = square_surface.get_rect(center=rect.center)
            screen.blit(square_surface, square_rect)
            
            font = self.font_small if rect.width < 50 else self.font
            text_surface = font.render(str(num), True, text_color)
            text_rect = text_surface.get_rect(center=rect.center)
            screen.blit(text_surface, text_rect)
            
            if self.move_history and self.move_history[-1]['diff'] == num:
                indicator_surface = pg.Surface((8, 8), pg.SRCALPHA)
                pg.draw.circle(indicator_surface, colors['GOLD'], (4, 4), 4)
                screen.blit(indicator_surface, (rect.right - 12, rect.top + 4))

    def draw_grid_pattern(self, screen):
        """Draw subtle grid pattern in background"""
        colors = self.theme
        pattern_surface = pg.Surface((20, 20), pg.SRCALPHA)
        pg.draw.circle(pattern_surface, (*colors['GRAY'][:3], 30), (10, 10), 1)
        
        for x in range(0, self.screen_width, 20):
            for y in range(100, self.screen_height - 100, 20):
                screen.blit(pattern_surface, (x, y))

    def draw_selection_preview(self, screen):
        """Draw preview line between selected numbers"""
        if len(self.selected_numbers) != 2:
            return
            
        colors = self.theme
        num1, num2 = self.selected_numbers
        pos1 = self.squares[num1].center
        pos2 = self.squares[num2].center
        
        diff = abs(num1 - num2)
        is_valid = diff not in self.active_numbers
        
        line_color = colors['SUCCESS'] if is_valid else colors['ERROR']
        
        distance = math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
        steps = int(distance / 10)
        
        for i in range(0, steps, 2):
            t = i / steps
            x = pos1[0] + (pos2[0] - pos1[0]) * t
            y = pos1[1] + (pos2[1] - pos1[1]) * t
            pg.draw.circle(screen, line_color, (int(x), int(y)), 2)
        
        mid_x = (pos1[0] + pos2[0]) // 2
        mid_y = (pos1[1] + pos2[1]) // 2
        
        label_bg = pg.Surface((60, 30), pg.SRCALPHA)
        pg.draw.rect(label_bg, (*colors['CARD_BG'], 200), (0, 0, 60, 30), border_radius=15)
        pg.draw.rect(label_bg, line_color, (0, 0, 60, 30), 2, border_radius=15)
        screen.blit(label_bg, (mid_x - 30, mid_y - 15))
        
        diff_text = self.font_small.render(str(diff), True, line_color)
        diff_rect = diff_text.get_rect(center=(mid_x, mid_y))
        screen.blit(diff_text, diff_rect)

    def draw_move_history(self, screen):
        colors = self.theme
        
        if not self.move_history:
            return
        
        panel_width = 300
        panel_height = min(400, len(self.move_history) * 30 + 60)
        panel_x = self.screen_width - panel_width - 20
        panel_y = 120
        
        panel_rect = pg.Rect(panel_x, panel_y, panel_width, panel_height)
        self.draw_glassmorphism_panel(screen, panel_rect, alpha=100)
        
        title_text = self.font.render(_("Move History"), True, colors['TEXT'])
        screen.blit(title_text, (panel_x + 20, panel_y + 20))
        
        y_offset = panel_y + 60
        for i, move in enumerate(self.move_history[-10:]):  # Show last 10 moves
            player_text = f"P{move['player']}: {move['num1']} - {move['num2']} = {move['diff']}"
            text_color = colors['PRIMARY'] if move['player'] == 1 else colors['SECONDARY']
            
            text_surface = self.font_small.render(player_text, True, text_color)
            screen.blit(text_surface, (panel_x + 20, y_offset))
            y_offset += 25

    def draw_enhanced_game_over(self, screen):
        """Enhanced game over screen with animations and stats"""
        colors = self.theme
        current_time = time.time()
        
        overlay = pg.Surface((self.screen_width, self.screen_height), pg.SRCALPHA)
        overlay_alpha = int(150 + 20 * math.sin(current_time))
        overlay.fill((0, 0, 0, overlay_alpha))
        screen.blit(overlay, (0, 0))
        
        if hasattr(self, 'game_over_particles_created'):
            pass
        else:
            self.game_over_particles_created = True
            particle_color = colors['SUCCESS'] if self.winner == 1 else colors['ERROR']
            for _ in range(100):
                x = random.randint(100, self.screen_width - 100)
                y = random.randint(100, self.screen_height - 100)
                velocity = (random.uniform(-100, 100), random.uniform(-200, -50))
                self.particles.append(
                    Particle(x, y, particle_color, velocity, 
                            random.uniform(3, 8), random.uniform(2, 4))
                )
        
        panel_width = 600
        panel_height = 400
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2
        
        entrance_progress = min(1.0, (current_time - self.game_over_time) * 2) if hasattr(self, 'game_over_time') else 1.0
        if not hasattr(self, 'game_over_time'):
            self.game_over_time = current_time
        
        panel_y_animated = panel_y + (1 - entrance_progress) * 100
        panel_rect = pg.Rect(panel_x, panel_y_animated, panel_width, panel_height)
        
        self.draw_victory_panel(screen, panel_rect, entrance_progress)
        
        self.draw_winner_text(screen, panel_rect, current_time)
        
        self.draw_game_over_buttons(screen, panel_rect, current_time)

    def draw_glass_panel(self, screen, rect, title, accent_color):
        """Draw a reusable glass-style panel"""
        colors = self.theme
        
        layers = [
            (rect.inflate(6, 6), (*colors['CARD_SHADOW'][:3], 20)),
            (rect.inflate(4, 4), (*colors['CARD_SHADOW'][:3], 30)),
            (rect.inflate(2, 2), (*colors['CARD_SHADOW'][:3], 40)),
        ]
        
        for layer_rect, color in layers:
            shadow_surface = pg.Surface((layer_rect.width, layer_rect.height), pg.SRCALPHA)
            pg.draw.rect(shadow_surface, color, (0, 0, layer_rect.width, layer_rect.height), 
                        border_radius=15)
            screen.blit(shadow_surface, layer_rect)
        
        panel_surface = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
        pg.draw.rect(panel_surface, (*colors['CARD_BG'][:3], 200), 
                    (0, 0, rect.width, rect.height), border_radius=15)
        
        pg.draw.rect(panel_surface, accent_color, 
                    (0, 0, rect.width, rect.height), 2, border_radius=15)
        
        screen.blit(panel_surface, rect)
        
        if title:
            title_rect = pg.Rect(rect.x, rect.y, rect.width, 35)
            title_surface = pg.Surface((title_rect.width, title_rect.height), pg.SRCALPHA)
            
            for i in range(title_rect.height):
                alpha = int(100 * (1 - i / title_rect.height))
                color = (*accent_color[:3], alpha)
                pg.draw.line(title_surface, color, (0, i), (title_rect.width, i))
            
            pg.draw.rect(title_surface, accent_color, 
                        (0, 0, title_rect.width, title_rect.height), 
                        border_top_left_radius=15, border_top_right_radius=15)
            
            screen.blit(title_surface, title_rect)
            
            title_text = self.font.render(title, True, (255, 255, 255))
            title_text_rect = title_text.get_rect(center=(title_rect.centerx, title_rect.centery))
            screen.blit(title_text, title_text_rect)

    def draw_move_history_panel(self, screen):
        """Enhanced move history with visual timeline"""
        colors = self.theme
        
        if not self.move_history:
            return
        
        panel_width = 280
        panel_height = min(400, len(self.move_history) * 35 + 80)
        panel_x = self.screen_width - panel_width - 20
        panel_y = 120
        
        panel_rect = pg.Rect(panel_x, panel_y, panel_width, panel_height)
        self.draw_glass_panel(screen, panel_rect, "Move History", colors['SECONDARY'])
        
        timeline_x = panel_x + 30
        timeline_start_y = panel_y + 50
        timeline_end_y = min(timeline_start_y + len(self.move_history) * 35, panel_y + panel_height - 20)
        
        pg.draw.line(screen, colors['GRAY'], 
                    (timeline_x, timeline_start_y), 
                    (timeline_x, timeline_end_y), 2)
        
        y_offset = timeline_start_y
        for i, move in enumerate(self.move_history[-10:]): 
            node_color = colors['PRIMARY'] if move['player'] == 1 else colors['SECONDARY']
            pg.draw.circle(screen, node_color, (timeline_x, y_offset), 6)
            pg.draw.circle(screen, (255, 255, 255), (timeline_x, y_offset), 3)
            
            move_text = f"{move['num1']} - {move['num2']} = {move['diff']}"
            player_text = f"P{move['player']}"
            
            badge_rect = pg.Rect(timeline_x + 20, y_offset - 12, 30, 24)
            pg.draw.rect(screen, node_color, badge_rect, border_radius=12)
            
            player_surface = self.font_small.render(player_text, True, (255, 255, 255))
            player_rect = player_surface.get_rect(center=badge_rect.center)
            screen.blit(player_surface, player_rect)
            
            text_surface = self.font_small.render(move_text, True, colors['TEXT'])
            screen.blit(text_surface, (timeline_x + 60, y_offset - 8))
            
            y_offset += 35

    def draw_victory_panel(self, screen, rect, progress):
        """Draw victory/defeat panel with effects"""
        colors = self.theme
        
        for i in range(5):
            shadow_alpha = int(60 * (1 - i / 5) * progress)
            shadow_rect = rect.inflate(i * 4, i * 4)
            shadow_surface = pg.Surface((shadow_rect.width, shadow_rect.height), pg.SRCALPHA)
            pg.draw.rect(shadow_surface, (*colors['CARD_SHADOW'][:3], shadow_alpha),
                        (0, 0, shadow_rect.width, shadow_rect.height),
                        border_radius=20)
            screen.blit(shadow_surface, shadow_rect)
        
        panel_surface = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
        
        winner_colors = colors['SUCCESS'] if self.winner == 1 else colors['ERROR']
        for i in range(rect.height):
            ratio = i / rect.height
            bg_color = [
                int(colors['CARD_BG'][0] * (1 - ratio * 0.2)),
                int(colors['CARD_BG'][1] * (1 - ratio * 0.2)),
                int(colors['CARD_BG'][2] * (1 - ratio * 0.2))
            ]
            pg.draw.line(panel_surface, bg_color, (0, i), (rect.width, i))
        
        pg.draw.rect(panel_surface, winner_colors, 
                    (0, 0, rect.width, rect.height), 3, border_radius=20)
        
        screen.blit(panel_surface, rect)

    def draw_winner_text(self, screen, panel_rect, current_time):
        """Draw animated winner announcement"""
        colors = self.theme
        
        if self.game_mode == GameMode.VS_BOT:
            if self.winner == 1:
                main_text = "Victory!"
                sub_text = "You've outsmarted the bot!"
                text_color = colors['SUCCESS']
            else:
                main_text = "Defeat!"
                sub_text = f"The {self.bot.difficulty.name} bot wins!"
                text_color = colors['ERROR']
        else:
            main_text = f"Player {self.winner} Wins!"
            sub_text = "Congratulations!"
            text_color = colors['PRIMARY'] if self.winner == 1 else colors['SECONDARY']
        
        scale = 1.0 + 0.1 * math.sin(current_time * 3)
        
        main_font_size = int(72 * scale)
        main_font = pg.font.Font(None, main_font_size)
        
        for i in range(3):
            glow_surface = main_font.render(main_text, True, (*text_color[:3], 100 - i * 30))
            glow_rect = glow_surface.get_rect(center=(panel_rect.centerx, panel_rect.y + 80))
            screen.blit(glow_surface, glow_rect.move(i, i))
        
        main_surface = main_font.render(main_text, True, text_color)
        main_rect = main_surface.get_rect(center=(panel_rect.centerx, panel_rect.y + 80))
        screen.blit(main_surface, main_rect)
        
        sub_surface = self.font.render(sub_text, True, colors['TEXT'])
        sub_rect = sub_surface.get_rect(center=(panel_rect.centerx, panel_rect.y + 130))
        screen.blit(sub_surface, sub_rect)

    def reset_game(self):
        """Reset game with transition effects"""
        for _ in range(50):
            x = random.randint(100, self.screen_width - 100)
            y = random.randint(100, self.screen_height - 100)
            velocity = (random.uniform(-100, 100), random.uniform(-100, 100))
            self.particles.append(
                Particle(x, y, self.theme['PRIMARY'], velocity, 3, 1.5)
            )
        
        self.active_numbers = []
        self.selected_numbers = []
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.animations = []
        self.hover_effects = {}
        self.bot_thinking = False
        self.game_start_time = time.time()
        
        self.add_initial_numbers_animated()
        
        if self.game_mode == GameMode.VS_BOT:
            self.bot = Bot(self.difficulty)
        
        if self.game_mode == GameMode.VS_BOT:
            self.bot = Bot(self.difficulty)

    def add_initial_numbers_animated(self):
        """Add initial numbers with animation"""
        num1 = random.randint(20, 40)
        num2 = random.randint(60, 80)

        self.active_numbers = [num1, num2]
        
        if num1 in self.squares and num2 in self.squares:
            start1 = (-100, self.screen_height // 2)
            start2 = (self.screen_width + 100, self.screen_height // 2)
            
            anim1 = Animation(start1, self.squares[num1].center, 
                            duration=1.0, easing='ease_out_cubic')
            anim1.number = num1
            
            anim2 = Animation(start2, self.squares[num2].center, 
                            duration=1.0, easing='ease_out_cubic')
            anim2.number = num2
            
            self.animations.extend([anim1, anim2])

    def select_number(self, number):
        if number not in self.active_numbers:
            return False
        
        if number in self.squares:
            rect = self.squares[number]
            x, y = rect.center
        
        if number in self.selected_numbers:
            self.selected_numbers.remove(number)
            self.create_selection_particles(x, y, self.theme['GRAY'])
        else:
            if len(self.selected_numbers) < 2:
                self.selected_numbers.append(number)
                self.create_selection_particles(x, y, self.theme['SECONDARY'])
        
        return True

    def draw_game_over_buttons(self, screen, panel_rect, current_time):
        """Draw action buttons for game over screen"""
        colors = self.theme
        
        button_y = panel_rect.y + 320
        button_width = 180
        button_height = 50
        
        button_x = panel_rect.centerx - button_width // 2
        button_rect = pg.Rect(button_x, button_y, button_width, button_height)
        
        self.play_again_button_rect = button_rect.copy()
        
        mouse_pos = pg.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        if is_hover:
            shadow_rect = button_rect.copy()
            shadow_rect.y += 5
            pg.draw.rect(screen, colors['CARD_SHADOW'], shadow_rect, border_radius=25)
            
            scale = 1.05 + 0.05 * math.sin(current_time * 4)
            button_rect = button_rect.inflate(int(button_width * (scale - 1)), 
                                            int(button_height * (scale - 1)))
        
        pg.draw.rect(screen, colors['SUCCESS'], button_rect, border_radius=25)
        
        text_surface = self.font.render("Play Again", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=button_rect.center)
        screen.blit(text_surface, text_rect)

    def count_valid_moves(self):
        """Count remaining valid moves"""
        count = 0
        for i in range(len(self.active_numbers)):
            for j in range(i + 1, len(self.active_numbers)):
                diff = abs(self.active_numbers[i] - self.active_numbers[j])
                if diff not in self.active_numbers:
                    count += 1
        return count

    def create_selection_particles(self, x, y, color):
        """Create particles when selecting/deselecting numbers"""
        for i in range(12):
            angle = (i / 12) * 2 * math.pi
            velocity = (
                math.cos(angle) * 100,
                math.sin(angle) * 100
            )
            self.particles.append(
                Particle(x, y, color, velocity, 3, 0.8)
            )

    def make_move(self):
        if len(self.selected_numbers) != 2:
            return False
        
        num1, num2 = self.selected_numbers
        diff = abs(num1 - num2)
        
        if diff in self.active_numbers:
            self.selected_numbers = []
            return False
        
        self.active_numbers.append(diff)
        self.move_history.append({
            'player': self.current_player,
            'num1': num1,
            'num2': num2,
            'diff': diff
        })
        
        if diff in self.squares:
            start_pos = ((self.squares[num1].centerx + self.squares[num2].centerx) // 2,
                        (self.squares[num1].centery + self.squares[num2].centery) // 2)
            end_pos = self.squares[diff].center
            
            anim = Animation(start_pos, end_pos, duration=0.8, easing='ease_bounce')
            anim.number = diff
            self.animations.append(anim)
        
        self.selected_numbers = []
        self.current_player = 2 if self.current_player == 1 else 1
        
        return True

    def bot_move(self):
        if self.game_over:
            return False
        
        move = self.bot.get_move({'active_numbers': self.active_numbers})
        if move:
            self.selected_numbers = [move[0], move[1]]
            return True
        return False

    def check_game_over(self):
        valid_moves = []
        for i in range(len(self.active_numbers)):
            for j in range(i + 1, len(self.active_numbers)):
                diff = abs(self.active_numbers[i] - self.active_numbers[j])
                if diff not in self.active_numbers:
                    valid_moves.append((self.active_numbers[i], self.active_numbers[j]))
        
        if not valid_moves:
            self.game_over = True
            self.winner = 2 if self.current_player == 1 else 1
            
            for _ in range(50):
                x = random.randint(100, self.screen_width - 100)
                y = random.randint(100, self.screen_height - 100)
                color = self.theme['SUCCESS'] if self.winner == 1 else self.theme['ERROR']
                self.create_particles(x, y, 1, color)

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        if hasattr(self, 'bot'):
            self.bot = Bot(difficulty)

    def quit(self):
        self.running = False

# Main execution
if __name__ == "__main__":
    game = Game()
    game.run()