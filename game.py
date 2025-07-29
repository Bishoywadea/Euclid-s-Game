# This file is part of the Euclid's game.
# Copyright (C) 2025 Bishoy Wadea
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
import random
from enum import Enum

class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    EXPERT = 3

class GameMode(Enum):
    VS_BOT = 1
    LOCAL_MULTIPLAYER = 2
    NETWORK_MULTIPLAYER = 3

class Bot:
    def __init__(self, difficulty):
        self.difficulty = difficulty
    
    def get_move(self, game_state):
        active_numbers = game_state['active_numbers']
        valid_moves = []
        
        for i in range(len(active_numbers)):
            for j in range(i + 1, len(active_numbers)):
                diff = abs(active_numbers[i] - active_numbers[j])
                if diff not in active_numbers:
                    valid_moves.append((active_numbers[i], active_numbers[j]))
        
        if not valid_moves:
            return None
        
        if self.difficulty == Difficulty.EASY:
            return random.choice(valid_moves)
        elif self.difficulty == Difficulty.MEDIUM:
            valid_moves.sort(key=lambda x: abs(x[0] - x[1]))
            return valid_moves[0]
        else: 
            best_move = None
            min_opponent_moves = float('inf')
            
            for move in valid_moves:
                temp_numbers = active_numbers.copy()
                diff = abs(move[0] - move[1])
                temp_numbers.append(diff)
                
                opponent_moves = 0
                for i in range(len(temp_numbers)):
                    for j in range(i + 1, len(temp_numbers)):
                        if abs(temp_numbers[i] - temp_numbers[j]) not in temp_numbers:
                            opponent_moves += 1
                
                if opponent_moves < min_opponent_moves:
                    min_opponent_moves = opponent_moves
                    best_move = move
            
            return best_move

