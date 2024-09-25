import pygame as pg
import numpy as np
import json

from .vfx import Boom, Sparks, Bolt, DustCloud
from ..util.math_util import lerp


class _Settings:
    GROUND_LEVEL = 675
    
    ANIMATION_SPEED = 12

    SPEED = 300
    ACCELERATION = 1000
    JUMP_SPEED = -400
    DASH_SPEED = 1000
    DASH_TIME = 1 / 2
    SQUASH_SPEED = 5
    GRAVITY = 980
    ORIENTATION = dict(right=1, left=-1)
    
    ATTACK_COOLDOWN = 0.5

    HIT_DELAY = 0.1

    DAMAGE = {}
    with open('./assets/attacks/damages.json', 'r') as f:
        DAMAGE = json.load(f)

    KNOCKBACK = {}
    with open('./assets/attacks/knockbacks.json', 'r') as f:
        KNOCKBACK = json.load(f)


class Attack:
    def __init__(self):
        self._setup_state()
        self._setup_animation()
    
    def _setup_state(self):
        # the goose is attacking
        self.active = False
        # the attack can hit the other goose
        self.dangerous = False
        # cooldown
        self.cooldown = 0
       
    def _setup_animation(self): 
        # render data
        self.orientation = 0
        self.attack_type = None
        self.sprite = None
        self.drawbox = None

        # animation
        self.frame_index = 0
    
    def create_new_attack(self, orientation: str, attack_type: str):
        # set to active and dangerous
        self.active = True
        self.dangerous = True

        # update data
        self.orientation = orientation
        self.attack_type = attack_type

        # reset animatino
        self.frame_index = 0

    def animate(self, goose, dt: float, attack_assets: dict[str, dict[str, dict[str, list[pg.Surface]]]]):
        if self.active:
            # animate
            self.frame_index += dt * _Settings.ANIMATION_SPEED
            # animation_length = len(attack_assets[goose.major][self.attack_type][goose.facing])
            animation_length = 20

            # once animation is done, the attack ends
            if self.frame_index >= animation_length:
                self.cooldown = _Settings.ATTACK_COOLDOWN
                self.frame_index = 0
                self.active = False
            
            # get the sprite
            if self.active:
                # white rectangle
                self.sprite = pg.Surface((100, 50))
                self.sprite.fill((255, 255, 255))
                # self.sprite = attack_assets[goose.major][self.attack_type][goose.facing][int(self.frame_index)]
                
                # get drawbox
                self.drawbox = self.sprite.get_rect()
                
                if self.attack_type[:1] == 's':
                    self.drawbox.centery = goose.drawbox.centery
                    if self.orientation == 'left':
                        self.drawbox.right = goose.drawbox.centerx
                    else:
                        self.drawbox.left = goose.drawbox.centerx
                elif self.attack_type[:1] == 'n':
                    self.drawbox.centerx = goose.drawbox.centerx
                    self.drawbox.bottom = goose.drawbox.centery
                else:
                    self.drawbox.centerx = goose.drawbox.centerx
                    self.drawbox.top = goose.drawbox.centery
            else:
                self.sprite = None

        self.cooldown = max(self.cooldown - dt, 0)
    
    def render(self, default: pg.Surface):
        # render when sprite is available
        if self.sprite is not None:
            default.blit(self.sprite, self.drawbox)


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
    def __init__(self, goose):
        self._setup_state(goose)
        self._setup_animation()
    
    def _setup_state(self, goose):
        # movement
        self.pos = goose.pos

        # logic for subpositioning
        self.orientation = 0 if goose.facing == 'left' else 1

    def _setup_animation(self):
        # sprites
        self.sprite = None
        self.drawbox = None

    def animate(self, goose, dt: float, accessory_assets: dict[str, dict[str, pg.Surface]]):
        # calculate the displacement, the accessory moves and lags behind the goose
        disp = goose.pos - self.pos
        self.pos = self.pos + disp * dt

        # subpositioning logic
        if goose.facing == 'right':
            spd = (1 - self.orientation)
            self.orientation = min(self.orientation + spd * dt, 1)
        else:
            spd = self.orientation
            self.orientation = max(self.orientation - spd * dt, 0)

        self.sprite = accessory_assets.get(goose.major, {
            'right': None,
            'left': None
        })[goose.facing]
        if self.sprite is not None and goose.drawbox is not None:
            self.drawbox = self.sprite.get_rect()
            self.drawbox.centerx = self.pos[0] - lerp(-self.drawbox.width, self.drawbox.width, self.orientation) / 2
            self.drawbox.bottom = self.pos[1] - goose.drawbox.height / 2

    def render(self, default: pg.Surface):
        # render if sprite is available
        if self.sprite is not None:
            default.blit(self.sprite, self.drawbox)


