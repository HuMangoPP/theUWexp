import pygame as pg
import numpy as np
import os
import json


class _Settings:
    GROUND_LEVEL = 600
    
    ANIMATION_SPEED = 12
    FADE_SPEED = 4

    CHARACTER_COLOURS = {
        'math': (255, 61, 187),
        'eng': (190, 39, 245),
        'env': (0, 219, 88),
        'art': (255, 128, 0),
        'sci': (31, 98, 255),
        'ahs': (46, 255, 224),
    }

    X_SPD = 300
    JUMP_SPEED = -400
    DASH_SPEED = 1000
    DASH_SLOW = 1250
    SQUASH_SPEED = 5
    XACC = 1500
    YACC = 980
    KBACC = 500

    EFFECT_LIFETIME = 0.1
    
    DAMAGE = {}
    with open('./assets/attacks/damages.json', 'r') as f:
        DAMAGE = json.load(f)

    KNOCKBACK = {}
    with open('./assets/attacks/knockbacks.json', 'r') as f:
        KNOCKBACK = json.load(f)


class Boom:
    def __init__(self):
        self._setup_state()
        self._setup_animation()
    
    def _setup_state(self):
        self.active = False
        self.orientation = 0
    
    def _setup_animation(self):
        self.x, self.y = 0, 0
        self.r = 0
        self.thickness = 100
    
    def create_new_particles(
        self,
        x: float, y: float,
        orientation: int
    ):
        self.active = True
        self.orientation = orientation

        self.x, self.y = x, y
        self.r = 0
        self.thickness = 100
    
    def animate(self, dt: float):
        if self.active:
            self.r += dt * 500
            self.thickness -= dt * 500
            if self.thickness <= 0:
                self.active = False
    
    def render(self, effects_display: pg.Surface):
        if self.active:
            pg.draw.circle(
                effects_display,
                (255,255,255),
                (self.x,self.y),
                self.r,
                int(np.ceil(self.thickness))
            )
            return True
        return False


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


class Cut:
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


class Attack:
    def __init__(self, fighter):
        self.fighter = fighter
        self._setup_state()
        self._setup_animation()
    
    def _setup_state(self):
        self.active = False
        self.dangerous = False
       
    def _setup_animation(self): 
        self.x, self.y = 0, 0
        self.sprite = None
        self.drawbox = None

        self.attack_type = None
        self.alt_attack = 0
        self.phase = None

        self.frames_elapsed = 0
        self.startup_frames = 0
        self.active_frames = 0
        self.recovery_frames = 0

        self.animation_index = 0

        self.particles = {
            'sparks': Sparks(),
            'cut': Cut()
        }
    
    def create_new_attack(
        self, 
        attack_type: str,
        x: float, y: float,
    ):
        self.active = True
        self.dangerous = True
        self.x, self.y = x, y

        self.attack_type = attack_type
        # self.phase = 'startup'
        # self.startup_frames = _Settings.ATTACK_FRAMES[self.attack_type]['startup']
        # self.active_frames = _Settings.ATTACK_FRAMES[self.attack_type]['active']
        # self.recovery_frames = _Settings.ATTACK_FRAMES[self.attack_type]['recovery']
        # self.alt_attack = (self.alt_attack + 1) % 2

        self.frames_elapsed = 0
        self.animation_index = 0

    def check_hit(self, fighter):
        orientation = 1 if self.fighter.facing == 'right' else -1
        if (
            self.dangerous and
            self.active
        ):
            overlap = pg.mask.from_surface(self.sprite).overlap(
                pg.mask.from_surface(fighter.sprite),
                np.array(fighter.drawbox.topleft) - np.array(self.drawbox.topleft)
            )
            if overlap is not None:
                self.particles['sparks'].create_new_particles(*fighter.drawbox.center, 0, -1)
                self.particles['cut'].create_new_particles(*fighter.drawbox.center, orientation, 0)
                kb = _Settings.KNOCKBACK[self.fighter.fighter_type][self.attack_type]
                fighter.knockback(2 * orientation * kb, - kb)
                fighter.gpa -= _Settings.DAMAGE[self.fighter.fighter_type][self.attack_type]
                self.dangerous = False
                return True
        
        return False

    def animate(
        self, 
        attack_assets: dict,
        dt: float
    ):
        if self.active:
            # self.frames_elapsed += dt * _Settings.ANIMATION_SPEED
            # if self.phase == 'startup':
            #     if self.frames_elapsed >= self.startup_frames:
            #         self.frames_elapsed = 0
            #         self.animation_index = 0
            #         self.phase = 'active'
            # elif self.phase == 'active':
            #     if self.frames_elapsed >= self.active_frames:
            #         self.phase = 'recovery'
            #         self.frames_elapsed = 0
            #         self.animation_index = 0
            # else:
            #     if self.frames_elapsed >= self.recovery_frames:
            #         self.active = False
            #         self.sprite = None
            #         self.drawbox = None
            #         self.attack_type = None
            #         return
                    

            self.animation_index += dt * _Settings.ANIMATION_SPEED
            animation_length = len(attack_assets[self.fighter.fighter_type][self.attack_type][self.fighter.facing])
            if self.animation_index >= animation_length:
                self.animation_index = 0
                self.active = False
            
            if self.active:
                self.sprite = attack_assets[self.fighter.fighter_type][self.attack_type][self.fighter.facing][int(self.animation_index)]
                self.drawbox = self.sprite.get_rect()
                self._update_drawbox()
            else:
                self.sprite = None

        [particle.animate(dt) for particle in self.particles.values()]

    def _update_drawbox(self):
        self.drawbox.center = (self.x, self.y)
    
    def render(self, default_display: pg.Surface, effects_display: pg.Surface):
        if self.sprite is not None:
            default_display.blit(
                self.sprite,
                self.drawbox
            )
        
        return np.any([particle.render(effects_display) for particle in self.particles.values()])


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
                -100 * np.ones(num_clouds)
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
        [
            pg.draw.circle(effects_display, (50,50,50), pos, lifetime * 100)
            for pos, lifetime in zip(self.pos, self.lifetime)
        ]
        if self.lifetime.size > 0:
            return True
        return False