class Game(Gtk.Window):
    def __init__(self):
        super().__init__(title="Euclid's Game")
        self.set_default_size(800, 600)
        self.set_border_width(10)
        
        self.game_mode = GameMode.VS_BOT
        self.difficulty = Difficulty.MEDIUM
        self.bot = Bot(self.difficulty)
        self.active_numbers = []
        self.selected_numbers = []
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []

        self._collab = None
        self.is_host = False
        self.network_players = []
        self.my_player_number = None
        self.opponent_buddy = None
        self.game_started = False
        
        self._setup_css()
        self._build_ui()
        self.show_menu()
        
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
    
    def _setup_css(self):
        css_provider = Gtk.CssProvider()
        css = b"""
        #menu_box {
            background-color: #f0f0f0;
            padding: 20px;
        }
        
        #game_box {
            background-color: #ffffff;
        }
        
        .number_button {
            font-size: 14pt;
            min-width: 50px;
            min-height: 40px;
            margin: 2px;
        }
        
        .number_button_active {
            background-color: #4CAF50;
            color: white;
        }
        
        .number_button_selected {
            background-color: #2196F3;
            color: white;
        }
        
        .info_label {
            font-size: 16pt;
            font-weight: bold;
            padding: 10px;
        }
        
        .turn_label {
            font-size: 14pt;
            padding: 5px;
        }
        
        .history_label {
            font-size: 10pt;
            padding: 2px;
        }

        .player1_move {
            color: #d32f2f;  /* Red for player 1 */
            font-weight: bold;
        }
        
        .player2_move {
            color: #1976d2;  /* Blue for player 2 */
            font-weight: bold;
        }
        
        .number_button:disabled {
            opacity: 0.6;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _build_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_box)
        
        self.menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.menu_box.set_name("menu_box")
        self.menu_box.set_halign(Gtk.Align.CENTER)
        self.menu_box.set_valign(Gtk.Align.CENTER)
        
        self.game_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.game_box.set_name("game_box")
        
        self._build_menu()
        self._build_lobby_ui()
        self._build_game_ui()
    
    def _build_menu(self):
        title = Gtk.Label(label="Euclid's Game")
        title.get_style_context().add_class("info_label")
        self.menu_box.pack_start(title, False, False, 0)
        
        mode_label = Gtk.Label(label="Select Game Mode:")
        self.menu_box.pack_start(mode_label, False, False, 0)
        
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.vs_bot_radio = Gtk.RadioButton.new_with_label(None, "VS Bot")
        self.vs_human_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.vs_bot_radio, "VS Human"
        )
        self.vs_network_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.vs_bot_radio, "VS Human (Network)"
        )
        mode_box.pack_start(self.vs_bot_radio, False, False, 0)
        mode_box.pack_start(self.vs_human_radio, False, False, 0)
        mode_box.pack_start(self.vs_network_radio, False, False, 0)
        self.menu_box.pack_start(mode_box, False, False, 0)
        
        self.difficulty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        diff_label = Gtk.Label(label="Select Difficulty:")
        self.difficulty_box.pack_start(diff_label, False, False, 0)
        
        diff_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.easy_radio = Gtk.RadioButton.new_with_label(None, "Easy")
        self.medium_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.easy_radio, "Medium"
        )
        self.expert_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.easy_radio, "Expert"
        )
        self.medium_radio.set_active(True)
        
        diff_button_box.pack_start(self.easy_radio, False, False, 0)
        diff_button_box.pack_start(self.medium_radio, False, False, 0)
        diff_button_box.pack_start(self.expert_radio, False, False, 0)
        self.difficulty_box.pack_start(diff_button_box, False, False, 0)
        
        self.menu_box.pack_start(self.difficulty_box, False, False, 0)
        
        start_button = Gtk.Button(label="Start Game")
        start_button.connect("clicked", self.on_start_game)
        self.menu_box.pack_start(start_button, False, False, 20)
        
        self.vs_bot_radio.connect("toggled", self.on_mode_changed)
    
    def _build_game_ui(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_homogeneous(False)
        
        back_button = Gtk.Button(label="Back to Menu")
        back_button.connect("clicked", lambda w: self.show_menu())
        header_box.pack_start(back_button, False, False, 0)
        
        self.turn_label = Gtk.Label()
        self.turn_label.get_style_context().add_class("turn_label")
        header_box.pack_start(self.turn_label, True, True, 0)
        
        self.connection_status = Gtk.Label()
        self.connection_status.set_markup("<span color='green'>●</span> Connected")
        header_box.pack_end(self.connection_status, False, False, 10)
        
        self.game_box.pack_start(header_box, False, False, 0)
        
        game_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.game_box.pack_start(game_paned, True, True, 0)
        
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        board_label = Gtk.Label(label="Number Board")
        board_label.get_style_context().add_class("info_label")
        left_box.pack_start(board_label, False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_width(400)
        
        self.numbers_grid = Gtk.FlowBox()
        self.numbers_grid.set_valign(Gtk.Align.START)
        self.numbers_grid.set_max_children_per_line(10)
        self.numbers_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.numbers_grid)
        
        left_box.pack_start(scrolled, True, True, 0)
        
        self.selection_label = Gtk.Label()
        self.selection_label.set_markup("<b>Selection:</b> None")
        left_box.pack_start(self.selection_label, False, False, 0)
        
        self.calculation_label = Gtk.Label()
        left_box.pack_start(self.calculation_label, False, False, 0)
        
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_box.set_margin_left(10)
        
        info_label = Gtk.Label(label="Game Info")
        info_label.get_style_context().add_class("info_label")
        right_box.pack_start(info_label, False, False, 0)
        
        self.stats_label = Gtk.Label()
        self.stats_label.set_halign(Gtk.Align.START)
        right_box.pack_start(self.stats_label, False, False, 0)
        
        history_label = Gtk.Label(label="Move History:")
        history_label.set_halign(Gtk.Align.START)
        right_box.pack_start(history_label, False, False, 0)
        
        history_scrolled = Gtk.ScrolledWindow()
        history_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        history_scrolled.set_min_content_height(200)
        
        self.history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        history_scrolled.add(self.history_box)
        right_box.pack_start(history_scrolled, True, True, 0)
        
        game_paned.pack1(left_box, True, False)
        game_paned.pack2(right_box, False, False)
        game_paned.set_position(500)
    
    def show_menu(self):
        for child in self.main_box.get_children():
            self.main_box.remove(child)
        self.main_box.pack_start(self.menu_box, True, True, 0)
        self.main_box.show_all()
    
    def show_game(self):
        for child in self.main_box.get_children():
            self.main_box.remove(child)
        self.main_box.pack_start(self.game_box, True, True, 0)
        
        if hasattr(self, 'connection_status'):
            if self.game_mode == GameMode.NETWORK_MULTIPLAYER:
                self.connection_status.show()
            else:
                self.connection_status.hide()
        
        self.main_box.show_all()
    
    def on_mode_changed(self, widget):
        if self.vs_bot_radio.get_active():
            self.difficulty_box.show()
        else:
            self.difficulty_box.hide()
    
    def on_start_game(self, widget):
        if self.vs_bot_radio.get_active():
            self.game_mode = GameMode.VS_BOT
            if self.easy_radio.get_active():
                self.difficulty = Difficulty.EASY
            elif self.medium_radio.get_active():
                self.difficulty = Difficulty.MEDIUM
            else:
                self.difficulty = Difficulty.EXPERT
            self.bot = Bot(self.difficulty)
            self.reset_game()
            self.show_game()
        elif self.vs_human_radio.get_active():
            self.game_mode = GameMode.LOCAL_MULTIPLAYER
            self.reset_game()
            self.show_game()
        else:
            self.game_mode = GameMode.NETWORK_MULTIPLAYER
            self.is_host = True
            self.show_lobby()
    
    def reset_game(self):
        self.active_numbers = []
        self.selected_numbers = []
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []
        
        for child in self.numbers_grid.get_children():
            self.numbers_grid.remove(child)
        
        for child in self.history_box.get_children():
            self.history_box.remove(child)
        
        num1 = random.randint(20, 40)
        num2 = random.randint(60, 80)
        self.active_numbers = [num1, num2]
        
        self.update_board()
        self.update_turn_label()
        self.update_stats()
    
    def update_board(self):
        print(f"DEBUG: update_board() - current_player={self.current_player}, my_player={self.my_player_number}, mode={self.game_mode}")
        
        for child in self.numbers_grid.get_children():
            self.numbers_grid.remove(child)
        
        for i in range(1, 101):
            if i in self.active_numbers:
                button = Gtk.Button(label=str(i))
                button.get_style_context().add_class("number_button")
                button.get_style_context().add_class("number_button_active")
                
                if i in self.selected_numbers:
                    button.get_style_context().add_class("number_button_selected")
                
                if (self.game_mode == GameMode.NETWORK_MULTIPLAYER and 
                    self.current_player != self.my_player_number):
                    button.set_sensitive(False)
                
                button.connect("clicked", self.on_number_clicked, i)
                self.numbers_grid.add(button)
        
        self.numbers_grid.show_all()
    
    def on_number_clicked(self, button, number):
        if self.game_over:
            return
        
        if self.current_player == 2 and self.game_mode == GameMode.VS_BOT:
            return 
        
        if number in self.selected_numbers:
            self.selected_numbers.remove(number)
        else:
            if len(self.selected_numbers) < 2:
                self.selected_numbers.append(number)
        
        self.update_board()
        self.update_selection_display()
        
        if len(self.selected_numbers) == 2:
            self.make_move()
    
    def update_selection_display(self):
        if not self.selected_numbers:
            self.selection_label.set_markup("<b>Selection:</b> None")
            self.calculation_label.set_text("")
        elif len(self.selected_numbers) == 1:
            self.selection_label.set_markup(f"<b>Selection:</b> {self.selected_numbers[0]}")
            self.calculation_label.set_text("")
        else:
            num1, num2 = self.selected_numbers
            diff = abs(num1 - num2)
            self.selection_label.set_markup(f"<b>Selection:</b> {num1}, {num2}")
            
            if diff in self.active_numbers:
                self.calculation_label.set_markup(
                    f"<span color='red'>{num1} - {num2} = {diff} (Already exists!)</span>"
                )
            else:
                self.calculation_label.set_markup(
                    f"<span color='green'>{num1} - {num2} = {diff} ✓</span>"
                )
    
    def make_move(self):
        if len(self.selected_numbers) != 2:
            return False
        
        num1, num2 = self.selected_numbers
        diff = abs(num1 - num2)
        
        if diff in self.active_numbers:
            self.selected_numbers = []
            self.update_board()
            self.update_selection_display()
            return False
        
        if (self.game_mode == GameMode.NETWORK_MULTIPLAYER and 
            self.current_player != self.my_player_number):
            print("Not your turn!")
            return False

        print(f"DEBUG: Making move - Player {self.current_player}: {num1} - {num2} = {diff}")

        self.active_numbers.append(diff)
        self.active_numbers.sort()
        
        move_text = f"Player {self.current_player}: {num1} - {num2} = {diff}"
        move_data = {
            'player': self.current_player,
            'num1': num1,
            'num2': num2,
            'diff': diff
        }
        self.move_history.append(move_data)
        
        history_label = Gtk.Label(label=move_text)
        history_label.get_style_context().add_class("history_label")
        history_label.get_style_context().add_class(f"player{self.current_player}_move")
        history_label.set_halign(Gtk.Align.START)
        self.history_box.pack_start(history_label, False, False, 0)
        self.history_box.show_all()
        
        if self.game_mode == GameMode.NETWORK_MULTIPLAYER:
            if self._collab:
                move_message = {
                    'action': 'move',
                    'player': self.current_player,
                    'num1': num1,
                    'num2': num2,
                    'diff': diff,
                    'active_numbers': self.active_numbers.copy()
                }
                print(f"DEBUG: Sending move message: {move_message}")
                try:
                    self._collab.post(move_message)
                    print("DEBUG: Move message sent successfully")
                except Exception as e:
                    print(f"ERROR: Failed to send move: {e}")
            else:
                print("ERROR: No collab wrapper available to send move!")
        
        self.selected_numbers = []
        self.update_board()
        self.update_selection_display()
        self.update_stats()
        
        if self.check_game_over():
            self.handle_game_over()
        else:
            self.current_player = 2 if self.current_player == 1 else 1
            self.update_turn_label()
            
            if self.current_player == 2 and self.game_mode == GameMode.VS_BOT:
                GLib.timeout_add(1000, self.bot_move)
        
        return True
    
    def bot_move(self):
        if self.game_over:
            return False
        
        move = self.bot.get_move({'active_numbers': self.active_numbers})
        if move:
            self.selected_numbers = list(move)
            self.update_board()
            self.update_selection_display()
            GLib.timeout_add(500, self.make_move)
        
        return False
    
    def check_game_over(self):
        for i in range(len(self.active_numbers)):
            for j in range(i + 1, len(self.active_numbers)):
                diff = abs(self.active_numbers[i] - self.active_numbers[j])
                if diff not in self.active_numbers:
                    return False
        return True
    
    def handle_game_over(self):
        self.game_over = True
        self.winner = 2 if self.current_player == 1 else 1
        
        if self.game_mode == GameMode.NETWORK_MULTIPLAYER and self._collab:
            self._collab.post({
                'action': 'game_over',
                'winner': self.winner,
                'final_state': self.active_numbers.copy()
            })
        
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Game Over!"
        )
        
        if self.game_mode == GameMode.VS_BOT:
            if self.winner == 1:
                message = "Congratulations! You won!"
            else:
                message = "The bot won this time. Try again!"
        elif self.game_mode == GameMode.LOCAL_MULTIPLAYER:
            message = f"Player {self.winner} wins!"
        else:
            if self.winner == self.my_player_number:
                message = "Congratulations! You won!"
            else:
                opponent_name = self.opponent_buddy.props.nick if self.opponent_buddy else "Opponent"
                message = f"{opponent_name} wins!"
        
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        
        self.show_menu()
    
    def update_turn_label(self):
        if self.game_mode == GameMode.VS_BOT:
            if self.current_player == 1:
                self.turn_label.set_markup("<b>Your Turn</b>")
            else:
                self.turn_label.set_markup("<b>Bot's Turn</b>")
        elif self.game_mode == GameMode.LOCAL_MULTIPLAYER:
            self.turn_label.set_markup(f"<b>Player {self.current_player}'s Turn</b>")
        elif self.game_mode == GameMode.NETWORK_MULTIPLAYER:
            if self.current_player == self.my_player_number:
                self.turn_label.set_markup("<b>Your Turn</b>")
            else:
                opponent_name = self.opponent_buddy.props.nick if self.opponent_buddy else "Opponent"
                self.turn_label.set_markup(f"<b>{opponent_name}'s Turn</b>")
    
    def update_stats(self):
        valid_moves = self.count_valid_moves()
        stats_text = f"""Active Numbers: {len(self.active_numbers)}