class Goose:
    def __init__(self, goose_data: dict):
        self.reset_state(goose_data)

    def _setup_state(self, goose_data: dict):
        # get the goose major
        self.major = goose_data['major']

        # goose movement
        self.pos = np.array([goose_data['x'], 500])
        self.vel = np.zeros(2)
        self.knockback = np.zeros(2)
        self.dash_time = 0

        # goose gpa
        self.gpa = 4.0

        # attack and hitbox
        self.attack = Attack()
        # self.hit = Hit(self)

    def _setup_animation(self, goose_data: dict):
        # get the sprite
        self.sprite = None
        self.drawbox = None

        # get the animation state
        self.action = 'idle'
        self.facing = goose_data['facing']
        self.frame_index = 0

        # # accessory
        # self.accessory = Accessory(self)

        # particle effects
        self.dash_vfx = Boom()
        self.hit_vfx = Sparks()
        self.impact_vfx = Bolt()

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
            'jump': 0,
            'light_attack': 0,
            'special_attack': 0,
            'dash': 0,
        }
        self.direction_inputs = {
            'up': 0,
            'down': 0,
            'left': 0,
            'right': 0,
        }

    def reset_state(self, goose_data: dict):
        self._setup_state(goose_data)
        self._setup_animation(goose_data)
        self._setup_input()

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
        attack_assets: dict
    ):
        # update animation state
        if self.attack.active:
            self._change_animation('idle')
        elif self.dash_time > 0:
            self._change_animation('dash')
        elif self.pos[1] < _Settings.GROUND_LEVEL:
            if self.vel[1] < 0:
                self._change_animation('jump')
            else:
                self._change_animation('fall')
        elif self.vel[0]:
            self._change_animation('move')
        else:
            self._change_animation('idle')
        
        # update animation
        self.frame_index += dt * _Settings.ANIMATION_SPEED
        animation_length = len(character_assets.get(self.major, character_assets['basic'])[self.action][self.facing])
        # end of animation frames
        if self.frame_index >= animation_length:
            self.frame_index = 0
            if self.action in ['jump', 'fall']:
                self.frame_index = animation_length - 1

        # get sprite
        self.sprite = character_assets.get(self.major, character_assets['basic'])[self.action][self.facing][int(self.frame_index)]
        self.drawbox = self.sprite.get_rect()
        self.drawbox.centerx = self.pos[0]
        self.drawbox.bottom = self.pos[1]

        # # animate accessories
        # self.accessory.animate(self, dt, accessory_assets)
        
        # animate attacks
        self.attack.animate(self, dt, attack_assets)
        
        # animate effects
        self.dash_vfx.animate(dt)
        self.hit_vfx.animate(dt)
        self.impact_vfx.animate(dt)

    def input(self, events: list[pg.Event], keybinds: dict[int, str]):
        for event in events:
            if event.type == pg.KEYDOWN:
                # get inputs
                key_function = keybinds.get(event.key, 'no_action')
                if key_function in self.action_inputs:
                    self.action_inputs[key_function] = 1
                if key_function in self.direction_inputs:
                    self.direction_inputs[key_function] = 1
            if event.type == pg.KEYUP:
                # remove inputs
                key_function = keybinds.get(event.key, None)
                if key_function in self.action_inputs:
                    self.action_inputs[key_function] = 0
                if key_function in self.direction_inputs:
                    self.direction_inputs[key_function] = 0

    def update(self, dt: float):
        # handle attack inputs
        if not self.attack.active and self.attack.cooldown <= 0:
            if self.action_inputs['light_attack'] == 1:
                if self.pos[1] < _Settings.GROUND_LEVEL:
                    attack_type = 'air'
                else:
                    attack_type = 'light'
                self.action_inputs['light_attack'] = 0
            elif self.action_inputs['special_attack'] == 1 and self.pos[1] >= _Settings.GROUND_LEVEL:
                attack_type = 'special'
                self.action_inputs['special_attack'] = 0
            else:
                attack_type = None
            if attack_type is not None:
                if self.direction_inputs['up'] == 1:
                    attack_direction = 'n'
                elif self.direction_inputs['down'] == 1:
                    attack_direction = 'd'
                elif self.direction_inputs['left'] == 1 or self.direction_inputs['right'] == 1:
                    attack_direction = 's'
                else:
                    attack_direction = 'n'
                self.attack.create_new_attack(self.facing, f'{attack_direction}{attack_type}')

        # handle movement inputs
        if self.action_inputs['dash'] == 1:
            self.dash_time = _Settings.DASH_TIME
            self.action_inputs['dash'] = 0
            
            x = self.drawbox.centerx
            w = self.drawbox.w
            y = self.drawbox.bottom - self.drawbox.height / 3
            self.dash_vfx.create_vfx(np.array([
                [x, y],
                [x - w / 4, y],
                [x + w / 4, y]
            ]))
        if self.action_inputs['jump'] == 1:
            self.vel[1] = _Settings.JUMP_SPEED
            self.action_inputs['jump'] = 0
        
        can_move = True
        can_change_direction = True
        if self.attack.active:
            self.dash_time = 0
            can_move = 'air' in self.attack.attack_type # prevent movement while attacking
            can_change_direction = False
        
        if self.dash_time > 0: # goose is dashing
            self.dash_time = max(self.dash_time - dt, 0)
            self.vel[0] = _Settings.ORIENTATION[self.facing] * lerp(0, _Settings.DASH_SPEED, self.dash_time + _Settings.DASH_TIME)
            can_move = False
            can_change_direction = False
        
        # handle movement inputs
        is_moving = False
        if can_move:
            if self.direction_inputs['right'] == 1:
                if can_change_direction:
                    self.facing = 'right'
                self.vel[0] = min(self.vel[0] + _Settings.ACCELERATION * dt, _Settings.SPEED)
                is_moving = True
            if self.direction_inputs['left'] == 1:
                if can_change_direction:
                    self.facing = 'left'
                self.vel[0] = max(self.vel[0] - _Settings.ACCELERATION * dt, -_Settings.SPEED)
                is_moving = True
        if not is_moving: # de-celerate
            sign = np.sign(self.vel[0])
            self.vel[0] = self.vel[0] - sign * _Settings.ACCELERATION * dt
            if sign * self.vel[0] <= 0:
                self.vel[0] = 0
        
        # move
        self.pos = self.pos + self.vel * dt

        # fall
        if self.pos[1] >= _Settings.GROUND_LEVEL:
            self.pos[1] = _Settings.GROUND_LEVEL
            self.vel[1] = 0
        else:
            self.vel[1] += _Settings.GRAVITY * dt
        
        # handle knockback movement
        # self.pos = self.pos + self.knockback * dt 
        # signs = np.sign(self.knockback)
        # self.knockback = self.knockback - signs * _Settings.ACCELERATION * dt
        # self.knockback[signs * self.knockback <= 0] = 0

    def check_collide(self, rival_goose):
        if self.dash_time > 0: # invincibility
            return False
        if not rival_goose.attack.active or not rival_goose.attack.dangerous: # no attack 
            return False
        if self.sprite is None: # no hitbox
            return False
        if rival_goose.attack.sprite is None: # no hurtbox
            return False
        
        # create masks for collision
        goose_mask = pg.mask.from_surface(self.sprite)
        attack_mask = pg.mask.from_surface(rival_goose.attack.sprite)

        # calculate collision
        collision = goose_mask.overlap(attack_mask, np.array(rival_goose.attack.drawbox.topleft) - np.array(self.drawbox.topleft))
        if collision is not None:
            self.gpa -= 0.5 # decrease gpa
            rival_goose.attack.dangerous = False # prevent future collisions
            angle = np.arctan2(
                rival_goose.drawbox.centerx - self.drawbox.centerx,
                rival_goose.drawbox.centery - self.drawbox.centery
            )
            self.hit_vfx.create_vfx(self.drawbox.center, angle) # sparks
            angle = np.arctan2(
                self.drawbox.centerx - rival_goose.attack.drawbox.centerx,
                self.drawbox.centery - rival_goose.attack.drawbox.centery
            )
            self.impact_vfx.create_vfx(self.drawbox.center, angle) # impact
            return True
        return False

    def render(self, default: pg.Surface, gaussian_blur: pg.Surface):
        # no sprite
        if self.sprite is None:
            return

        # render sprite
        default.blit(self.sprite, self.drawbox)

        # # render accessory
        # self.accessory.render(default)

        # render attack
        self.attack.render(default)

        # render effects
        self.dash_vfx.render(gaussian_blur)
        self.hit_vfx.render(gaussian_blur)
        self.impact_vfx.render(gaussian_blur)
