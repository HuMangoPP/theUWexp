import pygame as pg
import numpy as np

from ..util.transitions import transition_in, transition_out, TRANSITION_TIME
from ..fight.fighter import Fighter


class _Settings:
    DEFAULT_DISPLAY = 'default'
    EFFECTS_DISPLAY = 'gaussian_blur'
    OVERLAY_DISPLAY = 'black_alpha'

    LOGO_SIZE = (400,400)

    GOLD = (255, 213, 0)
    BLACK = (0,0,0)
    GRAY = (150,150,150)

    FIGHTERS = [
        'astro',
        'biotech',
        'civarch',
        'comm',
        'csse',
        'ece',
        'fin',
        'kine',
        'mathco',
        'mathphys',
        'med',
        'mte',
        'nanophys',
        'opto',
        'pharm',
        'phil',
        'plant',
        'stats'
    ]

    BULLET_TIME_FACTOR = 10
    BULLET_TIME = 1 / 2


def lerp(v1: np.ndarray, v2: np.ndarray, t: float):
    return np.array(v1) + (np.array(v2) - np.array(v1)) * t


class Menu:
    def __init__(self, client):
        self.client = client
        self.goto : str = None
    
    def _on_transition(self):
        # 0 -> no transition
        # 1 -> transition out
        # 2 -> black screen
        # 3 -> transition in
        self.transition_phase = 2
        self.transition_time = 0

    def on_load(self):
        self._on_transition()
    
    def update(self, events: list[pg.Event], dt: float):
        if self.transition_phase > 0:
            self.transition_time += dt
            if self.transition_phase == 1 and self.transition_time > TRANSITION_TIME:
                return {
                    'exit': False,
                    'goto': self.goto
                }
            if self.transition_time > TRANSITION_TIME:
                self.transition_time = 0
                self.transition_phase = (self.transition_phase + 1) % 4
        
        return {}
    
    def render(self) -> list[str]:
        self.client.displays[_Settings.DEFAULT_DISPLAY].fill((20, 26, 51))

        displays_to_render = [_Settings.DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(_Settings.OVERLAY_DISPLAY)
        return displays_to_render
        
    def render_overlay(self):
        if self.transition_phase == 1: 
            transition_out(self.client.displays[_Settings.OVERLAY_DISPLAY], self.transition_time)
        elif self.transition_phase == 2:
            self.client.displays[_Settings.OVERLAY_DISPLAY].fill((10, 10, 10))
        elif self.transition_phase == 3:
            transition_in(self.client.displays[_Settings.OVERLAY_DISPLAY], self.transition_time)


class StartMenu(Menu):
    def __init__(self, client):
        # init Menu
        super().__init__(client)
        self._load_assets()
        self._load_button_data()
        
        # override
        self.goto = 'main'
    
    def _load_assets(self):
        self.wlogo = pg.transform.scale(pg.image.load('./assets/menus/wlogo.png').convert_alpha(), _Settings.LOGO_SIZE)
        self.wlogo_rect = self.wlogo.get_rect()
        self.wlogo_rect.center = np.array(self.client.resolution) / 2 + np.array([0,-50])

    def _load_button_data(self):
        self.highlight = 1
        self.grow_dim = -1
        self.dim_speed = 1000 / 2000

    def update(self, events: list[pg.Event], dt: float):

        for event in events:
            if event.type == pg.MOUSEBUTTONUP and self.transition_phase == 0:
                self.transition_phase = 1
                self.transition_time = 0
                self.goto = 'main'
        
        self.highlight += self.dim_speed * self.grow_dim * dt
        if self.highlight >= 1:
            self.highlight = 1
            self.grow_dim = -1
        if self.highlight <= 0:
            self.highlight = 0
            self.grow_dim = 1

        return super().update(events, dt)

    def render(self) -> list[str]:
        displays_to_render = super().render()
        
        self.client.displays[_Settings.DEFAULT_DISPLAY].fill((255,255,255))
        self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
            self.wlogo,
            self.wlogo_rect
        )
        word = 'the'
        for i, char in enumerate(word):
            x = (i - len(word) / 2 + 1 / 2) * 60 + self.client.resolution[0] / 2
            if i % 2 == 0:
                self.client.font.render(
                    self.client.displays[_Settings.DEFAULT_DISPLAY], 
                    char,
                    x,
                    50, 
                    _Settings.BLACK,
                    50,
                    style='center'
                )
            else:
                self.client.font.render(
                    self.client.displays[_Settings.DEFAULT_DISPLAY], 
                    char, 
                    x, 
                    50, 
                    _Settings.GOLD, 
                    50, 
                    style='center'
                )
        
        word = 'experience'
        for i, char in enumerate(word):
            x = (i - len(word) / 2 + 1 / 2) * 60 + self.client.resolution[0] / 2
            if i % 2 == 0:
                self.client.font.render(
                    self.client.displays[_Settings.DEFAULT_DISPLAY], 
                    char,
                    x,
                    self.client.resolution[1] - 150, 
                    _Settings.BLACK,
                    50,
                    style='center'
                )
            else:
                self.client.font.render(
                    self.client.displays[_Settings.DEFAULT_DISPLAY], 
                    char, 
                    x, 
                    self.client.resolution[1] - 150, 
                    _Settings.GOLD, 
                    50, 
                    style='center'
                )
        
        pg.draw.rect(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            _Settings.GRAY, 
            pg.Rect(0, self.client.resolution[1]-75, self.client.resolution[0], 50)
        )
        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY], 
            'press anywhere to continue', 
            self.client.resolution[0] / 2, 
            self.client.resolution[1] - 50, 
            (255, 255, 255), 
            20, 
            'center', 
            self.highlight * 255
        )

        super().render_overlay()
        
        return displays_to_render