Moves Made: {len(self.move_history)}
Valid Moves Left: {valid_moves}"""
        self.stats_label.set_text(stats_text)
    
    def count_valid_moves(self):
        count = 0
        for i in range(len(self.active_numbers)):
            for j in range(i + 1, len(self.active_numbers)):
                diff = abs(self.active_numbers[i] - self.active_numbers[j])
                if diff not in self.active_numbers:
                    count += 1
        return count
    
    def save_state(self):
        """Return the current game state as a dictionary"""
        import json
    
        state = {}
        
        try:
            state['game_mode'] = self.game_mode.value
            json.dumps({'test': state['game_mode']})
        except Exception as e:
            print(f"Error with game_mode: {e}")
            state['game_mode'] = 1
        
        try:
            state['difficulty'] = self.difficulty.value
            json.dumps({'test': state['difficulty']})
        except Exception as e:
            print(f"Error with difficulty: {e}")
            state['difficulty'] = 2
        
        try:
            state['active_numbers'] = list(self.active_numbers)
            json.dumps({'test': state['active_numbers']})
        except Exception as e:
            print(f"Error with active_numbers: {e}, type: {type(self.active_numbers)}")
            state['active_numbers'] = []
        
        try:
            state['selected_numbers'] = list(self.selected_numbers)
            json.dumps({'test': state['selected_numbers']})
        except Exception as e:
            print(f"Error with selected_numbers: {e}")
            state['selected_numbers'] = []
        
        try:
            state['current_player'] = int(self.current_player)
            json.dumps({'test': state['current_player']})
        except Exception as e:
            print(f"Error with current_player: {e}")
            state['current_player'] = 1
        
        try:
            state['game_over'] = bool(self.game_over)
            json.dumps({'test': state['game_over']})
        except Exception as e:
            print(f"Error with game_over: {e}")
            state['game_over'] = False
        
        try:
            state['winner'] = int(self.winner) if self.winner is not None else None
            json.dumps({'test': state['winner']})
        except Exception as e:
            print(f"Error with winner: {e}")
            state['winner'] = None
        
        try:
            state['move_history'] = []
            for move in self.move_history:
                move_data = {
                    'player': int(move.get('player', 0)),
                    'num1': int(move.get('num1', 0)),
                    'num2': int(move.get('num2', 0)),
                    'diff': int(move.get('diff', 0))
                }
                state['move_history'].append(move_data)
            json.dumps({'test': state['move_history']})
        except Exception as e:
            print(f"Error with move_history: {e}")
            state['move_history'] = []
        
        try:
            state['show_menu'] = bool(self.show_menu)
            json.dumps({'test': state['show_menu']})
        except Exception as e:
            print(f"Error with show_menu: {e}")
            state['show_menu'] = True
        
        try:
            if hasattr(self, 'theme') and hasattr(Theme, 'LIGHT'):
                state['theme'] = 'LIGHT' if self.theme == Theme.LIGHT else 'DARK'
            else:
                state['theme'] = 'LIGHT'
            json.dumps({'test': state['theme']})
        except Exception as e:
            print(f"Error with theme: {e}")
            state['theme'] = 'LIGHT'
        
        return state
    
    def load_state(self, state):
        """Load game state from a dictionary"""
        print("DEBUG: Starting load_state")
        print(f"DEBUG: State keys received: {list(state.keys()) if state else 'None'}")
        
        try:
            try:
                game_mode_value = state.get('game_mode', GameMode.VS_BOT.value)
                print(f"DEBUG: Loading game_mode = {game_mode_value}")
                self.game_mode = GameMode(game_mode_value)
                print(f"DEBUG: Game mode set to: {self.game_mode}")
            except Exception as e:
                print(f"ERROR: Failed to load game_mode: {e}")
                self.game_mode = GameMode.VS_BOT
            
            try:
                difficulty_value = state.get('difficulty', Difficulty.MEDIUM.value)
                print(f"DEBUG: Loading difficulty = {difficulty_value}")
                self.difficulty = Difficulty(difficulty_value)
                self.bot = Bot(self.difficulty)
                print(f"DEBUG: Difficulty set to: {self.difficulty}")
            except Exception as e:
                print(f"ERROR: Failed to load difficulty: {e}")
                self.difficulty = Difficulty.MEDIUM
                self.bot = Bot(self.difficulty)
            
            try:
                self.active_numbers = state.get('active_numbers', [])
                print(f"DEBUG: Loaded {len(self.active_numbers)} active numbers: {self.active_numbers}")
            except Exception as e:
                print(f"ERROR: Failed to load active_numbers: {e}")
                self.active_numbers = []
            
            try:
                self.selected_numbers = state.get('selected_numbers', [])
                print(f"DEBUG: Loaded {len(self.selected_numbers)} selected numbers: {self.selected_numbers}")
            except Exception as e:
                print(f"ERROR: Failed to load selected_numbers: {e}")
                self.selected_numbers = []
            
            try:
                self.current_player = state.get('current_player', 1)
                print(f"DEBUG: Current player = {self.current_player}")
            except Exception as e:
                print(f"ERROR: Failed to load current_player: {e}")
                self.current_player = 1
            
            try:
                self.game_over = state.get('game_over', False)
                print(f"DEBUG: Game over = {self.game_over}")
            except Exception as e:
                print(f"ERROR: Failed to load game_over: {e}")
                self.game_over = False
            
            try:
                self.winner = state.get('winner', None)
                print(f"DEBUG: Winner = {self.winner}")
            except Exception as e:
                print(f"ERROR: Failed to load winner: {e}")
                self.winner = None
            
            try:
                self.move_history = state.get('move_history', [])
                print(f"DEBUG: Loaded {len(self.move_history)} moves in history")
                if self.move_history:
                    print(f"DEBUG: Last move: {self.move_history[-1]}")
            except Exception as e:
                print(f"ERROR: Failed to load move_history: {e}")
                self.move_history = []
            
            game_in_progress = state.get('game_in_progress', False)
            print(f"DEBUG: Game in progress = {game_in_progress}")
            
            if self.active_numbers and len(self.active_numbers) > 0:
                print("DEBUG: Game was in progress, restoring UI")
                
                self.show_game()
                
                self.update_board()
                self.update_turn_label()
                self.update_stats()
                self.update_selection_display()
                
                for child in self.history_box.get_children():
                    self.history_box.remove(child)
                
                for move in self.move_history:
                    move_text = f"Player {move['player']}: {move['num1']} - {move['num2']} = {move['diff']}"
                    history_label = Gtk.Label(label=move_text)
                    history_label.get_style_context().add_class("history_label")
                    history_label.set_halign(Gtk.Align.START)
                    self.history_box.pack_start(history_label, False, False, 0)
                
                self.history_box.show_all()
                
                if (self.current_player == 2 and 
                    self.game_mode == GameMode.VS_BOT and 
                    not self.game_over):
                    print("DEBUG: Scheduling bot move after load")
                    GLib.timeout_add(1500, self.bot_move)
            else:
                print("DEBUG: No game in progress, showing menu")
                self.show_menu()
            
            print("DEBUG: load_state completed successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Fatal error in load_state: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _build_lobby_ui(self):
        """Create the lobby/waiting screen UI"""
        self.lobby_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.lobby_box.set_halign(Gtk.Align.CENTER)
        self.lobby_box.set_valign(Gtk.Align.CENTER)
        
        title = Gtk.Label(label="Network Game Lobby")
        title.get_style_context().add_class("info_label")
        self.lobby_box.pack_start(title, False, False, 0)
        
        self.lobby_status_label = Gtk.Label(label="Waiting for another player to join...")
        self.lobby_box.pack_start(self.lobby_status_label, False, False, 0)
        
        self.lobby_spinner = Gtk.Spinner()
        self.lobby_spinner.start()
        self.lobby_box.pack_start(self.lobby_spinner, False, False, 20)
        
        players_label = Gtk.Label(label="Players:")
        players_label.set_halign(Gtk.Align.START)
        self.lobby_box.pack_start(players_label, False, False, 0)
        
        self.players_listbox = Gtk.ListBox()
        self.players_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(100)
        scrolled.set_min_content_width(300)
        scrolled.add(self.players_listbox)
        self.lobby_box.pack_start(scrolled, False, False, 0)
        
        back_button = Gtk.Button(label="Back to Menu")
        back_button.connect("clicked", self._leave_lobby)
        self.lobby_box.pack_start(back_button, False, False, 20)

    def show_lobby(self):
        """Show the network game lobby"""
        for child in self.main_box.get_children():
            self.main_box.remove(child)
        
        if not hasattr(self, 'lobby_box'):
            self._build_lobby_ui()
        
        self.main_box.pack_start(self.lobby_box, True, True, 0)
        self.main_box.show_all()
        
        self.game_started = False
        self.opponent_buddy = None
        
        for child in self.players_listbox.get_children():
            self.players_listbox.remove(child)
        
        self_row = Gtk.ListBoxRow()
        self_label = Gtk.Label(label=f"{self._get_my_nick()} (You - {'Host' if self.is_host else 'Guest'})")
        self_label.set_halign(Gtk.Align.START)
        self_row.add(self_label)
        self.players_listbox.add(self_row)
        
        if self.is_host:
            self.my_player_number = 1
        else:
            self.my_player_number = 2
        
        self.players_listbox.show_all()

    def _leave_lobby(self, widget):
        """Leave the lobby and go back to menu"""
        self.lobby_spinner.stop()
        self.show_menu()

    def set_collab_wrapper(self, collab):
        """Set the collaboration wrapper reference"""
        self._collab = collab
        self.is_host = False
        self.network_players = []

    def on_collaboration_joined(self):
        """Called when we successfully join a shared activity"""
        if self.game_mode == GameMode.NETWORK_MULTIPLAYER:
            self.is_host = False
            self.update_lobby_status("Connected! Waiting for game to start...")

    def on_buddy_joined(self, buddy):
        """Called when another player joins"""
        print(f"DEBUG: on_buddy_joined called for {buddy.props.nick}")
        
        if self.game_mode == GameMode.NETWORK_MULTIPLAYER and not self.game_started:
            if buddy not in self.network_players:
                buddy_row = Gtk.ListBoxRow()
                buddy_label = Gtk.Label(label=buddy.props.nick)
                buddy_label.set_halign(Gtk.Align.START)
                buddy_row.add(buddy_label)
                buddy_row.buddy = buddy 
                self.players_listbox.add(buddy_row)
                self.players_listbox.show_all()
                
                self.network_players.append(buddy)
                
                num_players = len(self.network_players) + 1 
                self.lobby_status_label.set_text(f"{num_players} players connected")
                
                if len(self.network_players) == 1: 
                    self.opponent_buddy = buddy
                    self.lobby_spinner.stop()
                    
                    if self.is_host:
                        self.lobby_status_label.set_text("Ready! Click 'Start Game' to begin.")
                        self._add_start_button()
                    else:
                        self.lobby_status_label.set_text("Ready! Waiting for host to start game...")
                        
                        if self._collab:
                            self._collab.post({
                                'action': 'player_ready',
                                'player_nick': self._get_my_nick()
                            })

    def _get_my_nick(self):
        """Get our own nickname for display"""
        try:
            from sugar3.profile import get_nick_name
            return get_nick_name()
        except:
            return "Player"

    def on_buddy_left(self, buddy):
        """Called when a player leaves"""
        print(f"DEBUG: on_buddy_left called for {buddy.props.nick}")
        
        if self.game_mode == GameMode.NETWORK_MULTIPLAYER:
            self.network_players = [p for p in self.network_players if p != buddy]
            
            for row in self.players_listbox.get_children():
                if hasattr(row, 'buddy') and row.buddy == buddy:
                    self.players_listbox.remove(row)
                    break
            
            if not self.game_started:
                num_players = len(self.network_players) + 1
                self.lobby_status_label.set_text(f"{num_players} player(s) connected. Waiting for another player...")
                self.lobby_spinner.start()
                
                if hasattr(self, 'lobby_start_button'):
                    self.lobby_box.remove(self.lobby_start_button)
                    del self.lobby_start_button
            else:
                if buddy == self.opponent_buddy:
                    self._handle_opponent_disconnect()

    def _handle_opponent_disconnect(self):
        """Handle when opponent disconnects during game"""
        self.game_over = True
        
        if hasattr(self, 'connection_status'):
            self.connection_status.set_markup("<span color='red'>●</span> Disconnected")
        
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text="Opponent Disconnected"
        )
        dialog.format_secondary_text("Your opponent has left the game.")
        dialog.run()
        dialog.destroy()
        
        self.show_menu()

    def on_message_received(self, buddy, message):
        """Handle incoming collaboration messages"""
        print("DEBUG: on_message_received called in game.py")
        
        if not isinstance(message, dict):
            print(f"ERROR: Message is not a dict, it's {type(message)}")
            return
        
        action = message.get('action')
        print(f"DEBUG: Action = {action}")
        print(f"DEBUG: From buddy = {buddy.props.nick}")
        print(f"DEBUG: Game mode = {self.game_mode}")
        print(f"DEBUG: Game started = {self.game_started}")
        
        if action == 'player_ready':
            if self.is_host and not self.game_started:
                print(f"Player {message.get('player_nick')} is ready")
        
        elif action == 'game_start':
            if not self.is_host and not self.game_started:
                print("Received game start signal from host")
                self.game_started = True
                self.opponent_buddy = buddy
                
                self.my_player_number = 2
                
                self._init_network_game(message)
        
        elif action == 'move':
            print("DEBUG: Received move action")
            if self.game_mode == GameMode.NETWORK_MULTIPLAYER and self.game_started:
                print("DEBUG: Processing opponent move")
                self._handle_opponent_move(message)
            else:
                print(f"DEBUG: Not processing move - game_mode={self.game_mode}, game_started={self.game_started}")
        
        elif action == 'game_over':
            if self.game_mode == GameMode.NETWORK_MULTIPLAYER:
                self._handle_opponent_game_over(message)
        
        else:
            print(f"DEBUG: Unknown action: {action}")
    
    def _handle_opponent_game_over(self, data):
        """Handle game over message from opponent"""
        winner = data.get('winner')
        final_state = data.get('final_state', [])
        
        if sorted(self.active_numbers) != sorted(final_state):
            print("WARNING: Final state mismatch!")
            self.active_numbers = final_state.copy()
        
        self.game_over = True
        self.winner = winner
        
        self.handle_game_over()
    
    def _handle_opponent_move(self, move_data):
        """Process a move received from the opponent"""
        player = move_data.get('player')
        num1 = move_data.get('num1')
        num2 = move_data.get('num2')
        diff = move_data.get('diff')
        received_numbers = move_data.get('active_numbers', [])
        
        print(f"Processing opponent move: {num1} - {num2} = {diff}")
        
        if player != self.current_player:
            print(f"ERROR: Received move for player {player} but current player is {self.current_player}")
            return
        
        if player == self.my_player_number:
            print("ERROR: Received move from opponent but it's marked as our move")
            return
        
        if diff in self.active_numbers:
            print(f"ERROR: Invalid move received - {diff} already exists")
            return
        
        if abs(num1 - num2) != diff:
            print(f"ERROR: Invalid calculation - {num1} - {num2} != {diff}")
            return
        
        if num1 not in self.active_numbers or num2 not in self.active_numbers:
            print(f"ERROR: Invalid numbers used - {num1} or {num2} not in active numbers")
            return
        
        self.active_numbers.append(diff)
        self.active_numbers.sort()
        
        if sorted(self.active_numbers) != sorted(received_numbers):
            print("WARNING: State mismatch after move!")
            print(f"Local: {sorted(self.active_numbers)}")
            print(f"Remote: {sorted(received_numbers)}")
            self.active_numbers = received_numbers.copy()
        
        move_text = f"Player {player}: {num1} - {num2} = {diff}"
        move_history_data = {
            'player': player,
            'num1': num1,
            'num2': num2,
            'diff': diff
        }
        self.move_history.append(move_history_data)
        
        history_label = Gtk.Label(label=move_text)
        history_label.get_style_context().add_class("history_label")
        history_label.get_style_context().add_class(f"player{player}_move")
        history_label.set_halign(Gtk.Align.START)
        self.history_box.pack_start(history_label, False, False, 0)
        self.history_box.show_all()
        self.update_stats()
        
        if self.check_game_over():
            self.handle_game_over()
        else:
            self.current_player = 2 if self.current_player == 1 else 1
            self.update_turn_label()
            
            self.update_board()
            
            if self.current_player == self.my_player_number:
                self._notify_your_turn()
                print(f"DEBUG: It's now our turn (player {self.my_player_number})")
            else:
                print(f"DEBUG: Still opponent's turn (we are player {self.my_player_number}, current is {self.current_player})")
    
    def _notify_your_turn(self):
        """Notify player it's their turn"""
        original_markup = self.turn_label.get_markup()
        
        def flash_on():
            self.turn_label.set_markup("<span background='#4CAF50' foreground='white'><b>  YOUR TURN!  </b></span>")
            GLib.timeout_add(500, flash_off)
            return False
        
        def flash_off():
            self.turn_label.set_markup(original_markup)
            return False
        
        GLib.timeout_add(100, flash_on)

    def update_lobby_status(self, status):
        """Update the lobby status message"""
        self.lobby_status_label.set_text(status)

    def _add_start_button(self):
        """Add start game button for host"""
        if hasattr(self, 'lobby_start_button'):
            return 
        
        self.lobby_start_button = Gtk.Button(label="Start Game")
        self.lobby_start_button.get_style_context().add_class("suggested-action")
        self.lobby_start_button.connect("clicked", self._start_network_game)
        self.lobby_box.pack_start(self.lobby_start_button, False, False, 10)
        self.lobby_box.show_all()

    def _start_network_game(self, widget):
        """Start the network game (host only)"""
        if not self.is_host or not self.opponent_buddy:
            print("ERROR: Cannot start game - not host or no opponent")
            return
        
        if len(self.network_players) != 1:
            print(f"ERROR: Wrong number of players: {len(self.network_players)}")
            return
        
        print("Host starting network game...")
        self.game_started = True
        
        num1 = random.randint(20, 40)
        num2 = random.randint(60, 80)
        
        initial_state = {
            'action': 'game_start',
            'active_numbers': [num1, num2],
            'current_player': 1,
            'host_player': 1,
            'guest_player': 2
        }
        
        if self._collab:
            print(f"Sending initial state: {initial_state}")
            self._collab.post(initial_state)
        
        self._init_network_game(initial_state)
    
    def _init_network_game(self, initial_state):
        """Initialize the network game with given state"""
        print(f"Initializing network game with state: {initial_state}")
        
        self.game_mode = GameMode.NETWORK_MULTIPLAYER
        
        self.active_numbers = initial_state['active_numbers'].copy()
        self.selected_numbers = []
        self.current_player = initial_state['current_player']
        self.game_over = False
        self.winner = None
        self.move_history = []
        
        for child in self.numbers_grid.get_children():
            self.numbers_grid.remove(child)
        
        for child in self.history_box.get_children():
            self.history_box.remove(child)
        
        self.show_game()
        
        self.update_board()
        self.update_turn_label()
        self.update_stats()
        self.update_selection_display()
        
        if self.is_host:
            self._show_game_start_message("You are Player 1 (Red). You start!")
        else:
            self._show_game_start_message("You are Player 2 (Blue). Waiting for Player 1...")
    
    def _show_game_start_message(self, message):
        """Show a temporary message when game starts"""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Game Started!"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def get_game_state_for_sync(self):
        """Get current game state for syncing with joining player"""
        if self.game_mode != GameMode.NETWORK_MULTIPLAYER or not self.game_started:
            return {}
        
        return {
            'game_in_progress': True,
            'active_numbers': self.active_numbers.copy(),
            'current_player': self.current_player,
            'move_history': self.move_history.copy(),
            'host_player': 1,
            'guest_player': 2
        }

    def set_game_state_from_sync(self, data):
        """Set game state when joining a game in progress"""
        if data.get('game_in_progress'):
            print("Joining game in progress...")
            self.game_mode = GameMode.NETWORK_MULTIPLAYER 
            self.is_host = False
            self.my_player_number = 2
            self.game_started = True
            
            self._init_network_game(data)

from gi.repository import GLib

if __name__ == "__main__":
    game = EuclidsGame()
    Gtk.main()