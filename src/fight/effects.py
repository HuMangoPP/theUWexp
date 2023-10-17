import pygame as pg
import numpy as np


class _Settings:
    EFFECT_LIFETIME = 0.1


class Boom:
    def __init__(self):
        self._setup_state()
    
    def _setup_state(self):
        self.active = False
        self.x, self.y = 0,0
        self.angles = np.zeros(3)
        self.omega = 0
        self.rs = np.zeros(3)
    
    def create_new_particles(
        self,
        x: float, y: float,
        ox: int,
        num_rings: int = 3
    ):
        self.active = True
        self.x, self.y = x, y
        self.omega = np.pi / 4 * ox * 10
        self.angles = -ox * np.arange(num_rings) * 2 * np.pi / num_rings / num_rings 
        self.rs = (np.arange(num_rings) - num_rings + 1) * 100
    
    def animate(self, dt: float):
        self.angles = self.angles + self.omega * dt
        self.rs = self.rs + 1000 * dt
        
    def render(self, effects_display: pg.Surface):
        for r, angle in zip(self.rs, self.angles):
            if r < 200 and r > 0:
                pg.draw.polygon(
                    effects_display,
                    (255,255,255),
                    np.array([self.x, self.y]) + r * np.column_stack([
                        np.cos(np.arange(3) * 2 * np.pi / 3 + angle),
                        np.sin(np.arange(3) * 2 * np.pi / 3 + angle)
                    ]),
                    int(1000 / (1 + r))
                )
        return np.all(self.rs >= 200)


class Sparks:
    def __init__(self):
        self._setup_state()
    
    def _setup_state(self):
        self.pos = np.array([])
        self.vel = np.array([])
        self.lifetime = np.array([])

    def create_new_particles(
        self,
        x: float, y: float,
        ox: float, oy: float,
        num_particles: int = 3
    ):
        new_pos = np.full((num_particles * 2,2), [x,y])
        angles = np.pi / 6 * (np.random.rand(num_particles * 2) * 2 - 1) + np.arctan2(oy, ox)
        new_vel = 1000 * np.column_stack([
            np.cos(angles),
            np.sin(angles)
        ])
        new_vel[num_particles:] = -new_vel[num_particles:]
        new_lifetime = np.full(num_particles * 2, _Settings.EFFECT_LIFETIME)

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
        for pos, vel, lifetime in zip(self.pos, self.vel, self.lifetime):
            perp = np.array([0,0])
            perp[0] = vel[1]
            perp[1] = -vel[0]
            vel_scale = vel / 200 / (lifetime + _Settings.EFFECT_LIFETIME)
            perp_scale = perp / 20 * lifetime
            vertices = vel_scale + np.array([
                pos - vel_scale,
                pos - perp_scale, 
                pos + 2 * vel_scale,
                pos + perp_scale,
            ])
            pg.draw.polygon(
                effects_display,
                (255,255,255),
                vertices
            )
        if self.lifetime.size > 0:
            return True
        return False


class Bolt:
    def __init__(self):
        self._setup_state()
    
    def _setup_state(self):
        self.active = False
        self.pos = np.zeros(2)
        self.vel = np.zeros(2)
        self.angle = 0
        self.lifetime = 1
        self.move_forward = False
    
    def create_new_particles(
        self,
        x: float, y: float,
        ox: float, oy: float,
    ):
        self.active = True
        self.pos = np.array([x,y])
        self.angle = np.arctan2(oy, ox) + np.pi / 12 * (np.random.rand() * 2 - 1)
        self.vel = 3000 * np.array([
            np.cos(self.angle),
            np.sin(self.angle)
        ])
        self.move_forward = True
        self.lifetime = _Settings.EFFECT_LIFETIME

    def animate(self, dt: float):
        if not self.active:
            return
        self.lifetime -= dt
        if self.lifetime < _Settings.EFFECT_LIFETIME / 2:
            self.move_forward = False
        if self.lifetime < 0:
            self.active = False
        
        if self.move_forward:
            self.pos = self.pos + self.vel * dt
        else:
            self.pos = self.pos - self.vel * dt
    
    def render(self, effects_display: pg.Surface):
        if self.active:
            long = 50 / (self.lifetime + _Settings.EFFECT_LIFETIME) * np.array([np.cos(self.angle), np.sin(self.angle)])
            short = 3 * np.array([np.cos(self.angle + np.pi / 2), np.sin(self.angle + np.pi / 2)])
            points = np.array([
                self.pos - long,
                self.pos - short,
                self.pos + long,
                self.pos + short,
            ])
            pg.draw.polygon(
                effects_display,
                (255,255,255),
                points
            )
            return True
        return False


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