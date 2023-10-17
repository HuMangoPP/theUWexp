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
    LIGHT = (245,245,245)

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
    
    BGS = [
        'uwmain',
        'dp',
        'm3',
        'e7',
        'qnc',
        'exp',
        'hh',
        'ev3'
    ]

    BULLET_TIME_FACTOR = 10
    BULLET_TIME = 1 / 2


def lerp(v1: np.ndarray, v2: np.ndarray, t: float):
    return np.array(v1) + (np.array(v2) - np.array(v1)) * np.clip(t, a_min=0, a_max=1)


def get_splash(character_assets: dict, accessory_assets: dict, fighter_type: str, facing: str) -> tuple[pg.Surface, pg.Surface]:
    sprite = character_assets.get(fighter_type, character_assets['basic'])['idle'][facing][0]
    accessory = accessory_assets.get(fighter_type, {
        'right': None,
        'left': None
    })[facing]

    return sprite, accessory


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
        displays_to_render = [_Settings.DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(_Settings.OVERLAY_DISPLAY)
            self._render_overlay()
        return displays_to_render
        
    def _render_overlay(self):
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
        self.wlogo = pg.transform.scale(pg.image.load('./assets/ui/uw.png').convert_alpha(), _Settings.LOGO_SIZE)
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
        
        self.client.displays[_Settings.DEFAULT_DISPLAY].fill(_Settings.LIGHT)
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

        self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
            self.client.cursor, pg.mouse.get_pos()
        )
        
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
        self.client.displays[_Settings.DEFAULT_DISPLAY].fill(_Settings.LIGHT)

        pg.draw.rect(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            lerp(_Settings.GOLD, _Settings.BLACK, self.training_opacity),
            self.training_rect
        )
        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            'training mode',
            *self.training_rect.center,
            lerp(_Settings.BLACK, _Settings.GOLD, self.training_opacity),
            35, 
            style='center'
        )

        pg.draw.rect(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            lerp(_Settings.GOLD, _Settings.BLACK, self.options_opacity),
            self.options_rect
        )
        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            'options',
            *self.options_rect.center,
            lerp(_Settings.BLACK, _Settings.GOLD, self.options_opacity),
            35, 
            style='center'
        )

        self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
            self.client.cursor, pg.mouse.get_pos()
        )

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
                self.client.resolution[1] * 5 / 12 + y * 60, 
                150, 50
            )
            for y in np.arange(6)
            for x in np.arange(3)
        ]
        self.box_hover = -1

        self.selected_bg = 0
        self.scroll_boxes = [
            pg.Rect(
                self.client.resolution[0] / 2 - (self.client.resolution[0] / 10 + 20) - 10,
                190, 20, 20
            ),
            pg.Rect(
                self.client.resolution[0] / 2 + (self.client.resolution[0] / 10 + 20) - 10,
                190, 20, 20
            )
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
            
                if self.scroll_boxes[0].collidepoint(event.pos):
                    self.selected_bg = (self.selected_bg - 1) % len(_Settings.BGS)
                if self.scroll_boxes[1].collidepoint(event.pos):
                    self.selected_bg = (self.selected_bg + 1) % len(_Settings.BGS)

            if event.type == pg.MOUSEMOTION:
                self.box_hover = -1
                for i, box in enumerate(self.boxes):
                    if box.collidepoint(event.pos):
                        self.box_hover = i
                
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
        
        self.client.displays[_Settings.DEFAULT_DISPLAY].fill(_Settings.LIGHT)
        self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            'character select',
            self.client.resolution[0] / 2,
            50,
            (0,0,0),
            25,
            style='center'
        )

        [pg.draw.rect(
            self.client.displays[_Settings.DEFAULT_DISPLAY], 
            lerp(_Settings.BLACK, _Settings.GOLD, float(i == self.box_hover)), 
            box
        ) for i, box in enumerate(self.boxes)]
        [self.client.font.render(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            fighter_name,
            *box.center,
            lerp(_Settings.GOLD, _Settings.BLACK, float(i == self.box_hover)),
            10,
            style='center'
        ) for i, (fighter_name, box) in enumerate(zip(_Settings.FIGHTERS, self.boxes))]

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
            sprite, accessory = get_splash(
                self.client.character_assets,
                self.client.accessory_assets,
                self.f1_selection,
                'right'
            )

            drawbox = sprite.get_rect()
            drawbox.centerx = 50 + self.client.resolution[0] / 8
            drawbox.centery = self.client.resolution[1] / 2

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
            sprite, accessory = get_splash(
                self.client.character_assets,
                self.client.accessory_assets,
                self.f2_selection,
                'left'
            )

            drawbox = sprite.get_rect()
            drawbox.centerx = self.client.resolution[0] * 7 / 8
            drawbox.centery = self.client.resolution[1] / 2

            self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                sprite,
                drawbox
            )
            if accessory is not None:
                self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                accessory,
                drawbox
            )

        self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
            self.client.bg_thumbs[_Settings.BGS[self.selected_bg]],
            (self.client.resolution[0] / 2 - self.client.resolution[0] / 10, 200 - self.client.resolution[1] / 10)
        )
        [pg.draw.rect(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            _Settings.GOLD,
            box
        ) for box in self.scroll_boxes]

        self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
            self.client.cursor, pg.mouse.get_pos()
        )

        return displays_to_render
        