class MainMenu(Menu):
    def __init__(self, client):
        super().__init__(client)
        self._setup_buttons()

        # override
        self.goto = 'select'
    
    def _setup_buttons(self):
        self.training_rect = pg.Rect(
            0, 0,
            *np.array(self.client.resolution) * 3 / 5
        )
        self.options_rect = pg.Rect(
            *self.training_rect.bottomright,
            *(np.array(self.client.resolution) - np.array(self.training_rect.size))
        )
    
        self.fade_speed = 1000 / 250
        
        self.training_opacity = 1
        self.options_opacity = 1
    
    def update(self, events: list[pg.Event], dt: float):
        for event in events:
            if event.type == pg.MOUSEBUTTONUP:
                if self.training_rect.collidepoint(event.pos):
                    self.transition_phase = 1
                    self.transition_time = 0
        
        # hovering
        mpos = pg.mouse.get_pos()
        if self.training_rect.collidepoint(mpos):
            self.training_opacity = np.maximum(
                self.training_opacity - dt * self.fade_speed,
                0
            )
        else:
            self.training_opacity = np.minimum(
                self.training_opacity + dt * self.fade_speed,
                1
            )
        
        if self.options_rect.collidepoint(mpos):
            self.options_opacity = np.maximum(
                self.options_opacity - dt * self.fade_speed,
                0
            )
        else:
            self.options_opacity = np.minimum(
                self.options_opacity + dt * self.fade_speed,
                1
            )

        return super().update(events, dt)

    def render(self):
        displays_to_render = super().render()
        self.client.displays[_Settings.DEFAULT_DISPLAY].fill((255,255,255))

        pg.draw.rect(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            lerp(_Settings.BLACK, _Settings.GOLD, self.training_opacity),
            self.training_rect
        )
        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            'training mode',
            *self.training_rect.center,
            lerp(_Settings.GOLD, _Settings.BLACK, self.training_opacity),
            35, 
            style='center'
        )

        pg.draw.rect(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            lerp(_Settings.BLACK, _Settings.GOLD, self.options_opacity),
            self.options_rect
        )
        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            'options',
            *self.options_rect.center,
            lerp(_Settings.GOLD, _Settings.BLACK, self.options_opacity),
            35, 
            style='center'
        )

        super().render_overlay()

        return displays_to_render


