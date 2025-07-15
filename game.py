import pygame as pg
import sys
import gi
import random
from enum import Enum
import time
from gettext import gettext as _
from config import Theme


gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    EXPERT = 3

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
        self.canvas = None
        self.show_help = False
        self.clock = None
        self.move_history = []
        self.show_menu = True
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
        self.difficulty = Difficulty.EASY
        self.reset_game()
        self.menu_buttons = []
        
        self.font_small = None
        self.font = None
        self.font_large = None
        self.title_font = None
        
        self.bot_avatar = None

    def toggle_theme(self):
        pass
        
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
        
        self.setup_squares()
        self.setup_menu_buttons()

        while self.running:
            while Gtk.events_pending():
                Gtk.main_iteration()

            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pg.quit()
        sys.exit(0)

    def setup_squares(self):
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

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.handle_click(event.pos)
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if self.show_help:
                        self.show_help = False 
                    elif not self.show_menu:
                        self.show_menu = True
                        self.reset_game()
                
    def handle_click(self, mouse_pos):
        if self.show_help:
            self.show_help = False
            return
        if self.show_menu:
            self.handle_menu_click(mouse_pos)
        elif not self.game_over:
            self.handle_game_click(mouse_pos)
        else:
            restart_rect = pg.Rect(self.screen_width // 2 - 100, 400, 200, 50)
            menu_rect = pg.Rect(self.screen_width // 2 - 100, 470, 200, 50)
            if restart_rect.collidepoint(mouse_pos):
                self.reset_game()
            elif menu_rect.collidepoint(mouse_pos):
                self.show_menu = True
                self.reset_game()

    def handle_menu_click(self, mouse_pos):
        if self.menu_buttons['vs_bot'].collidepoint(mouse_pos):
            self.game_mode = GameMode.VS_BOT
        elif self.menu_buttons['multiplayer'].collidepoint(mouse_pos):
            self.game_mode = GameMode.LOCAL_MULTIPLAYER
        elif self.game_mode == GameMode.VS_BOT:
            if self.menu_buttons['easy'].collidepoint(mouse_pos):
                self.difficulty = Difficulty.EASY
            elif self.menu_buttons['medium'].collidepoint(mouse_pos):
                self.difficulty = Difficulty.MEDIUM
            elif self.menu_buttons['expert'].collidepoint(mouse_pos):
                self.difficulty = Difficulty.EXPERT
        elif self.menu_buttons['start'].collidepoint(mouse_pos):
            self.show_menu = False
            self.reset_game()
        elif self.menu_buttons['help'].collidepoint(mouse_pos):
            self.show_help = True
    
    def handle_game_click(self, mouse_pos):
        if self.current_player == 1 or self.game_mode == GameMode.LOCAL_MULTIPLAYER:
            for num, rect in self.squares.items():
                if rect.collidepoint(mouse_pos) and num in self.active_numbers:
                    self.select_number(num)
                    if len(self.selected_numbers) == 2:
                        if self.make_move():
                            self.check_game_over()
    
    def select_number(self, number):
        if number not in self.active_numbers:
            return False
        
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
        if (self.current_player == 2 and not self.game_over and 
            self.game_mode == GameMode.VS_BOT and not self.show_menu):
            if not self.bot_thinking:
                self.bot_thinking = True
                self.bot_timer = pg.time.get_ticks()
            elif pg.time.get_ticks() - self.bot_timer >= 1000:
                if self.bot_move():
                    if self.make_move():
                        self.check_game_over()
                self.bot_thinking = False

    def draw(self):
        self.screen.fill((240, 240, 240))

        if self.show_help:
            self.draw_help()
        if self.show_menu:
            self.draw_menu()
        else:
            self.draw_game()
            if self.game_over:
                self.draw_game_over()
        
        pg.display.flip()

    def draw_help(self):
        # Semi-transparent overlay
        overlay = pg.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(230)
        overlay.fill((240, 240, 240))
        self.screen.blit(overlay, (0, 0))
        
        # Help panel
        panel_rect = pg.Rect(self.screen_width // 2 - 300, 100, 600, 500)
        pg.draw.rect(self.screen, (255, 255, 255), panel_rect)
        pg.draw.rect(self.screen, (0, 0, 0), panel_rect, 3)
        
        # Title
        title = self.font_large.render("How to Play", True, (0, 0, 0))
        title_rect = title.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Help content
        help_text = [
            "Euclid's Game Rules:",
            "",
            "1. Players take turns selecting two numbers",
            "2. Calculate the absolute difference",
            "3. If the difference is not on the board, add it",
            "4. The player who cannot make a move loses",
            "",
            "Example: Select 15 and 10 → difference is 5",
            "If 5 is not on the board, it gets added",
            "",
            "Controls:",
            "• Click numbers to select them",
            "• ESC: Back to menu",
            "",
            "Click anywhere to close this help"
        ]
        
        y_offset = 200
        for line in help_text:
            if line:
                font = self.font if line.endswith(":") else self.font_small
                text = font.render(line, True, (0, 0, 0))
                text_rect = text.get_rect(center=(self.screen_width // 2, y_offset))
                self.screen.blit(text, text_rect)
            y_offset += 25
    
    def draw_game(self):
        title = self.font_large.render("Euclid's Game", True, (0, 0, 0))
        self.screen.blit(title, (20, 20))
        
        if self.game_mode == GameMode.VS_BOT:
            player_text = "Your Turn" if self.current_player == 1 else "Bot's Turn"
        else:
            player_text = f"Player {self.current_player}'s Turn"
        
        turn_text = self.font.render(player_text, True, (0, 0, 0))
        self.screen.blit(turn_text, (20, 80))
        
        for num, rect in self.squares.items():
            if num in self.active_numbers:
                if num in self.selected_numbers:
                    color = (255, 200, 0)
                else:
                    color = (200, 200, 200)
                
                pg.draw.rect(self.screen, color, rect)
                pg.draw.rect(self.screen, (0, 0, 0), rect, 2)
                
                text = self.font_small.render(str(num), True, (0, 0, 0))
                text_rect = text.get_rect(center=rect.center)
                self.screen.blit(text, text_rect)
        
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
        
        history_text = self.font.render("Move History:", True, (0, 0, 0))
        self.screen.blit(history_text, (850, 150))
        
        y_offset = 180
        for i, move in enumerate(self.move_history[-10:]):
            text = f"P{move['player']}: {move['num1']} - {move['num2']} = {move['diff']}"
            move_text = self.font_small.render(text, True, (0, 0, 0))
            self.screen.blit(move_text, (850, y_offset))
            y_offset += 25

    def draw_menu(self):
        # Title
        title = self.title_font.render("EUCLID'S GAME", True, (50, 50, 50))
        title_rect = title.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_small.render("A Mathematical Strategy Game", True, (100, 100, 100))
        subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Game Mode Section
        mode_text = self.font.render("Select Game Mode", True, (0, 0, 0))
        mode_rect = mode_text.get_rect(center=(self.screen_width // 2, 250))
        self.screen.blit(mode_text, mode_rect)
        
        # VS Bot button
        bot_color = (0, 150, 200) if self.game_mode == GameMode.VS_BOT else (150, 150, 150)
        pg.draw.rect(self.screen, bot_color, self.menu_buttons['vs_bot'], border_radius=10)
        text = self.font.render("VS Bot", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.menu_buttons['vs_bot'].center)
        self.screen.blit(text, text_rect)
        
        # Multiplayer button
        multi_color = (0, 150, 200) if self.game_mode == GameMode.LOCAL_MULTIPLAYER else (150, 150, 150)
        pg.draw.rect(self.screen, multi_color, self.menu_buttons['multiplayer'], border_radius=10)
        text = self.font.render("2 Players", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.menu_buttons['multiplayer'].center)
        self.screen.blit(text, text_rect)
        
        # Difficulty section (only for VS Bot)
        if self.game_mode == GameMode.VS_BOT:
            diff_text = self.font.render("Select Difficulty", True, (0, 0, 0))
            diff_rect = diff_text.get_rect(center=(self.screen_width // 2, 360))
            self.screen.blit(diff_text, diff_rect)
            
            difficulties = [
                (Difficulty.EASY, "Easy", self.menu_buttons['easy'], (100, 200, 100)),
                (Difficulty.MEDIUM, "Medium", self.menu_buttons['medium'], (200, 200, 50)),
                (Difficulty.EXPERT, "Expert", self.menu_buttons['expert'], (200, 100, 100))
            ]
            
            for diff, name, rect, color in difficulties:
                btn_color = color if self.difficulty == diff else (150, 150, 150)
                pg.draw.rect(self.screen, btn_color, rect, border_radius=8)
                text = self.font_small.render(name, True, (255, 255, 255))
                text_rect = text.get_rect(center=rect.center)
                self.screen.blit(text, text_rect)
        
        # Start button
        pg.draw.rect(self.screen, (0, 200, 100), self.menu_buttons['start'], border_radius=15)
        text = self.font_large.render("START GAME", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.menu_buttons['start'].center)
        self.screen.blit(text, text_rect)
        
        # Help button
        pg.draw.rect(self.screen, (100, 100, 100), self.menu_buttons['help'], border_radius=8)
        text = self.font.render("?", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.menu_buttons['help'].center)
        self.screen.blit(text, text_rect)
        
        # Instructions
        instructions = [
            "How to Play:",
            "1. Select two numbers from the board",
            "2. Their difference will be added if it's new",
            "3. Player who can't make a move loses"
        ]
        
        y_offset = 600
        for instruction in instructions:
            text = self.font_small.render(instruction, True, (80, 80, 80))
            text_rect = text.get_rect(center=(self.screen_width // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 30

    def draw_game_over(self):
        overlay = pg.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((255, 255, 255))
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pg.Rect(self.screen_width // 2 - 200, 250, 400, 300)
        pg.draw.rect(self.screen, (255, 255, 255), panel_rect)
        pg.draw.rect(self.screen, (0, 0, 0), panel_rect, 3)
        
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
    
    def reset_game(self):
        self.active_numbers = []
        self.selected_numbers = []
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.bot_thinking = False
        
        num1 = random.randint(20, 40)
        num2 = random.randint(60, 80)
        self.active_numbers = [num1, num2]

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
        
        self.selected_numbers = []
        self.current_player = 2 if self.current_player == 1 else 1
        
        return True

    def bot_move(self):
        if self.game_over:
            return False
        
        valid_moves = []
        for i in range(len(self.active_numbers)):
            for j in range(i + 1, len(self.active_numbers)):
                diff = abs(self.active_numbers[i] - self.active_numbers[j])
                if diff not in self.active_numbers:
                    valid_moves.append((self.active_numbers[i], self.active_numbers[j]))
        
        if valid_moves:
            move = random.choice(valid_moves)
            self.selected_numbers = list(move)
            return True
        return False
    
    def setup_menu_buttons(self):
        """Setup menu button positions"""
        center_x = self.screen_width // 2
        
        self.menu_buttons = {
            'vs_bot': pg.Rect(center_x - 200, 300, 180, 50),
            'multiplayer': pg.Rect(center_x + 20, 300, 180, 50),
            'easy': pg.Rect(center_x - 150, 400, 100, 40),
            'medium': pg.Rect(center_x - 50, 400, 100, 40),
            'expert': pg.Rect(center_x + 50, 400, 100, 40),
            'start': pg.Rect(center_x - 100, 500, 200, 60),
            'help': pg.Rect(20, 20, 40, 40),
        }

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
            
    def quit(self):
        self.running = False

if __name__ == "__main__":
    game = Game()
    game.run()