class FightMenu(Menu):
    def __init__(self, client):
        super().__init__(client)

    def _load_meta_state(self):
        self.split_screen_countdown = 3

        self.winner = None
        self.win_banner_opacity = 0
        self.win_banner_delay = 0

        self.bullet_time = False
        self.bullet_time_elapsed = 0

    def _load_fight_data(self):
        self.bg = 'uwmain'
        self.f1 = Fighter()
        self.f2 = Fighter()

        self.f1.x = 300
        self.f2.x = self.client.resolution[0] - 300
        self.f2.facing = 'left'
    
    def reset_fight_data(self):
        self._load_meta_state()
        self._load_fight_data()

    def get_fight_data(self, select_menu):
        self.f1.fighter_type = select_menu.f1_selection
        self.f2.fighter_type = select_menu.f2_selection

        self.bg = _Settings.BGS[select_menu.selected_bg]

    def update(self, events: list[pg.Event], dt: float):
        if (
            self.split_screen_countdown <= 0 and 
            self.winner is None
        ):
            self.f1.input(self.client.keybinds['f1'], events)
        elif self.split_screen_countdown > 0:
            if self.transition_phase == 0:
                self.split_screen_countdown -= dt
        else:
            self.win_banner_opacity = np.minimum(self.win_banner_opacity + dt, 1)
            self.win_banner_delay += dt
            if self.win_banner_delay >= 5:
                self.goto = 'select'
                self.transition_phase = 1


        if self.bullet_time:
            self.bullet_time_elapsed -= dt
            if self.bullet_time_elapsed <= 0:
                self.bullet_time = False
            else:
                dt /= _Settings.BULLET_TIME_FACTOR

        if np.any([self.f1.update(dt), self.f2.update(dt)]):
            self.bullet_time = True
            self.bullet_time_elapsed = _Settings.BULLET_TIME
        self.f1.x = np.clip(self.f1.x, 0, self.client.resolution[0])
        self.f2.x = np.clip(self.f2.x, 0, self.client.resolution[0])
        
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

        if np.any([self.f1.attack.check_hit(self.f2), self.f2.attack.check_hit(self.f1)]):
            self.bullet_time = True
            self.bullet_time_elapsed = _Settings.BULLET_TIME
        
        if self.f1.gpa <= 0 and self.winner is None:
            self.winner = 'f2'
            self.f1.movement_inputs = []
            self.f1.direction_inputs = []
            self.f2.movement_inputs = []
            self.f2.direction_inputs = []
        if self.f2.gpa <= 0 and self.winner is None:
            self.winner = 'f1'
            self.f1.movement_inputs = []
            self.f1.direction_inputs = []
            self.f2.movement_inputs = []
            self.f2.direction_inputs = []

        return super().update(events, dt)
    
    def render(self):
        displays_to_render = super().render()

        self.client.displays[_Settings.DEFAULT_DISPLAY].fill((0,0,0))
        self.client.displays[_Settings.DEFAULT_DISPLAY].blit(self.client.bgs[self.bg], (0,0))

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

        if self.split_screen_countdown > 0:
            pg.draw.polygon(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                (0,0,0),
                [[0,0],
                 [0,self.client.resolution[1]],
                 [self.client.resolution[0] * 3 / 4, self.client.resolution[1] / 2]]
            )
            pg.draw.polygon(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                (0,0,0),
                [[self.client.resolution[0],0],
                 [self.client.resolution[0],self.client.resolution[1]],
                 [self.client.resolution[0] / 4, self.client.resolution[1] / 2]]
            )

            sprite, accessory = get_splash(
                self.client.character_assets,
                self.client.accessory_assets,
                self.f1.fighter_type,
                'right'
            )

            drawbox = sprite.get_rect()
            drawbox.centerx = 50 + self.client.resolution[0] / 8
            drawbox.centery = self.client.resolution[1] / 2

            self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                sprite,
                drawbox
            )
            if accessory is not None:
                self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                    accessory,
                    drawbox
                )

            sprite, accessory = get_splash(
                self.client.character_assets,
                self.client.accessory_assets,
                self.f2.fighter_type,
                'left'
            )

            drawbox = sprite.get_rect()
            drawbox.centerx = self.client.resolution[0] * 7 / 8
            drawbox.centery = self.client.resolution[1] / 2

            self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                sprite,
                drawbox
            )
            if accessory is not None:
                self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
                    accessory,
                    drawbox
                )
            
            self.client.font.render(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                'vs',
                *(np.array(self.client.resolution) / 2 + np.array([5,5])),
                (200,100,0),
                100,
                style='center'
            )
            self.client.font.render(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                'vs',
                *(np.array(self.client.resolution) / 2 - np.array([5,5])),
                (200,0,100),
                100,
                style='center'
            )
            self.client.font.render(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                'vs',
                *(np.array(self.client.resolution) / 2),
                (255,0,0),
                100,
                style='center'
            )
            
                
            self.client.font.render(
                self.client.displays[_Settings.DEFAULT_DISPLAY],
                f'{int(np.ceil(self.split_screen_countdown))}',
                *(np.array(self.client.resolution) / 2),
                (255,255,255),
                50,
                style='center'
            )

        if self.winner is not None:
            banner = pg.Surface((self.client.resolution[0], 100))
            banner.fill((0,0,0))
            self.client.font.render(
                banner,
                f'{self.winner} wins!',
                self.client.resolution[0] / 2, 50,
                _Settings.GOLD,
                50,
                style='center'
            )
            banner.set_alpha(self.win_banner_opacity * 255)
            self.client.displays[_Settings.DEFAULT_DISPLAY].blit(banner, (0, self.client.resolution[1] / 2 - 50))

        # self.client.displays[_Settings.DEFAULT_DISPLAY].blit(
        #     self.client.cursor, pg.mouse.get_pos()
        # )

        return displays_to_render

