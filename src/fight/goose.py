import pygame as pg
import numpy as np
import json

from .effects import Boom, Sparks, Bolt, DustCloud
from ..util.math_util import lerp


class _Settings:
    GROUND_LEVEL = 675
    
    ANIMATION_SPEED = 12

    X_SPD = 300
    JUMP_SPEED = -400
    DASH_SPEED = 1000
    DASH_SLOW = 2000
    SQUASH_SPEED = 5
    X_ACC = 1500
    Y_ACC = 980
    KNOCKBACK_ACC = 500
    
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
            mask = pg.mask.from_surface(self.sprite)
            # check parry
            overlap = mask.overlap(
                pg.mask.from_surface(fighter.attack.sprite),
                np.array(fighter.attack.drawbox.topleft) - np.array(self.drawbox.topleft)
            ) if fighter.attack.sprite is not None else None
            if overlap is not None:
                self.fighter.hit.parry()
                self.dangerous = False
                
                self.fighter.hit_particles['sparks'].create_new_particles(
                    *(np.array(self.drawbox.topleft) + np.array(overlap)), 
                    0, -1
                )
                self.fighter.hit_particles['bolt'].create_new_particles(
                    *(np.array(self.drawbox.topleft) + np.array(overlap)), 
                    orientation,
                    0
                )
                return np.array(self.drawbox.topleft) + np.array(overlap)

            # check hit with character
            overlap = mask.overlap(
                pg.mask.from_surface(fighter.sprite),
                np.array(fighter.drawbox.topleft) - np.array(self.drawbox.topleft)
            )
            if overlap is not None:
                fighter.hit.create_new_hit({
                    'fighter_type': self.fighter.fighter_type,
                    'attack_type': self.attack_type,
                    'orientation': orientation,
                    'hit_origin': np.array(self.drawbox.topleft) + np.array(overlap)
                })
                self.dangerous = False

        return None

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
    
    def create_new_hit(
        self,
        hit_data: dict,
    ):
        self.was_hit = True
        self.hit_delay = _Settings.HIT_DELAY
        self.hit_data = hit_data
    
    def parry(self):
        self.was_hit = False
        self.hit_data = {}

    def update(self, dt: float):
        if self.was_hit:
            self.hit_delay -= dt
        
            if self.hit_delay <= 0:
                kb = _Settings.KNOCKBACK[self.hit_data['fighter_type']][self.hit_data['attack_type']]
                self.fighter.knockback(2 * self.hit_data['orientation'] * kb, - kb)
                self.fighter.gpa -= _Settings.DAMAGE[self.hit_data['fighter_type']][self.hit_data['attack_type']]
                hit_origin : np.ndarray = self.hit_data['hit_origin']

                self.was_hit = False
                self.hit_data = {}

                return hit_origin
        return None


class Accessory:
    def __init__(self, fighter):
        self.fighter = fighter
        self._setup_state()
        self._setup_animation()
    
    def _setup_state(self):
        self.pos = self.fighter.pos
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


