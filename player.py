import random
from abc import ABC, abstractmethod
from enum import Enum

class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    EXPERT = 3

# Player base class
class Player(ABC):
    def __init__(self, name, player_id):
        self.name = name
        self.player_id = player_id
    
    @abstractmethod
    def get_move(self, game_state):
        pass

# Bot players
class Bot(Player):
    def __init__(self, difficulty=Difficulty.MEDIUM):
        self.difficulty = difficulty
        name = f"Bot ({difficulty.name})"
        super().__init__(name, 2)
    
    def get_move(self, game_state):
        if self.difficulty == Difficulty.EASY:
            return self._easy_move(game_state)
        elif self.difficulty == Difficulty.MEDIUM:
            return self._medium_move(game_state)
        else:
            return self._expert_move(game_state)
    
    def _easy_move(self, game_state):
        valid_moves = self._get_valid_moves(game_state)
        if valid_moves:
            return random.choice(valid_moves)
        return None
    
    def _medium_move(self, game_state):
        valid_moves = self._get_valid_moves(game_state)
        if not valid_moves:
            return None
        
        for move in valid_moves:
            temp_numbers = game_state['active_numbers'].copy()
            diff = abs(move[0] - move[1])
            temp_numbers.append(diff)
            
            opponent_moves = self._get_valid_moves({'active_numbers': temp_numbers})
            if not opponent_moves:
                return move
        
        moves_with_diff = [(move, abs(move[0] - move[1])) for move in valid_moves]
        moves_with_diff.sort(key=lambda x: x[1])
        return moves_with_diff[0][0]
    
    def _expert_move(self, game_state):
        valid_moves = self._get_valid_moves(game_state)
        if not valid_moves:
            return None
        
        best_move = None
        best_value = float('-inf')
        
        for move in valid_moves:
            value = self._minimax(game_state, move, depth=4, maximizing=False)
            if value > best_value:
                best_value = value
                best_move = move
        
        return best_move
    
    def _minimax(self, game_state, move, depth, maximizing):
        temp_numbers = game_state['active_numbers'].copy()
        diff = abs(move[0] - move[1])
        temp_numbers.append(diff)
        new_state = {'active_numbers': temp_numbers}
        
        moves = self._get_valid_moves(new_state)
        if not moves or depth == 0:
            return len(moves) if maximizing else -len(moves)
        
        if maximizing:
            max_eval = float('-inf')
            for next_move in moves:
                eval_score = self._minimax(new_state, next_move, depth - 1, False)
                max_eval = max(max_eval, eval_score)
            return max_eval
        else:
            min_eval = float('inf')
            for next_move in moves:
                eval_score = self._minimax(new_state, next_move, depth - 1, True)
                min_eval = min(min_eval, eval_score)
            return min_eval
    
    def _get_valid_moves(self, game_state):
        valid_moves = []
        numbers = game_state['active_numbers']
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                diff = abs(numbers[i] - numbers[j])
                if diff not in numbers:
                    valid_moves.append((numbers[i], numbers[j]))
        return valid_moves