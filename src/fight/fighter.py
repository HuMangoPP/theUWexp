import pygame as pg
import numpy as np
import json

from .effects import Boom, Sparks, Bolt, DustCloud


class _Settings:
    GROUND_LEVEL = 600
    
    ANIMATION_SPEED = 12

    X_SPD = 300
    JUMP_SPEED = -400
    DASH_SPEED = 1000
    DASH_SLOW = 1250
    SQUASH_SPEED = 5
    XACC = 1500
    YACC = 980
    KBACC = 500
    
    HIT_DELAY = 0.1

    DAMAGE = {}
    with open('./assets/attacks/damages.json', 'r') as f:
        DAMAGE = json.load(f)

    KNOCKBACK = {}
    with open('./assets/attacks/knockbacks.json', 'r') as f:
        KNOCKBACK = json.load(f)


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
                fighter.hit.create_new_hit({
                    'fighter_type': self.fighter.fighter_type,
                    'attack_type': self.attack_type,
                    'orientation': orientation
                }, None)
                self.dangerous = False

    def animate(
        self, 
        attack_assets: dict,
        dt: float
    ):
        if self.active:
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

        # [particle.animate(dt) for particle in self.particles.values()]

    def _update_drawbox(self):
        self.drawbox.center = (self.x, self.y)
    
    def render(self, default_display: pg.Surface):
        if self.sprite is not None:
            default_display.blit(
                self.sprite,
                self.drawbox
            )


class Hit:
    def __init__(self, fighter):
        self.fighter = fighter
        self._setup_state()
    
    def _setup_state(self):
        self.was_hit = False
        self.hit_delay = _Settings.HIT_DELAY
        self.hit_data = {}
        self.hurtbox = None
    
    def create_new_hit(
        self,
        hit_data: dict,
        hurtbox: pg.Mask
    ):
        self.was_hit = True
        self.hit_delay = _Settings.HIT_DELAY
        self.hit_data = hit_data
        self.hurtbox = hurtbox
    
    def update(self, dt: float):
        if self.was_hit:
            self.hit_delay -= dt
        
            if self.hit_delay <= 0:
                kb = _Settings.KNOCKBACK[self.hit_data['fighter_type']][self.hit_data['attack_type']]
                self.fighter.knockback(2 * self.hit_data['orientation'] * kb, - kb)
                self.fighter.gpa -= _Settings.DAMAGE[self.hit_data['fighter_type']][self.hit_data['attack_type']]

                self.was_hit = False
                self.hit_data = {}
                self.hurtbox = None

                return True
        return False


class Accessory:
    def __init__(self, fighter):
        self.fighter = fighter
        self._setup_state()
        self._setup_animation()
    
    def _setup_state(self):
        self.x = self.fighter.x
        self.y = self.fighter.y
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
        self.hit = Hit(self)

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
            'bolt': Bolt(),
        }
        self.hit_particles = {
            'bolt': Bolt(),
            'sparks': Sparks()
        }

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

        self.hit_particles['sparks'].create_new_particles(*self.drawbox.center, 0, -1)
        self.hit_particles['bolt'].create_new_particles(*self.drawbox.center, orientation, 0)

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
        [particles.animate(dt) for particles in self.hit_particles.values()]

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
                    self.dash_particles['bolt'].create_new_particles(*self.drawbox.center, orientation, 0)
                
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

        return self.hit.update(dt)

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

        self.attack.render(default_display)
        use_effects = False
        use_effects = self.jump_particles.render(effects_display) or use_effects
        use_effects = np.any([particles.render(effects_display) for particles in self.dash_particles.values()]) or use_effects
        use_effects = np.any([particles.render(effects_display) for particles in self.hit_particles.values()]) or use_effects

        return use_effects
