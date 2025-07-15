import time
import math

class Animation:
    def __init__(self, start_pos, end_pos, duration=0.5, easing='ease_out_cubic'):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.duration = duration
        self.start_time = time.time()
        self.active = True
        self.number = None
        self.easing = easing
        self.scale = 1.0
        self.rotation = 0
        self.alpha = 255
    
    def ease_out_cubic(self, t):
        return 1 - (1 - t) ** 3
    
    def ease_in_out_cubic(self, t):
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def ease_bounce(self, t):
        if t < 1/2.75:
            return 7.5625 * t * t
        elif t < 2/2.75:
            return 7.5625 * (t - 1.5/2.75) * (t - 1.5/2.75) + 0.75
        elif t < 2.5/2.75:
            return 7.5625 * (t - 2.25/2.75) * (t - 2.25/2.75) + 0.9375
        else:
            return 7.5625 * (t - 2.625/2.75) * (t - 2.625/2.75) + 0.984375
    
    def update(self):
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        if progress >= 1.0:
            self.active = False
            return self.end_pos
        
        # Apply easing
        if self.easing == 'ease_out_cubic':
            progress = self.ease_out_cubic(progress)
        elif self.easing == 'ease_in_out_cubic':
            progress = self.ease_in_out_cubic(progress)
        elif self.easing == 'ease_bounce':
            progress = self.ease_bounce(progress)
        
        # Update position
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * progress
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * progress
        
        # Update visual effects
        self.scale = 1.0 + 0.5 * math.sin(progress * math.pi)
        self.rotation = progress * 360
        self.alpha = int(255 * (1 - progress * 0.3))
        
        return (x, y)