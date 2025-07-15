import pygame as pg
import sys
import gi
import random
from enum import Enum
import time
import math
from gettext import gettext as _
from config import Theme
from player import Player, Bot, Difficulty

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

WIDTH, HEIGHT = 1200, 800
FPS = 60

# Game modes
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
        self.transition_alpha = 0
        self.transition_target = 0
        self.last_frame_time = time.time()
        self.screen = None
        self.reset_game()
        
        # Initialize fonts as None
        self.font_small = None
        self.font = None
        self.font_large = None
        self.title_font = None
        
        # Bot avatar
        self.bot_avatar = None

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.theme == Theme.LIGHT:
            self.theme = Theme.DARK
        else:
            self.theme = Theme.LIGHT
        
    def set_canvas(self, canvas):
        self.canvas = canvas
        if self.screen:
            pg.display.set_caption(_("Euclid's Game"))

    def toggle_help(self):
        self.show_help = not self.show_help

    def run(self):
        # Initialize pygame
        pg.init()
        pg.font.init()
        
        self.clock = pg.time.Clock()
        
        # IMPORTANT: Get the display surface that sugargame created
        self.screen = pg.display.get_surface()
        
        # Get screen dimensions
        if self.screen:
            self.screen_width = self.screen.get_width()
            self.screen_height = self.screen.get_height()
        else:
            # Fallback for standalone testing
            self.screen_width = WIDTH
            self.screen_height = HEIGHT
            self.screen = pg.display.set_mode((WIDTH, HEIGHT))
            pg.display.set_caption("Euclid's Game")
        
        # Initialize fonts after pygame is fully initialized
        self.font_small = pg.font.Font(None, 24)
        self.font = pg.font.Font(None, 36)
        self.font_large = pg.font.Font(None, 48)
        self.title_font = pg.font.Font(None, 72)
        
        
        # Calculate square positions
        self.setup_squares()

        while self.running:
            # Handle GTK events
            while Gtk.events_pending():
                Gtk.main_iteration()

            self.handle_events()
            
            # self.update(dt)
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pg.quit()
        sys.exit(0)

    def setup_squares(self): ##
        # Simple grid layout
        square_size = 50
        margin = 10
        grid_start_x = 100
        grid_start_y = 150
        
        for i in range(100):
            row = i // 10
            col = i % 10
            x = grid_start_x + col * (square_size + margin)
            y = grid_start_y + row * (square_size + margin)
            self.squares[i + 1] = pg.Rect(x, y, square_size, square_size)

    def handle_events(self): ##
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.handle_click(event.pos)
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if not self.show_menu:
                        self.show_menu = True
                        self.reset_game()
                
    def handle_click(self, mouse_pos): ##
        if self.show_menu:
            self.handle_menu_click(mouse_pos)
        elif not self.game_over:
            self.handle_game_click(mouse_pos)
        else:
            # Check restart button
            restart_rect = pg.Rect(self.screen_width // 2 - 100, 400, 200, 50)
            menu_rect = pg.Rect(self.screen_width // 2 - 100, 470, 200, 50)
            if restart_rect.collidepoint(mouse_pos):
                self.reset_game()
            elif menu_rect.collidepoint(mouse_pos):
                self.show_menu = True
                self.reset_game()

    def handle_menu_click(self, mouse_pos): ##
        # Simple menu buttons
        vs_bot_rect = pg.Rect(400, 300, 200, 50)
        multiplayer_rect = pg.Rect(400, 370, 200, 50)
        
        # Difficulty buttons
        easy_rect = pg.Rect(650, 300, 150, 40)
        medium_rect = pg.Rect(650, 350, 150, 40)
        expert_rect = pg.Rect(650, 400, 150, 40)
        
        # Start button
        start_rect = pg.Rect(self.screen_width // 2 - 100, 500, 200, 50)
        
        if vs_bot_rect.collidepoint(mouse_pos):
            self.game_mode = GameMode.VS_BOT
        elif multiplayer_rect.collidepoint(mouse_pos):
            self.game_mode = GameMode.LOCAL_MULTIPLAYER
        elif easy_rect.collidepoint(mouse_pos) and self.game_mode == GameMode.VS_BOT:
            self.difficulty = Difficulty.EASY
        elif medium_rect.collidepoint(mouse_pos) and self.game_mode == GameMode.VS_BOT:
            self.difficulty = Difficulty.MEDIUM
        elif expert_rect.collidepoint(mouse_pos) and self.game_mode == GameMode.VS_BOT:
            self.difficulty = Difficulty.EXPERT
        elif start_rect.collidepoint(mouse_pos):
            self.show_menu = False
            self.reset_game()
    
    def handle_game_click(self, mouse_pos): ##
        if self.current_player == 1 or self.game_mode == GameMode.LOCAL_MULTIPLAYER:
            # Check number squares
            for num, rect in self.squares.items():
                if rect.collidepoint(mouse_pos) and num in self.active_numbers:
                    self.select_number(num)
                    if len(self.selected_numbers) == 2:
                        if self.make_move():
                            self.check_game_over()
    
    def select_number(self, number):
        if number not in self.active_numbers:
            return False
        
        # Get square position for particle effects
        if number in self.squares:
            rect = self.squares[number]
            x, y = rect.center
        
        if number in self.selected_numbers:
            self.selected_numbers.remove(number)
        else:
            if len(self.selected_numbers) < 2:
                self.selected_numbers.append(number)
        
        return True

    def update(self):
        # Simple bot logic
        if (self.current_player == 2 and not self.game_over and 
            self.game_mode == GameMode.VS_BOT and not self.show_menu):
            if not self.bot_thinking:
                self.bot_thinking = True
                self.bot_timer = pg.time.get_ticks()
            elif pg.time.get_ticks() - self.bot_timer >= 1000:  # 1 second delay
                if self.bot_move():
                    if self.make_move():
                        self.check_game_over()
                self.bot_thinking = False

    def draw(self): ##
        # Clear screen
        self.screen.fill((240, 240, 240))

        if self.show_menu:
            self.draw_menu()
        else:
            self.draw_game()
            if self.game_over:
                self.draw_game_over()
        
        pg.display.flip()
    
    def draw_game(self):  ##
        # Title
        title = self.font_large.render("Euclid's Game", True, (0, 0, 0))
        self.screen.blit(title, (20, 20))
        
        # Current player
        if self.game_mode == GameMode.VS_BOT:
            player_text = "Your Turn" if self.current_player == 1 else "Bot's Turn"
        else:
            player_text = f"Player {self.current_player}'s Turn"
        
        turn_text = self.font.render(player_text, True, (0, 0, 0))
        self.screen.blit(turn_text, (20, 80))
        
        # Draw number grid
        for num, rect in self.squares.items():
            if num in self.active_numbers:
                # Draw active numbers
                if num in self.selected_numbers:
                    color = (255, 200, 0)  # Yellow for selected
                else:
                    color = (200, 200, 200)  # Light gray for active
                
                pg.draw.rect(self.screen, color, rect)
                pg.draw.rect(self.screen, (0, 0, 0), rect, 2)
                
                # Draw number
                text = self.font_small.render(str(num), True, (0, 0, 0))
                text_rect = text.get_rect(center=rect.center)
                self.screen.blit(text, text_rect)
        
        # Show selected numbers and calculation
        if self.selected_numbers:
            y_pos = 720
            if len(self.selected_numbers) == 1:
                text = f"Selected: {self.selected_numbers[0]}"
            else:
                num1, num2 = self.selected_numbers
                diff = abs(num1 - num2)
                text = f"{num1} - {num2} = {diff}"
                if diff in self.active_numbers:
                    text += " (Already exists!)"
            
            calc_text = self.font.render(text, True, (0, 0, 0))
            calc_rect = calc_text.get_rect(center=(self.screen_width // 2, y_pos))
            self.screen.blit(calc_text, calc_rect)
        
        # Move history (simple list)
        history_text = self.font.render("Move History:", True, (0, 0, 0))
        self.screen.blit(history_text, (850, 150))
        
        y_offset = 180
        for i, move in enumerate(self.move_history[-10:]):  # Show last 10 moves
            text = f"P{move['player']}: {move['num1']} - {move['num2']} = {move['diff']}"
            move_text = self.font_small.render(text, True, (0, 0, 0))
            self.screen.blit(move_text, (850, y_offset))
            y_offset += 25

    def draw_menu(self): ##
        # Title
        title = self.font_large.render("EUCLID'S GAME", True, (0, 0, 0))
        title_rect = title.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Instructions
        inst = self.font_small.render("Select two numbers to find their difference", True, (100, 100, 100))
        inst_rect = inst.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(inst, inst_rect)
        
        # Game mode buttons
        vs_bot_rect = pg.Rect(400, 300, 200, 50)
        color = (0, 150, 0) if self.game_mode == GameMode.VS_BOT else (150, 150, 150)
        pg.draw.rect(self.screen, color, vs_bot_rect)
        text = self.font.render("VS Bot", True, (255, 255, 255))
        text_rect = text.get_rect(center=vs_bot_rect.center)
        self.screen.blit(text, text_rect)
        
        multiplayer_rect = pg.Rect(400, 370, 200, 50)
        color = (0, 150, 0) if self.game_mode == GameMode.LOCAL_MULTIPLAYER else (150, 150, 150)
        pg.draw.rect(self.screen, color, multiplayer_rect)
        text = self.font.render("2 Players", True, (255, 255, 255))
        text_rect = text.get_rect(center=multiplayer_rect.center)
        self.screen.blit(text, text_rect)
        
        # Difficulty (only for VS Bot)
        if self.game_mode == GameMode.VS_BOT:
            diff_text = self.font.render("Difficulty:", True, (0, 0, 0))
            self.screen.blit(diff_text, (650, 250))
            
            difficulties = [
                (Difficulty.EASY, "Easy", pg.Rect(650, 300, 150, 40)),
                (Difficulty.MEDIUM, "Medium", pg.Rect(650, 350, 150, 40)),
                (Difficulty.EXPERT, "Expert", pg.Rect(650, 400, 150, 40))
            ]
            
            for diff, name, rect in difficulties:
                color = (0, 150, 0) if self.difficulty == diff else (150, 150, 150)
                pg.draw.rect(self.screen, color, rect)
                text = self.font_small.render(name, True, (255, 255, 255))
                text_rect = text.get_rect(center=rect.center)
                self.screen.blit(text, text_rect)
        
        # Start button
        start_rect = pg.Rect(self.screen_width // 2 - 100, 500, 200, 50)
        pg.draw.rect(self.screen, (0, 0, 200), start_rect)
        text = self.font.render("START", True, (255, 255, 255))
        text_rect = text.get_rect(center=start_rect.center)
        self.screen.blit(text, text_rect)

    def draw_game_over(self): ##
        # Semi-transparent overlay
        overlay = pg.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((255, 255, 255))
        self.screen.blit(overlay, (0, 0))
        
        # Game over panel
        panel_rect = pg.Rect(self.screen_width // 2 - 200, 250, 400, 300)
        pg.draw.rect(self.screen, (255, 255, 255), panel_rect)
        pg.draw.rect(self.screen, (0, 0, 0), panel_rect, 3)
        
        # Winner text
        if self.game_mode == GameMode.VS_BOT:
            if self.winner == 1:
                winner_text = "You Win!"
            else:
                winner_text = "Bot Wins!"
        else:
            winner_text = f"Player {self.winner} Wins!"
        
        text = self.font_large.render(winner_text, True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.screen_width // 2, 320))
        self.screen.blit(text, text_rect)
        
        # Buttons
        restart_rect = pg.Rect(self.screen_width // 2 - 100, 400, 200, 50)
        pg.draw.rect(self.screen, (0, 150, 0), restart_rect)
        text = self.font.render("Play Again", True, (255, 255, 255))
        text_rect = text.get_rect(center=restart_rect.center)
        self.screen.blit(text, text_rect)
        
        menu_rect = pg.Rect(self.screen_width // 2 - 100, 470, 200, 50)
        pg.draw.rect(self.screen, (150, 150, 150), menu_rect)
        text = self.font.render("Main Menu", True, (255, 255, 255))
        text_rect = text.get_rect(center=menu_rect.center)
        self.screen.blit(text, text_rect)
    
    def reset_game(self): ##
        self.active_numbers = []
        self.selected_numbers = []
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.bot_thinking = False
        
        # Add two random starting numbers
        num1 = random.randint(20, 40)
        num2 = random.randint(60, 80)
        self.active_numbers = [num1, num2]

    def draw_game_stats(self, screen, panel_rect):
        """Draw game statistics"""
        colors = self.theme
        
        # Stats background
        stats_rect = pg.Rect(panel_rect.x + 50, panel_rect.y + 180, 
                            panel_rect.width - 100, 120)
        stats_surface = pg.Surface((stats_rect.width, stats_rect.height), pg.SRCALPHA)
        pg.draw.rect(stats_surface, (*colors['GLASS'][:3], 100), 
                    (0, 0, stats_rect.width, stats_rect.height), 
                    border_radius=10)
        screen.blit(stats_surface, stats_rect)
        
        # Calculate stats
        total_moves = len(self.move_history)
        game_duration = int(time.time() - self.game_start_time) if hasattr(self, 'game_start_time') else 0
        minutes = game_duration // 60
        seconds = game_duration % 60
        
        # Stats to display
        stats = [
            ("Total Moves", str(total_moves), colors['PRIMARY']),
            ("Game Duration", f"{minutes}:{seconds:02d}", colors['SECONDARY']),
            ("Numbers Used", f"{len(self.active_numbers)}/100", colors['ACCENT']),
        ]
        
        # Draw stats in columns
        stat_width = stats_rect.width // 3
        for i, (label, value, color) in enumerate(stats):
            x = stats_rect.x + i * stat_width + stat_width // 2
            
            # Icon background
            icon_rect = pg.Rect(x - 30, stats_rect.y + 20, 60, 60)
            pg.draw.circle(screen, (*color[:3], 30), icon_rect.center, 30)
            pg.draw.circle(screen, color, icon_rect.center, 30, 2)
            
            # Value (large)
            value_surface = self.font_large.render(value, True, color)
            value_rect = value_surface.get_rect(center=(x, stats_rect.y + 45))
            screen.blit(value_surface, value_rect)
            
            # Label (small)
            label_surface = self.font_small.render(label, True, colors['TEXT_MUTED'])
            label_rect = label_surface.get_rect(center=(x, stats_rect.y + 75))
            screen.blit(label_surface, label_rect)

    def draw_game_over_buttons(self, screen, panel_rect, current_time):
        """Draw action buttons for game over screen"""
        colors = self.theme
        
        button_y = panel_rect.y + 320
        button_width = 180
        button_height = 50
        spacing = 40
        
        buttons = [
            ("Play Again", colors['SUCCESS'], self.reset_game),
            ("Main Menu", colors['PRIMARY'], self.show_main_menu)
        ]
        
        start_x = panel_rect.centerx - (button_width + spacing // 2)
        
        for i, (text, color, action) in enumerate(buttons):
            button_x = start_x + i * (button_width + spacing)
            button_rect = pg.Rect(button_x, button_y, button_width, button_height)
            
            # Hover effect
            mouse_pos = pg.mouse.get_pos()
            is_hover = button_rect.collidepoint(mouse_pos)
            
            if is_hover:
                # Elevated shadow
                shadow_rect = button_rect.copy()
                shadow_rect.y += 5
                pg.draw.rect(screen, colors['CARD_SHADOW'], shadow_rect, border_radius=25)
                
                # Pulse effect
                scale = 1.05 + 0.05 * math.sin(current_time * 4)
                button_rect = button_rect.inflate(int(button_width * (scale - 1)), 
                                                int(button_height * (scale - 1)))
            
            # Button background
            pg.draw.rect(screen, color, button_rect, border_radius=25)
            
            # Button text
            text_surface = self.font.render(text, True, (255, 255, 255))
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

    def show_main_menu(self):
        """Return to main menu"""
        self.show_menu = True
        self.game_over = False
        if hasattr(self, 'game_over_particles_created'):
            del self.game_over_particles_created
        if hasattr(self, 'game_over_time'):
            del self.game_over_time

    def make_move(self):
        if len(self.selected_numbers) != 2:
            return False
        
        num1, num2 = self.selected_numbers
        diff = abs(num1 - num2)
        
        if diff in self.active_numbers:
            self.selected_numbers = []
            return False
        
        # Valid move
        self.active_numbers.append(diff)
        self.move_history.append({
            'player': self.current_player,
            'num1': num1,
            'num2': num2,
            'diff': diff
        })
        
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
        # Check if there are any valid moves left
        valid_moves = []
        for i in range(len(self.active_numbers)):
            for j in range(i + 1, len(self.active_numbers)):
                diff = abs(self.active_numbers[i] - self.active_numbers[j])
                if diff not in self.active_numbers:
                    valid_moves.append((self.active_numbers[i], self.active_numbers[j]))
        
        if not valid_moves:
            self.game_over = True
            # The current player loses (can't make a move)
            self.winner = 2 if self.current_player == 1 else 1
            
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