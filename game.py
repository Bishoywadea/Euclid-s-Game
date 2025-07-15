import pygame as pg
import sys
import gi
import random
from enum import Enum
import time
from gettext import gettext as _


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
                    if not self.show_menu:
                        self.show_menu = True
                        self.reset_game()
                
    def handle_click(self, mouse_pos):
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
        vs_bot_rect = pg.Rect(400, 300, 200, 50)
        multiplayer_rect = pg.Rect(400, 370, 200, 50)
        
        easy_rect = pg.Rect(650, 300, 150, 40)
        medium_rect = pg.Rect(650, 350, 150, 40)
        expert_rect = pg.Rect(650, 400, 150, 40)
        
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

        if self.show_menu:
            self.draw_menu()
        else:
            self.draw_game()
            if self.game_over:
                self.draw_game_over()
        
        pg.display.flip()
    
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
        title = self.font_large.render("EUCLID'S GAME", True, (0, 0, 0))
        title_rect = title.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title, title_rect)
        
        inst = self.font_small.render("Select two numbers to find their difference", True, (100, 100, 100))
        inst_rect = inst.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(inst, inst_rect)
        
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
        
        start_rect = pg.Rect(self.screen_width // 2 - 100, 500, 200, 50)
        pg.draw.rect(self.screen, (0, 0, 200), start_rect)
        text = self.font.render("START", True, (255, 255, 255))
        text_rect = text.get_rect(center=start_rect.center)
        self.screen.blit(text, text_rect)

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
            
    def quit(self):
        self.running = False

if __name__ == "__main__":
    game = Game()
    game.run()