class MovementParticles:
    def __init__(self):
        self._setup_state()
        self._setup_animation()
    
    def _setup_state(self):
        self.active = False
        self.orientation = 0
    
    def _setup_animation(self):
        self.x, self.y = 0, 0
        self.sprite = None
        self.drawbox = None

        self.effect_type = None
        self.phase = None
        self.animation_index = 0
        self.animation_done = False
        self.alpha = 1
    
    def create_new_particles(
        self, 
        effect_type: str,
        x: float, y: float,
        orientation: int
    ):
        self.active = True
        self.orientation = orientation
        self.effect_type = effect_type

        self.x, self.y = x, y

        self.phase = 'active'
        self.animation_index = 0
        self.animation_done = False
        self.alpha = 1

        self.sprite = None
        self.drawbox = None
    
    def animate(
        self,
        effect_assets: dict,
        dt: float,
    ):
        if self.active:
            self.animation_index += dt * _Settings.ANIMATION_SPEED

            animation_length = len(effect_assets[self.effect_type][self.phase][self.orientation])
            if self.phase == 'active':
                if self.animation_index >= animation_length:
                    self.phase = 'fade'
                    self.animation_index = 0
            
            elif self.phase == 'fade':
                self.alpha -= dt * _Settings.FADE_SPEED
                if self.animation_index >= animation_length:
                    self.animation_index = animation_length - 1
                if self.alpha <= 0:
                    self.animation_done = True
            
            if self.animation_done:
                self.active = False
                self.sprite = None
                self.drawbox = None
            else:
                self.sprite = effect_assets[self.effect_type][self.phase][self.orientation][int(self.animation_index)]
                if self.drawbox is None:
                    self.drawbox = self.sprite.get_rect()
                    self.drawbox.centerx = self.x
                    self.drawbox.bottom = self.y

    def render(self, default_display: pg.Surface):
        if self.sprite is not None:
            self.sprite.set_alpha(self.alpha * 255)
            default_display.blit(self.sprite, self.drawbox)


class Accessory:
    def __init__(self, fighter):
        self.fighter = fighter
        self._setup_state()
        self._setup_animation()
    
    def _setup_state(self):
        self.x = 0
        self.y = 0
        self.xvel = 0
        self.yvel = 0

    def _setup_animation(self):
        self.sprite = None
        self.drawbox = None

    def animate(self, accessory_assets: dict, dt: float):
        dx = self.fighter.x - self.x
        dy = self.fighter.y - self.y
        self.xvel = dx
        self.yvel = dy

        self.x += (self.xvel * dt)
        self.y += (self.yvel * dt)

        self.sprite = accessory_assets.get(self.fighter.fighter_type, {
            'right': None,
            'left': None
        })[self.fighter.facing]
        if self.sprite is not None:
            self.drawbox = self.sprite.get_rect()
            self.drawbox.centerx = self.x
            self.drawbox.bottom = self.y

    def render(self, default_display: pg.Surface):
        if self.sprite is not None:
            default_display.blit(self.sprite, self.drawbox)


