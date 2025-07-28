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
            # Random move
            return random.choice(valid_moves)
        elif self.difficulty == Difficulty.MEDIUM:
            # Prefer moves that create smaller differences
            valid_moves.sort(key=lambda x: abs(x[0] - x[1]))
            return valid_moves[0]
        else:  # EXPERT
            # Try to minimize opponent's options
            best_move = None
            min_opponent_moves = float('inf')
            
            for move in valid_moves:
                # Simulate this move
                temp_numbers = active_numbers.copy()
                diff = abs(move[0] - move[1])
                temp_numbers.append(diff)
                
                # Count opponent's possible moves
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
        
        # Game state
        self.game_mode = GameMode.VS_BOT
        self.difficulty = Difficulty.MEDIUM
        self.bot = Bot(self.difficulty)
        self.active_numbers = []
        self.selected_numbers = []
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []
        
        # UI setup
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
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _build_ui(self):
        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_box)
        
        # Menu container
        self.menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.menu_box.set_name("menu_box")
        self.menu_box.set_halign(Gtk.Align.CENTER)
        self.menu_box.set_valign(Gtk.Align.CENTER)
        
        # Game container
        self.game_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.game_box.set_name("game_box")
        
        # Build menu
        self._build_menu()
        
        # Build game UI
        self._build_game_ui()
    
    def _build_menu(self):
        # Title
        title = Gtk.Label(label="Euclid's Game")
        title.get_style_context().add_class("info_label")
        self.menu_box.pack_start(title, False, False, 0)
        
        # Game mode selection
        mode_label = Gtk.Label(label="Select Game Mode:")
        self.menu_box.pack_start(mode_label, False, False, 0)
        
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.vs_bot_radio = Gtk.RadioButton.new_with_label(None, "VS Bot")
        self.vs_human_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.vs_bot_radio, "VS Human"
        )
        mode_box.pack_start(self.vs_bot_radio, False, False, 0)
        mode_box.pack_start(self.vs_human_radio, False, False, 0)
        self.menu_box.pack_start(mode_box, False, False, 0)
        
        # Difficulty selection
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
        
        # Start button
        start_button = Gtk.Button(label="Start Game")
        start_button.connect("clicked", self.on_start_game)
        self.menu_box.pack_start(start_button, False, False, 20)
        
        # Connect radio button signals
        self.vs_bot_radio.connect("toggled", self.on_mode_changed)
    
    def _build_game_ui(self):
        # Header with turn info
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_homogeneous(True)
        
        self.turn_label = Gtk.Label()
        self.turn_label.get_style_context().add_class("turn_label")
        
        back_button = Gtk.Button(label="Back to Menu")
        back_button.connect("clicked", lambda w: self.show_menu())
        
        header_box.pack_start(back_button, False, False, 0)
        header_box.pack_start(self.turn_label, True, True, 0)
        header_box.pack_start(Gtk.Box(), False, False, 0)  # Spacer
        
        self.game_box.pack_start(header_box, False, False, 0)
        
        # Main game area
        game_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.game_box.pack_start(game_paned, True, True, 0)
        
        # Left side - Number board
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        board_label = Gtk.Label(label="Number Board")
        board_label.get_style_context().add_class("info_label")
        left_box.pack_start(board_label, False, False, 0)
        
        # Scrolled window for numbers
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_width(400)
        
        self.numbers_grid = Gtk.FlowBox()
        self.numbers_grid.set_valign(Gtk.Align.START)
        self.numbers_grid.set_max_children_per_line(10)
        self.numbers_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.numbers_grid)
        
        left_box.pack_start(scrolled, True, True, 0)
        
        # Selection display
        self.selection_label = Gtk.Label()
        self.selection_label.set_markup("<b>Selection:</b> None")
        left_box.pack_start(self.selection_label, False, False, 0)
        
        self.calculation_label = Gtk.Label()
        left_box.pack_start(self.calculation_label, False, False, 0)
        
        # Right side - Game info
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_box.set_margin_left(10)
        
        info_label = Gtk.Label(label="Game Info")
        info_label.get_style_context().add_class("info_label")
        right_box.pack_start(info_label, False, False, 0)
        
        # Stats
        self.stats_label = Gtk.Label()
        self.stats_label.set_halign(Gtk.Align.START)
        right_box.pack_start(self.stats_label, False, False, 0)
        
        # Move history
        history_label = Gtk.Label(label="Move History:")
        history_label.set_halign(Gtk.Align.START)
        right_box.pack_start(history_label, False, False, 0)
        
        history_scrolled = Gtk.ScrolledWindow()
        history_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        history_scrolled.set_min_content_height(200)
        
        self.history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        history_scrolled.add(self.history_box)
        right_box.pack_start(history_scrolled, True, True, 0)
        
        # Add to paned
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
        self.main_box.show_all()
    
    def on_mode_changed(self, widget):
        if self.vs_bot_radio.get_active():
            self.difficulty_box.show()
        else:
            self.difficulty_box.hide()
    
    def on_start_game(self, widget):
        # Set game mode
        if self.vs_bot_radio.get_active():
            self.game_mode = GameMode.VS_BOT
            # Set difficulty
            if self.easy_radio.get_active():
                self.difficulty = Difficulty.EASY
            elif self.medium_radio.get_active():
                self.difficulty = Difficulty.MEDIUM
            else:
                self.difficulty = Difficulty.EXPERT
            self.bot = Bot(self.difficulty)
        else:
            self.game_mode = GameMode.LOCAL_MULTIPLAYER
        
        self.reset_game()
        self.show_game()
    
    def reset_game(self):
        self.active_numbers = []
        self.selected_numbers = []
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []
        
        # Clear UI
        for child in self.numbers_grid.get_children():
            self.numbers_grid.remove(child)
        
        for child in self.history_box.get_children():
            self.history_box.remove(child)
        
        # Add initial numbers
        num1 = random.randint(20, 40)
        num2 = random.randint(60, 80)
        self.active_numbers = [num1, num2]
        
        self.update_board()
        self.update_turn_label()
        self.update_stats()
    
    def update_board(self):
        # Clear the board
        for child in self.numbers_grid.get_children():
            self.numbers_grid.remove(child)
        
        # Add number buttons
        for i in range(1, 101):
            if i in self.active_numbers:
                button = Gtk.Button(label=str(i))
                button.get_style_context().add_class("number_button")
                button.get_style_context().add_class("number_button_active")
                
                if i in self.selected_numbers:
                    button.get_style_context().add_class("number_button_selected")
                
                button.connect("clicked", self.on_number_clicked, i)
                self.numbers_grid.add(button)
        
        self.numbers_grid.show_all()
    
    def on_number_clicked(self, button, number):
        if self.game_over:
            return
        
        if self.current_player == 2 and self.game_mode == GameMode.VS_BOT:
            return  # Don't allow clicks during bot's turn
        
        if number in self.selected_numbers:
            self.selected_numbers.remove(number)
        else:
            if len(self.selected_numbers) < 2:
                self.selected_numbers.append(number)
        
        self.update_board()
        self.update_selection_display()
        
        # Make move if 2 numbers selected
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
            # Invalid move
            self.selected_numbers = []
            self.update_board()
            self.update_selection_display()
            return False
        
        # Valid move
        self.active_numbers.append(diff)
        self.active_numbers.sort()
        
        # Add to history
        move_text = f"Player {self.current_player}: {num1} - {num2} = {diff}"
        self.move_history.append({
            'player': self.current_player,
            'num1': num1,
            'num2': num2,
            'diff': diff
        })
        
        history_label = Gtk.Label(label=move_text)
        history_label.get_style_context().add_class("history_label")
        history_label.set_halign(Gtk.Align.START)
        self.history_box.pack_start(history_label, False, False, 0)
        self.history_box.show_all()
        
        self.selected_numbers = []
        self.update_board()
        self.update_selection_display()
        self.update_stats()
        
        # Check for game over
        if self.check_game_over():
            self.handle_game_over()
        else:
            # Switch player
            self.current_player = 2 if self.current_player == 1 else 1
            self.update_turn_label()
            
            # Bot move
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
        # Check if any valid moves exist
        for i in range(len(self.active_numbers)):
            for j in range(i + 1, len(self.active_numbers)):
                diff = abs(self.active_numbers[i] - self.active_numbers[j])
                if diff not in self.active_numbers:
                    return False
        return True
    
    def handle_game_over(self):
        self.game_over = True
        self.winner = 2 if self.current_player == 1 else 1
        
        # Show game over dialog
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
        else:
            message = f"Player {self.winner} wins!"
        
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        
        # Return to menu
        self.show_menu()
    
    def update_turn_label(self):
        if self.game_mode == GameMode.VS_BOT:
            if self.current_player == 1:
                self.turn_label.set_markup("<b>Your Turn</b>")
            else:
                self.turn_label.set_markup("<b>Bot's Turn</b>")
        else:
            self.turn_label.set_markup(f"<b>Player {self.current_player}'s Turn</b>")
    
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
        
        # Test each field individually
        try:
            state['game_mode'] = self.game_mode.value
            json.dumps({'test': state['game_mode']})  # Test if serializable
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
            # Check if Theme.LIGHT exists and is comparable
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
            # Load game mode
            try:
                game_mode_value = state.get('game_mode', GameMode.VS_BOT.value)
                print(f"DEBUG: Loading game_mode = {game_mode_value}")
                self.game_mode = GameMode(game_mode_value)
                print(f"DEBUG: Game mode set to: {self.game_mode}")
            except Exception as e:
                print(f"ERROR: Failed to load game_mode: {e}")
                self.game_mode = GameMode.VS_BOT
            
            # Load difficulty
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
            
            # Load active numbers
            try:
                self.active_numbers = state.get('active_numbers', [])
                print(f"DEBUG: Loaded {len(self.active_numbers)} active numbers: {self.active_numbers}")
            except Exception as e:
                print(f"ERROR: Failed to load active_numbers: {e}")
                self.active_numbers = []
            
            # Load selected numbers
            try:
                self.selected_numbers = state.get('selected_numbers', [])
                print(f"DEBUG: Loaded {len(self.selected_numbers)} selected numbers: {self.selected_numbers}")
            except Exception as e:
                print(f"ERROR: Failed to load selected_numbers: {e}")
                self.selected_numbers = []
            
            # Load current player
            try:
                self.current_player = state.get('current_player', 1)
                print(f"DEBUG: Current player = {self.current_player}")
            except Exception as e:
                print(f"ERROR: Failed to load current_player: {e}")
                self.current_player = 1
            
            # Load game over status
            try:
                self.game_over = state.get('game_over', False)
                print(f"DEBUG: Game over = {self.game_over}")
            except Exception as e:
                print(f"ERROR: Failed to load game_over: {e}")
                self.game_over = False
            
            # Load winner
            try:
                self.winner = state.get('winner', None)
                print(f"DEBUG: Winner = {self.winner}")
            except Exception as e:
                print(f"ERROR: Failed to load winner: {e}")
                self.winner = None
            
            # Load move history
            try:
                self.move_history = state.get('move_history', [])
                print(f"DEBUG: Loaded {len(self.move_history)} moves in history")
                if self.move_history:
                    print(f"DEBUG: Last move: {self.move_history[-1]}")
            except Exception as e:
                print(f"ERROR: Failed to load move_history: {e}")
                self.move_history = []
            
            # Load show menu
            try:
                self.show_menu = state.get('show_menu', True)
                print(f"DEBUG: Show menu = {self.show_menu}")
            except Exception as e:
                print(f"ERROR: Failed to load show_menu: {e}")
                self.show_menu = True
            
            # Load theme
            try:
                theme_name = state.get('theme', 'LIGHT')
                print(f"DEBUG: Loading theme = {theme_name}")
                # Uncomment when Theme is properly defined
                # self.theme = Theme.DARK if theme_name == 'DARK' else Theme.LIGHT
            except Exception as e:
                print(f"ERROR: Failed to load theme: {e}")
            
            # Update UI if game is in progress
            if not self.show_menu and self.active_numbers:
                print("DEBUG: Game in progress, updating UI")
                self.game_start_time = time.time()
                # Reset some UI elements
                self.animations = []
                self.particles = []
                self.hover_effects = {}
                self.bot_thinking = False
                
                # If we have an active game, make sure we're not stuck
                if self.current_player == 2 and self.game_mode == GameMode.VS_BOT and not self.game_over:
                    print("DEBUG: It's bot's turn after loading")
            
            print("DEBUG: load_state completed successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Fatal error in load_state: {e}")
            import traceback
            traceback.print_exc()
            return False

# For GTK timeout
from gi.repository import GLib

if __name__ == "__main__":
    game = EuclidsGame()
    Gtk.main()