class SelectMenu(Menu):
    def __init__(self, client):
        super().__init__(client)
        # self._load_assets()
        self._setup_variables()

        # override
        self.goto = 'fight'
    
    def _setup_variables(self):
        self.f1_selection = None
        self.f2_selection = None

        self.currently_picking = 1

        self.boxes = [
            pg.Rect(
                self.client.resolution[0] / 2 + (x - 3 / 2) * 160 + 5, 
                self.client.resolution[1] / 2 + (y - 6 / 2) * 60, 
                150, 50
            )
            for y in np.arange(6)
            for x in np.arange(3)
        ]
    
    def update(self, events: list[pg.Event], dt: float):
        for event in events:
            if event.type == pg.MOUSEBUTTONUP:
                for i, box in enumerate(self.boxes):
                    if box.collidepoint(event.pos):
                        if self.currently_picking == 1:
                            self.f1_selection = _Settings.FIGHTERS[i]
                            self.currently_picking = 2
                        elif self.currently_picking == 2:
                            self.f2_selection = _Settings.FIGHTERS[i]
                            self.currently_picking = 0
                
            if event.type == pg.KEYDOWN:
                if (
                    event.key == pg.K_RETURN and 
                    self.f1_selection is not None and
                    self.f2_selection is not None
                ):
                    self.transition_phase = 1
                    self.transition_time = 0
                if event.key == pg.K_1:
                    self.currently_picking = 1
                if event.key == pg.K_2:
                    self.currently_picking = 2
        
        return super().update(events, dt)

    def render(self):
        displays_to_render = super().render()
        
        self.client.displays[_Settings.DEFAULT_DISPLAY].fill((255,255,255))
        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            'character select',
            self.client.resolution[0] / 2,
            50,
            (0,0,0),
            25,
            style='center'
        )

        [pg.draw.rect(self.client.displays[_Settings.DEFAULT_DISPLAY], (50,50,50), box) for box in self.boxes]
        [self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            fighter_name,
            *box.center,
            (255,255,255),
            10,
            style='center'
        ) for fighter_name, box in zip(_Settings.FIGHTERS, self.boxes)]

        if self.currently_picking == 1:
            pg.draw.rect(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                _Settings.GOLD,
                pg.Rect(
                    50, 50,
                    self.client.resolution[0] / 4,
                    self.client.resolution[1] - 100
                ),
                10
            )
        elif self.currently_picking == 2:
            pg.draw.rect(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                _Settings.GOLD,
                pg.Rect(
                    self.client.resolution[0] * 3 / 4 - 50, 
                    50,
                    self.client.resolution[0] / 4,
                    self.client.resolution[1] - 100,
                ),
                10
            )
        
        if self.f1_selection is not None:
            sprite = self.client.character_assets.get(self.f1_selection, self.client.character_assets['basic'])['idle']['right'][0]
            accessory = self.client.accessory_assets.get(self.f1_selection, {
                'right': None,
                'left': None
            })['right']

            drawbox = sprite.get_rect()
            drawbox.centerx = 50 + self.client.resolution[0] / 8
            drawbox.centery = 50 + (self.client.resolution[1] - 100) / 2

            self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                sprite,
                drawbox
            )
            if accessory is not None:
                self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                accessory,
                drawbox
            )
            
        if self.f2_selection is not None:
            sprite = self.client.character_assets.get(self.f2_selection, self.client.character_assets['basic'])['idle']['left'][0]
            accessory = self.client.accessory_assets.get(self.f2_selection, {
                'right': None,
                'left': None
            })['left']

            drawbox = sprite.get_rect()
            drawbox.centerx = self.client.resolution[0] * 3 / 4 - 50 + self.client.resolution[0] / 8
            drawbox.centery = 50 + (self.client.resolution[1] - 100) / 2

            self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                sprite,
                drawbox
            )
            if accessory is not None:
                self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                accessory,
                drawbox
            )

        super().render_overlay()

        return displays_to_render
        

class FightMenu(Menu):
    def __init__(self, client):
        super().__init__(client)

        self._load_fighter_data()
        self._setup_variables()

    def _load_fighter_data(self):
        self.f1 = Fighter()
        self.f2 = Fighter()
    
    def _setup_variables(self):
        self.bullet_time = False
        self.bullet_time_elapsed = 0
    
    def select_fighters(self, select_menu):
        self.f1.fighter_type = select_menu.f1_selection
        self.f2.fighter_type = select_menu.f2_selection

    def _check_victory(self):
        return 0
    
    def update(self, events: list[pg.Event], dt: float):
        self.f1.input(self.client.keybinds['f1'], events)

        if self.bullet_time:
            self.bullet_time_elapsed -= dt
            if self.bullet_time_elapsed <= 0:
                self.bullet_time = False
            else:
                dt /= _Settings.BULLET_TIME_FACTOR

        self.f1.update(dt)
        self.f2.update(dt)
        
        self.f1.animate(
            self.client.character_assets, 
            self.client.accessory_assets,
            self.client.attack_assets,
            dt
        )
        self.f2.animate(
            self.client.character_assets,
            self.client.accessory_assets,
            self.client.attack_assets,
            dt
        )

        if (
            self.f1.attack.check_hit(self.f2) or 
            self.f2.attack.check_hit(self.f1)
        ):
            self.bullet_time = True
            self.bullet_time_elapsed = _Settings.BULLET_TIME

        return super().update(events, dt)
    
    def render(self):
        displays_to_render = super().render()

        self.client.displays[_Settings.DEFAULT_DISPLAY].fill((0,0,0))
        self.client.displays[_Settings.DEFAULT_DISPLAY].blit(self.client.bgs['uwmain'], (0,0))

        use_effects = False 
        self.client.displays[_Settings.EFFECTS_DISPLAY].fill((0,0,0))
        use_effects = any([
            self.f1.render(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                self.client.displays[_Settings.EFFECTS_DISPLAY]
            ),
            self.f2.render(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                self.client.displays[_Settings.EFFECTS_DISPLAY]
            )
        ])
        if use_effects:
            displays_to_render.insert(1, _Settings.EFFECTS_DISPLAY)

        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            f'{round(self.f1.gpa, 2)} gpa',
            150, 50,
            lerp(np.array([255,0,0]), np.array([0,255,0]), self.f1.gpa / 4),
            25,
            style='center'
        )

        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            f'{round(self.f2.gpa, 2)} gpa',
            self.client.resolution[0] - 150, 50,
            lerp(np.array([255,0,0]), np.array([0,255,0]), self.f2.gpa / 4),
            25,
            style='center'
        )

        super().render_overlay()

        return displays_to_render