class Fighter:
    def __init__(self):
        self._setup_state()
        self._setup_animation()
        self._setup_input()

    def _setup_state(self):
        self.fighter_type = 'stats'

        self.x = 500
        self.y = 500
        self.xvel = 0
        self.yvel = 0
        self.kbx = 0
        self.kby = 0

        self.gpa = 4.0

        self.attack = Attack(self)

    def _setup_animation(self):
        self.sprite = None
        self.drawbox = None

        self.action = 'idle'
        self.facing = 'right'

        self.dashing = False

        self.accessory = Accessory(self)

        self.jump_particles = DustCloud()
        self.dash_particles = {
            'boom': Boom(),
            'cut': Cut()
        }
        self.hit_particles = Sparks()

    def _setup_input(self):
        self.movement_inputs = []
        self.direction_inputs = []
        self.attack_input = None

    def _change_animation(self, action, hard_reset: bool = False):
        if self.action != action or hard_reset:
            self.animation_index = 0
        self.action = action

    def knockback(self, kbx: float, kby: float):
        orientation = 1 if kbx > 0 else -1
        self.kbx = kbx
        self.kby = kby

        # self.hit_particles.create_new_particles(*self.drawbox.center, -orientation, 1)

    def animate(
        self, 
        character_assets: dict,
        accessory_assets: dict,
        attack_assets: dict,
        dt: float
    ):
        if self.attack.active:
            if 'honk' not in self.action:
                self._change_animation(f'honk_startup')
        elif 'honk' in self.action:
            self._change_animation(f'honk_recovery')
        elif self.dashing:
            self._change_animation('dash')
        elif self.y < _Settings.GROUND_LEVEL:
            if self.yvel < 0:
                self._change_animation('jump')
            else:
                self._change_animation('fall')
        elif self.xvel:
            self._change_animation('walk')
        else:
            self._change_animation('idle')
        
        self.animation_index += dt * _Settings.ANIMATION_SPEED
        animation_length = len(character_assets.get(self.fighter_type, character_assets['basic'])[self.action][self.facing])
        if self.animation_index >= animation_length:
            self.animation_index = 0
            if self.action in ['jump', 'fall', 'hit', 'dash']:
                self.animation_index = animation_length - 1
            if self.action in ['honk_startup']:
                self._change_animation('honk_active')
            if self.action in ['honk_recovery']:
                self._change_animation('idle')

        self.sprite = character_assets.get(self.fighter_type, character_assets['basic'])[self.action][self.facing][int(self.animation_index)]
        self.drawbox = self.sprite.get_rect()
        self.drawbox.centerx = self.x
        self.drawbox.bottom = self.y

        self.accessory.animate(accessory_assets, dt)
        
        self.attack.animate(attack_assets, dt)
        
        self.jump_particles.animate(dt)
        [particles.animate(dt) for particles in self.dash_particles.values()]
        self.hit_particles.animate(dt)

    def input(self, keybinds: dict, events: list[pg.Event]):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == keybinds['right']:
                    self.movement_inputs.append('right')
                    self.direction_inputs.append('right')
                if event.key == keybinds['left']:
                    self.movement_inputs.append('left') 
                    self.direction_inputs.append('left')
                if event.key == keybinds['up']:
                    self.direction_inputs.append('up')
                
                if event.key == keybinds['jump'] and self.y >= _Settings.GROUND_LEVEL:
                    self.yvel = _Settings.JUMP_SPEED
                    self.jump_particles.create_new_particles(self.x, self.y, 1 if self.facing == 'right' else 0)
                
                if event.key == keybinds['dash']:
                    orientation = 1 if self.facing == 'right' else -1
                    self.dashing = True
                    self.xvel = _Settings.DASH_SPEED * orientation
                    if 'up' in self.direction_inputs:
                        self.yvel = -_Settings.DASH_SPEED / 2
                        self.xvel = self.xvel * np.sqrt(3) / 2

                    self.dash_particles['boom'].create_new_particles(
                        *self.drawbox.center,
                        1 if self.facing == 'right' else 0
                    )
                    self.dash_particles['cut'].create_new_particles(*self.drawbox.center, orientation, 0)
                
                for keybind in ['light', 'spec']:
                    if event.key == keybinds[keybind]:
                        self.attack_input = keybind
            
            if event.type == pg.KEYUP:
                if event.key == keybinds['right']:
                    self.movement_inputs = [movement_input for movement_input in self.movement_inputs if movement_input != 'right']
                    self.direction_inputs = [direction_input for direction_input in self.direction_inputs if direction_input != 'right']
                if event.key == keybinds['left']:
                    self.movement_inputs = [movement_input for movement_input in self.movement_inputs if movement_input != 'left']
                    self.direction_inputs = [direction_input for direction_input in self.direction_inputs if direction_input != 'left']
                if event.key == keybinds['up']:
                    self.movement_inputs = [movement_input for movement_input in self.movement_inputs if movement_input != 'up']
                    self.direction_inputs = [direction_input for direction_input in self.direction_inputs if direction_input != 'up']

    def update(self, dt: float):
        if self.attack_input is not None:
            if not self.attack.active:
                if self.accessory.drawbox is not None:
                    x, y = self.accessory.drawbox.center
                else:
                    x, y = self.drawbox.center
                if len(self.direction_inputs) == 0:
                    attack_type = 'n'
                elif 'up' in self.direction_inputs:
                    attack_type = 'n'
                else:
                    attack_type = 's'
                self.attack.create_new_attack(
                    f'{attack_type}{self.attack_input}',
                    x, y
                )
            self.attack_input = None
        
        if self.dashing:
            orientation = 1 if self.facing == 'right' else -1
            self.xvel -= _Settings.DASH_SLOW * dt * orientation
            if orientation > 0 and self.xvel <= _Settings.X_SPD:
                self.dashing = False
            elif orientation < 0 and self.xvel >= -_Settings.X_SPD:
                self.dashing = False
        elif self.movement_inputs:
            if self.movement_inputs[-1] == 'right':
                if (
                    not self.attack.active and 
                    self.y >= _Settings.GROUND_LEVEL and
                    not self.dashing
                ):
                    self.facing = 'right'
                self.xvel = np.minimum(
                    self.xvel + _Settings.XACC * dt,
                    _Settings.X_SPD
                )
            else:
                if (
                    not self.attack.active and 
                    self.y >= _Settings.GROUND_LEVEL and
                    not self.dashing
                ):
                    self.facing = 'left'
                self.xvel = np.maximum(
                    self.xvel - _Settings.XACC * dt,
                    -_Settings.X_SPD
                )
        else:
            if self.xvel > 0:
                self.xvel -= _Settings.XACC * dt
                if self.xvel < 0:
                    self.xvel = 0
            else:
                self.xvel += _Settings.XACC * dt
                if self.xvel > 0:
                    self.xvel = 0

        if not self.attack.active:
            self.x += self.xvel * dt
            self.y += self.yvel * dt
            if self.y >= _Settings.GROUND_LEVEL:
                self.y = _Settings.GROUND_LEVEL
                self.yvel = 0
            else:
                self.yvel += _Settings.YACC * dt
        
        self.x += self.kbx * dt
        self.y += self.kby * dt

        if self.kbx > 0:
            self.kbx -= _Settings.KBACC * dt
            if self.kbx < 0:
                self.kbx = 0
        elif self.kbx < 0:
            self.kbx += _Settings.KBACC * dt
            if self.kbx > 0:
                self.kbx = 0
        
        if self.kby < 0:
            self.kby += _Settings.KBACC * dt
            if self.kby > 0:
                self.kby = 0

    def render(self, default_display: pg.Surface, effects_display: pg.Surface):
        if self.sprite is None:
            return False
        self.drawbox.centerx = self.x
        self.drawbox.bottom = self.y
        default_display.blit(
            self.sprite,
            self.drawbox
        )
        self.accessory.render(default_display)

        use_effects = False
        use_effects = self.attack.render(default_display, effects_display) or use_effects
        
        use_effects = self.jump_particles.render(effects_display) or use_effects
        use_effects = np.any([particles.render(effects_display) for particles in self.dash_particles.values()]) or use_effects
        use_effects = self.hit_particles.render(effects_display) or use_effects

        return use_effects