class Goose:
    def __init__(self, goose_data: dict):
        self._setup_state(goose_data)
        self._setup_animation(goose_data)
        self._setup_input()

    def _setup_state(self, goose_data: dict):
        self.reset_state(goose_data)

        # attack and hitbox
        self.attack = Attack(self)
        self.hit = Hit(self)

    def reset_state(self, goose_data: dict):
        # get the goose major
        self.major = goose_data['major']

        # goose movement
        self.pos = np.array([goose_data['x'], 500])
        self.vel = np.zeros(2)
        self.knockback = np.zeros(2)
        self.dash_time = 0

        # goose gpa
        self.gpa = 4.0

    def _setup_animation(self, goose_data: dict):
        # get the sprite
        self.sprite = None
        self.drawbox = None

        # get the animation state
        self.action = 'idle'
        self.facing = goose_data['facing']
        self.frame_index = 0

        # accessory
        self.accessory = Accessory(self)

        # self.jump_particles = DustCloud()
        # self.dash_particles = {
        #     'boom': Boom(),
        #     'bolt': Bolt(),
        # }
        # self.hit_particles = {
        #     'bolt': Bolt(),
        #     'sparks': Sparks()
        # }

        # self.sfx = {
        #     'honk': pg.mixer.Sound('./assets/sounds/honk.wav'),
        #     'hit': pg.mixer.Sound('./assets/sounds/hit.wav')
        # }

    def _setup_input(self):
        # inputs
        self.action_inputs = {
            'no_action': 0,
            'jump': 0,
            'right': 0,
            'left': 0,
            'light_attack': 0,
            'heavy_attack': 0,
            'dash': 0,
        }

    def _change_animation(self, action: str, reset: bool = False):
        # change the animation state
        if self.action != action or reset:
            self.frame_index = 0
        self.action = action

    def get_knocked_back(self, knockback: np.ndarray):
        # get knocked back
        self.knockback = knockback

        # orientation = 'right' if knockback[0] >= 0 else 'left'
        # self.hit_particles['sparks'].create_new_particles(*self.drawbox.center, 0, -1)
        # self.hit_particles['bolt'].create_new_particles(*self.drawbox.center, orientation, 0)
        
        # self.sfx['hit'].play()

    def animate(
        self, 
        dt: float,
        character_assets: dict[str, dict[str, dict[str, list[pg.Surface]]]],
        accessory_assets: dict,
        attack_assets: dict
    ):
        # if self.attack.active:
        #     if 'honk' not in self.action:
        #         self._change_animation(f'honk_startup')
        # elif 'honk' in self.action:
        #     self._change_animation(f'honk_recovery')
        # elif self.dashing:
        #     self._change_animation('dash')
        # elif self.y < _Settings.GROUND_LEVEL:
        #     if self.yvel < 0:
        #         self._change_animation('jump')
        #     else:
        #         self._change_animation('fall')
        # elif self.xvel:
        #     self._change_animation('walk')
        # else:
        #     self._change_animation('idle')

        # update animation state
        if self.dash_time > 0:
            self._change_animation('dash')
        elif self.pos[1] < _Settings.GROUND_LEVEL:
            if self.vel[1] < 0:
                self._change_animation('jump')
            else:
                self._change_animation('fall')
        elif self.vel[0]:
            self._change_animation('walk')
        else:
            self._change_animation('idle')
        
        # update animation
        self.frame_index += dt * _Settings.ANIMATION_SPEED
        animation_length = len(character_assets.get(self.major, character_assets['basic'])[self.action][self.facing])
        # end of animation frames
        if self.frame_index >= animation_length:
            self.frame_index = 0
            if self.action in ['jump', 'fall', 'hit', 'dash']:
                self.frame_index = animation_length - 1
            if self.action in ['honk_startup']:
                self._change_animation('honk_active')
            if self.action in ['honk_recovery']:
                self._change_animation('idle')

        # get sprite
        self.sprite = character_assets.get(self.major, character_assets['basic'])[self.action][self.facing][int(self.frame_index)]
        self.drawbox = self.sprite.get_rect()
        self.drawbox.centerx = self.pos[0]
        self.drawbox.bottom = self.pos[1]

        # # animate accessories
        # self.accessory.animate(dt, accessory_assets)
        
        # # animate attacks
        # self.attack.animate(dt, attack_assets)
        
        # self.jump_particles.animate(dt)
        # [particles.animate(dt) for particles in self.dash_particles.values()]
        # [particles.animate(dt) for particles in self.hit_particles.values()]

    def input(self, events: list[pg.Event], keybinds: dict[int, str]):
        for event in events:
            if event.type == pg.KEYDOWN:
                # get inputs
                action = keybinds.get(event.key, 'no_action')
                self.action_inputs[action] = 1
            if event.type == pg.KEYUP:
                # remove inputs
                action = keybinds.get(event.key, 'no_action')
                self.action_inputs[action] = 0

                # if event.key == keybinds['jump'] and self.y >= _Settings.GROUND_LEVEL:
                #     self.yvel = _Settings.JUMP_SPEED
                #     self.jump_particles.create_new_particles(self.x, self.y, 1 if self.facing == 'right' else -1)
                
                # if event.key == keybinds['dash']:
                #     orientation = 1 if self.facing == 'right' else -1
                #     for dir_input in self.direction_inputs:
                #         if dir_input == 'left':
                #             orientation = -1
                #         elif dir_input == 'right':
                #             orientation = 1

                #     self.dashing = True
                #     self.xvel = _Settings.DASH_SPEED * orientation
                #     if 'up' in self.direction_inputs:
                #         self.yvel = -_Settings.DASH_SPEED / 2
                #         self.xvel = self.xvel * np.sqrt(3) / 2

                #     self.dash_particles['boom'].create_new_particles(
                #         *self.drawbox.center,
                #         1 if self.facing == 'right' else -1
                #     )
                #     self.dash_particles['bolt'].create_new_particles(*self.drawbox.center, orientation, 0)
                
                # for keybind in ['light', 'spec']:
                #     if event.key == keybinds[keybind]:
                #         self.attack_input = keybind
            
            # if event.type == pg.KEYUP:
            #     if event.key == keybinds['right']:
            #         self.movement_inputs = [movement_input for movement_input in self.movement_inputs if movement_input != 'right']
            #         self.direction_inputs = [direction_input for direction_input in self.direction_inputs if direction_input != 'right']
            #     if event.key == keybinds['left']:
            #         self.movement_inputs = [movement_input for movement_input in self.movement_inputs if movement_input != 'left']
            #         self.direction_inputs = [direction_input for direction_input in self.direction_inputs if direction_input != 'left']
            #     if event.key == keybinds['up']:
            #         self.movement_inputs = [movement_input for movement_input in self.movement_inputs if movement_input != 'up']
            #         self.direction_inputs = [direction_input for direction_input in self.direction_inputs if direction_input != 'up']

    def update(self, dt: float):
        # handle attack inputs
        if self.action_inputs['light_attack'] == 1 and not self.attack.active:
            if self.accessory.drawbox is not None:
                xy = self.accessory.drawbox.center
            else:
                xy = self.drawbox.center
            attack_type = 'side'
            # self.attack.create_new_attack(
            #     f'{attack_type}-light_attack',
            #     xy
            # )
            self.action_inputs['light_attack'] = 0
        elif self.action_inputs['heavy_attack'] == 1 and not self.attack.active:
            if self.accessory.drawbox is not None:
                xy = self.accessory.drawbox.center
            else:
                xy = self.drawbox.center
            attack_type = 'side'
            # self.attack.create_new_attack(
            #     f'{attack_type}-heavy_attack',
            #     xy
            # )
            self.action_inputs['heavy_attack'] = 0

        # handle movement inputs
        if self.action_inputs['dash'] == 1:
            self.dash_time = 0.5
            self.action_inputs['dash'] = 0
        if self.action_inputs['jump'] == 1:
            self.vel[1] = _Settings.JUMP_SPEED
            self.action_inputs['jump'] = 0
        
        if self.dash_time <= 0 and not self.attack.active:
            is_moving = False
            if self.action_inputs['right'] == 1:
                self.facing = 'right'
                self.vel[0] = min(
                    self.vel[0] + _Settings.X_ACC * dt,
                    _Settings.X_SPD
                )
                is_moving = True
            if self.action_inputs['left'] == 1:
                self.facing = 'left'
                self.vel[0] = max(
                    self.vel[0] - _Settings.X_ACC * dt,
                    -_Settings.X_SPD
                )
                is_moving = True
            
            if not is_moving:
                sign = self.vel[0]
                self.vel[0] = self.vel[0] - sign * _Settings.X_ACC * dt
                if sign * self.vel[0] <= 0:
                    self.vel[0] = 0

        # movement actions
        if self.dash_time > 0:
            self.dash_time -= dt
            self.vel[0] = lerp(0, _Settings.DASH_SPEED, self.dash_time / 0.5)

        # move
        self.pos = self.pos + self.vel * dt

        # fall
        if self.pos[1] >= _Settings.GROUND_LEVEL:
            self.pos[1] = _Settings.GROUND_LEVEL
            self.vel[1] = 0
        else:
            self.vel[1] += _Settings.Y_ACC * dt
        
        # handle knockback movement
        self.pos = self.pos + self.knockback * dt 
        signs = np.sign(self.knockback)
        self.knockback = self.knockback - signs * _Settings.KNOCKBACK_ACC * dt
        self.knockback[signs * self.knockback <= 0] = 0

    def check_collide(self, rival_goose):
        ...

    def render(self, default: pg.Surface, gaussian_blur: pg.Surface):
        # no sprite
        if self.sprite is None:
            return

        # render sprite
        default.blit(self.sprite, self.drawbox)

        # # render accessory
        # self.accessory.render(default)

        # # render attack
        # self.attack.render(default)
        # use_effects = False
        # use_effects = self.jump_particles.render(effects_display) or use_effects
        # use_effects = np.any([particles.render(effects_display) for particles in self.dash_particles.values()]) or use_effects
        # use_effects = np.any([particles.render(effects_display) for particles in self.hit_particles.values()]) or use_effects
