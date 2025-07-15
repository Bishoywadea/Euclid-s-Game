import pygame as pg
class Particle:
    def __init__(self, x, y, color, velocity, size=3, lifetime=1.0):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alpha = 255
    
    def update(self, dt):
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        self.lifetime -= dt
        self.alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        return self.lifetime > 0
    
    def draw(self, surface):
        if self.alpha > 0:
            color = (*self.color[:3], self.alpha)
            temp_surface = pg.Surface((self.size * 2, self.size * 2), pg.SRCALPHA)
            pg.draw.circle(temp_surface, color, (self.size, self.size), self.size)
            surface.blit(temp_surface, (self.x - self.size, self.y - self.size))