import pygame as pg
import numpy as np

from ..util import lerp


class _Settings:
    EFFECT_LIFETIME = 0.1


class Boom:
    def __init__(self):
        # data arrays
        self.lifetime = np.zeros(0)
        self.pos = np.zeros((0,2))
    
    def create_vfx(self, pos: np.ndarray):
        # new data arrays
        new_lifetime = np.full(pos.shape[0], _Settings.EFFECT_LIFETIME)

        # append
        if self.pos.size == 0:
            self.lifetime = new_lifetime
            self.pos = pos
        else:
            self.lifetime = np.hstack([self.lifetime, new_lifetime])
            self.pos = np.vstack([self.pos, pos])
    
    def animate(self, dt: float):
        if self.lifetime.size == 0:
            return

        # destroy vfx 
        self.lifetime = self.lifetime - dt
        alive = self.lifetime > 0
        self.lifetime = self.lifetime[alive]
        self.pos = self.pos[alive]
        
    def render(self, gaussian_blur: pg.Surface):
        if self.lifetime.size == 0:
            return

        for lifetime, pos in zip(self.lifetime, self.pos):
            r = lerp(150, 0, lifetime / _Settings.EFFECT_LIFETIME)
            rect = pg.Rect(0, 0, r / 2, r)
            rect.center = pos
            pg.draw.ellipse(gaussian_blur, (255, 255, 255), rect, 10)


class Sparks:
    def __init__(self):
        # data arrays
        self.lifetime = np.array([])
        self.pos = np.array([])
        self.angle = np.array([])

    def create_vfx(self, pos: tuple, angle: float, num_particles: int = 2):
        # create new data arrays
        num_sparks = 2 * num_particles + 1
        new_lifetime = np.full(num_sparks, _Settings.EFFECT_LIFETIME)
        new_pos = np.full((num_sparks,2), pos)
        new_angle = np.pi / 3 * (np.random.rand(num_sparks) * 2 - 1) + angle

        # append
        if self.lifetime.size == 0:
            self.lifetime = new_lifetime
            self.pos = new_pos
            self.angle = new_angle
        else:
            self.lifetime = np.hstack([self.lifetime, new_lifetime])
            self.pos = np.vstack([self.pos, new_pos])
            self.angle = np.hstack([self.angle, new_angle])

    def animate(self, dt: float):
        if self.lifetime.size == 0:
            return
        # move the sparks
        vel = 1000 * np.column_stack([np.sin(self.angle), np.cos(self.angle)])
        self.pos = self.pos + vel * dt

        # delete sparks that have exceeded their lifetime
        self.lifetime = self.lifetime - dt
        alive = self.lifetime > 0
        self.lifetime = self.lifetime[alive]
        self.pos = self.pos[alive]
        self.angle = self.angle[alive]
    
    def render(self, gaussian_blur: pg.Surface):
        for pos, angle, lifetime in zip(self.pos, self.angle, self.lifetime):
            # render a diamond shaped spark
            scale = lerp(np.zeros(4), np.array([100, 10, 100, 10]), lifetime / _Settings.EFFECT_LIFETIME)
            vertices = pos + scale.reshape(-1,1) * np.array([
                [np.sin(angle), np.cos(angle)],
                [np.sin(angle + np.pi / 2), np.cos(angle + np.pi / 2)],
                [np.sin(angle + np.pi), np.cos(angle + np.pi)],
                [np.sin(angle - np.pi / 2), np.cos(angle - np.pi / 2)]
            ])
            pg.draw.polygon(gaussian_blur, (255,255,255), vertices)


class Bolt:
    def __init__(self):
        # data arrays
        self.lifetime = np.zeros(0)
        self.pos = np.zeros((0,2))
        self.angle = np.zeros(0)
    
    def create_vfx(self, pos: np.ndarray, angle: float):
        # append
        if self.lifetime.size == 0:
            self.lifetime = np.full(1, _Settings.EFFECT_LIFETIME)
            self.pos = np.array([pos])
            self.angle = np.full(1, angle + np.pi / 6 * (2 * np.random.rand() - 1))
        else:
            self.lifetime = np.hstack([self.lifetime, _Settings.EFFECT_LIFETIME])
            self.pos = np.vstack([self.pos, pos])
            self.angle = np.hstack([self.angle, angle + np.pi / 6 * (2 * np.random.rand() - 1)])

    def animate(self, dt: float):
        if self.lifetime.size == 0:
            return
        
        # move bolt
        vel = 100 * np.column_stack([np.sin(self.angle), np.cos(self.angle)])
        self.pos = self.pos + vel * dt

        # destroy vfx
        self.lifetime = self.lifetime - dt
        alive = self.lifetime > 0
        self.lifetime = self.lifetime[alive]
        self.pos = self.pos[alive]
        self.angle = self.angle[alive]
    
    def render(self, gaussian_blur: pg.Surface):
        for pos, angle, lifetime in zip(self.pos, self.angle, self.lifetime):
            scale = np.array([500, 20, 500, 20]) * lerp(1 / 5, 1, lifetime / _Settings.EFFECT_LIFETIME)
            vertices = pos + scale.reshape(-1,1) * np.array([
                [np.sin(angle), np.cos(angle)],
                [np.sin(angle + np.pi / 2), np.cos(angle + np.pi / 2)],
                [np.sin(angle + np.pi), np.cos(angle + np.pi)],
                [np.sin(angle - np.pi / 2), np.cos(angle - np.pi / 2)]
            ])
            pg.draw.polygon(gaussian_blur, (255, 255, 255), vertices)


class DustCloud:
    def __init__(self):
        self._setup_state()
    
    def _setup_state(self):
        self.pos = np.array([])
        self.vel = np.array([])
        self.lifetime = np.array([])
    
    def create_new_particles(
        self,
        x: float, y: float, ox: float,
        num_clouds: int = 5
    ):
        new_pos = np.full((num_clouds * 2,2), [x,y])
        new_vel = np.array([
            *np.column_stack([
                400 * (np.random.rand(num_clouds) * 2 - 1),
                -50 * (np.random.rand(num_clouds))
            ]),
            *np.column_stack([
                250 * np.full(num_clouds, ox / 2) + 50 * (np.random.rand(num_clouds) * 2 - 1),
                -200 * np.ones(num_clouds)
            ])
        ])
        new_lifetime = np.full(num_clouds * 2, _Settings.EFFECT_LIFETIME * 2)

        self.pos = np.array([*self.pos, *new_pos])
        self.vel = np.array([*self.vel, *new_vel])
        self.lifetime = np.array([*self.lifetime, *new_lifetime])
    
    def animate(self, dt: float):
        self.lifetime = self.lifetime - dt
        mask = self.lifetime > 0

        self.pos = self.pos[mask]
        self.vel = self.vel[mask]
        self.lifetime = self.lifetime[mask]

        self.pos = self.pos + self.vel * dt

    def render(self, effects_display: pg.Surface):
        [pg.draw.circle(effects_display, (50,50,50), pos, lifetime * 100)
            for pos, lifetime in zip(self.pos, self.lifetime)]
        if self.lifetime.size > 0:
            return True
        return False