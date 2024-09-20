import pygame as pg
import numpy as np

from ..util.transitions import transition_in, transition_out, TRANSITION_TIME


class _Settings:
    DEFAULT_DISPLAY = 'default'
    EFFECTS_DISPLAY = 'gaussian_blur'
    OVERLAY_DISPLAY = 'overlay'

    LOGO_SIZE = (400,400)

    GOLD = (255, 213, 0)
    BLACK = (10, 10, 10)
    GRAY = (150, 150, 150)
    LIGHT = (245, 245, 245)

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
    BULLET_TIME = 1


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
    def __init__(self, resolution: tuple):
        self.resolution = resolution
        self.goto : str = None
    
    def _on_transition(self):
        # 0 = none
        # 1 = fade out
        # 2 = black screen
        # 3 = fade in
        self.transition_phase = 2
        self.transition_time = 0

    def on_load(self):
        self._on_transition()
    
    def update(self, dt: float, events: list[pg.Event]):
        # transition logic
        if self.transition_phase > 0:
            self.transition_time += dt
            if self.transition_phase == 1 and self.transition_time > TRANSITION_TIME:
                return dict(exit=False, goto=self.goto)
            if self.transition_time > TRANSITION_TIME:
                self.transition_time = 0
                self.transition_phase = (self.transition_phase + 1) % 4
        
        return dict()
    
    def _render_overlay(self, display: pg.Surface):
        display.fill((0, 0, 0)) # fill transparency
        if self.transition_phase == 1: # fade out
            transition_out(display, self.transition_time)
        elif self.transition_phase == 2: # "black" screen
            display.fill(_Settings.BLACK)
        elif self.transition_phase == 3: # fade in
            transition_in(display, self.transition_time)

    def render(self, displays: dict[str, pg.Surface], font):
        # render overlay
        self._render_overlay(displays['overlay'])

        # render cursor
        displays['overlay'].blit(self.cursor, pg.mouse.get_pos()) # TODO))


class StartMenu(Menu):
    def __init__(self, resolution: tuple):
        # init Menu
        super().__init__(resolution)
        self._load_assets()
        self._load_button_data()
        
        # override
        self.goto = 'main'
    
    def _load_assets(self):
        # logo
        self.wlogo = pg.transform.scale(pg.image.load('./assets/ui/uw.png').convert_alpha(), _Settings.LOGO_SIZE)
        self.wlogo_rect = self.wlogo.get_rect()
        self.wlogo_rect.center = np.array(self.client.resolution) / 2 + np.array([0,-50])

    def _load_button_data(self):
        # title will fade in and out
        self.highlight = 1
        self.grow_dim = -1
        self.dim_speed = 1 / 2

    def on_load(self):
        super().on_load()

    def update(self, dt: float, events: list[pg.Event]):
        # handle transitions
        for event in events:
            if event.type == pg.MOUSEBUTTONUP and self.transition_phase == 0:
                # goto next menu
                self.transition_phase = 1
                self.transition_time = 0
                self.goto = 'main'
        
        # title highlighting
        self.highlight += self.dim_speed * self.grow_dim * dt
        if self.highlight >= 1:
            self.highlight = 1
            self.grow_dim = -1
        if self.highlight <= 0:
            self.highlight = 0
            self.grow_dim = 1

        return super().update(dt, events)

    def render(self, displays: dict[str, pg.Surface], font):
        # super() will render the overlay transitions if active
        super().render(displays)
        
        default = displays['default']
        default.fill(_Settings.LIGHT)

        # render the logo
        default.blit(self.wlogo, self.wlogo_rect)
        font.render(
            default,
            'the',
            (self.resolution[0] / 2, 50),
            [_Settings.BLACK, _Settings.GOLD],
            50,
            style='center',
            highlighting='010'
        )
        font.render(
            default,
            'experience',
            (self.resolution[0] / 2, self.resolution[1] - 150),
            [_Settings.BLACK, _Settings.GOLD],
            50,
            style='center',
            highlighting='0101010101'
        )
        
        # render the start button
        pg.draw.rect(
            self.client.displays[_Settings.DEFAULT_DISPLAY],
            _Settings.GRAY, 
            pg.Rect(0, self.resolution[1] - 75, self.resolution[0], 50)
        )
        font.render(
            default, 
            'press anywhere to continue', 
            (self.resolution[0] / 2, self.resolution[1] - 50) 
            (255, 255, 255), 
            20, 
            style='center', 
        )


class MainMenu(Menu):
    def __init__(self, resolution: tuple):
        super().__init__(resolution)
        self._setup_buttons()

        # override
        self.goto = 'select'
    
    def _setup_buttons(self):
        # buttons
        self.training_rect = pg.Rect(
            (0, 0),
            np.array(self.resolution) * 3 / 5
        )
        self.options_rect = pg.Rect(
            self.training_rect.bottomright,
            np.array(self.resolution) - np.array(self.training_rect.size)
        )
    
        # button styling data
        self.fade_speed = 1 / 0.25
        
        self.training_opacity = 1
        self.options_opacity = 1
    
    def on_load(self):
        super().on_load()

    def update(self, dt: float, events: list[pg.Event]):
        # button actions
        for event in events:
            if event.type == pg.MOUSEBUTTONUP:
                if self.training_rect.collidepoint(event.pos):
                    self.transition_phase = 1
                    self.transition_time = 0
        
        # hovering, button animations
        mpos = pg.mouse.get_pos()
        if self.training_rect.collidepoint(mpos):
            self.training_opacity = np.maximum(self.training_opacity - dt * self.fade_speed, 0)
        else:
            self.training_opacity = np.minimum(self.training_opacity + dt * self.fade_speed,1)
        
        if self.options_rect.collidepoint(mpos):
            self.options_opacity = np.maximum(self.options_opacity - dt * self.fade_speed, 0)
        else:
            self.options_opacity = np.minimum(self.options_opacity + dt * self.fade_speed, 1)

        return super().update(dt, events)

    def render(self, displays: dict[str, pg.Surface], font):
        super().render(displays, font)

        default = displays['default']
        default.fill(_Settings.LIGHT)

        # render buttons
        pg.draw.rect(
            default,
            lerp(_Settings.GOLD, _Settings.BLACK, self.training_opacity),
            self.training_rect
        )
        font.render(
            default,
            'training mode',
            self.training_rect.center,
            lerp(_Settings.BLACK, _Settings.GOLD, self.training_opacity),
            35, 
            style='center'
        )

        pg.draw.rect(
            default,
            lerp(_Settings.GOLD, _Settings.BLACK, self.options_opacity),
            self.options_rect
        )
        self.client.font.render(
            default,
            'options',
            self.options_rect.center,
            lerp(_Settings.BLACK, _Settings.GOLD, self.options_opacity),
            35, 
            style='center'
        )


class SelectMenu(Menu):
    def __init__(self, resolution: tuple):
        super().__init__(resolution)
        # self._load_assets()
        self._setup_variables()

        # override
        self.goto = 'fight'

    def on_load(self):
        super().on_load()
        self._reset_data()
    
    def _reset_data(self):
        # keep track of the geese players have selected
        self.selections = [None, None]
        self.currently_selecting = 2

        # split screen
        self.show_split_screen = False
        self.show_countdown = False
        self.split_screen_countdown = 3
        self.split_screen_sliding = 1
        self.split_screen_offset = self.resolution[0]
    
    def _setup_variables(self):
        self.reset_data()

        # character boxes
        self.boxes = [
            pg.Rect(
                self.resolution[0] / 2 + (x - 3 / 2) * 160 + 5, 
                self.resolution[1] * 5 / 12 + y * 60, 
                150, 50
            )
            for y in np.arange(6)
            for x in np.arange(3)
        ]
        self.box_hover = -1

        # bg boxes
        self.selected_bg = 0
        self.scroll_boxes = [
            pg.Rect(
                self.resolution[0] / 2 - (self.resolution[0] / 10 + 20) - 10,
                190, 20, 20
            ),
            pg.Rect(
                self.resolution[0] / 2 + (self.resolution[0] / 10 + 20) - 10,
                190, 20, 20
            )
        ]

    def update(self, dt: float, events: list[pg.Event]):
        for event in events:
            if event.type == pg.MOUSEBUTTONUP:
                # check player selecting a goose
                for i, box in enumerate(self.boxes):
                    if box.collidepoint(event.pos):
                        if self.currently_selecting < len(self.selections):
                            self.selections[self.currently_selecting] = _Settings.FIGHTERS[i]
                            self.currently_selecting = 2

                # check player select bg
                if self.scroll_boxes[0].collidepoint(event.pos):
                    self.selected_bg = (self.selected_bg - 1) % len(_Settings.BGS)
                if self.scroll_boxes[1].collidepoint(event.pos):
                    self.selected_bg = (self.selected_bg + 1) % len(_Settings.BGS)

            # check mouse hover
            if event.type == pg.MOUSEMOTION:
                self.box_hover = -1
                for i, box in enumerate(self.boxes):
                    if box.collidepoint(event.pos):
                        self.box_hover = i
            
            if event.type == pg.KEYDOWN:
                # check confirm start fight
                self.show_split_screen = (
                    event.key == pg.K_RETURN and 
                    all([selection is not None for selection in self.selections])
                ) or self.show_split_screen

                # check re-select for players
                if event.key == pg.K_1:
                    self.currently_selecting = 0
                if event.key == pg.K_2:
                    self.currently_selecting = 1
        
        if self.show_countdown: # countdown
            self.split_screen_countdown -= dt
            if self.split_screen_countdown < 0:
                self.transition_phase = 1
        elif self.show_split_screen: # split screen
            self.split_screen_sliding -= dt
            if self.split_screen_sliding < 0:
                self.show_countdown = True
                self.split_screen_offset = 0
            else:
                self.split_screen_offset -= self.client.resolution[0] * dt

        return super().update(dt, events)

    def render(self, displays: dict[str, pg.Surface], font):
        super().render(displays, font)
        
        default = displays[_Settings.DEFAULT_DISPLAY]
        default.fill(_Settings.LIGHT)

        # title
        font.render(
            default,
            'character select',
            (self.resolution[0] / 2, 50),
            _Settings.BLACK,
            25,
            style='center'
        )

        # render goose boxes and goose names
        for i, (fighter_name, box) in enumerate(zip(_Settings.FIGHTERS, self.boxes)):
            pg.draw.rect(
                default, 
                lerp(_Settings.BLACK, _Settings.GOLD, float(i == self.box_hover)), 
                box
            )
            font.render(
                default,
                fighter_name,
                box.center,
                lerp(_Settings.GOLD, _Settings.BLACK, float(i == self.box_hover)),
                10,
                style='center'
            )

        # render border around the player who is currently selecting their character
        if self.currently_selecting == 0:
            pg.draw.rect(
                default,
                _Settings.GOLD,
                pg.Rect(
                    50, 50,
                    self.client.resolution[0] / 4,
                    self.client.resolution[1] - 100
                ),
                10
            )
        elif self.currently_selecting == 1:
            pg.draw.rect(
                default,
                _Settings.GOLD,
                pg.Rect(
                    self.client.resolution[0] * 3 / 4 - 50, 
                    50,
                    self.client.resolution[0] / 4,
                    self.client.resolution[1] - 100,
                ),
                10
            )
        
        # render goose sprite for player 1
        if self.selections[0] is not None:
            sprite, accessory = get_splash( # TODO
                self.client.character_assets,
                self.client.accessory_assets,
                self.selections[0],
                'right'
            )

            drawbox = sprite.get_rect()
            drawbox.centerx = 50 + self.resolution[0] / 8
            drawbox.centery = self.resolution[1] / 2

            default.blit(
                sprite,
                drawbox
            )
            if accessory is not None:
                default.blit(
                accessory,
                drawbox
            )
        
        # render goose sprite for player 2
        if self.f2_selection is not None:
            sprite, accessory = get_splash( # TODO
                self.client.character_assets,
                self.client.accessory_assets,
                self.selections[1],
                'left'
            )

            drawbox = sprite.get_rect()
            drawbox.centerx = self.resolution[0] * 7 / 8 - 50
            drawbox.centery = self.resolution[1] / 2

            default.blit(
                sprite,
                drawbox
            )
            if accessory is not None:
                default.blit(
                accessory,
                drawbox
            )

        # render the selected bg
        default.blit(
            self.client.bg_thumbs[_Settings.BGS[self.selected_bg]], # TODO
            (self.resolution[0] / 2 - self.resolution[0] / 10, 200 - self.resolution[1] / 10)
        )
        # render bg thumbnails
        [pg.draw.rect(
            default,
            _Settings.GOLD,
            box
        ) for box in self.scroll_boxes]

        # render split screen
        if self.show_split_screen:
            pg.draw.polygon(
                default,
                _Settings.BLACK,
                -np.array([self.split_screen_offset, 0]) + np.array([
                    [0, 0],
                    [0, self.resolution[1]],
                    [self.resolution[0] * 3 / 4, self.resolution[1] / 2]
                ])
            )
            pg.draw.polygon(
                default,
                _Settings.BLACK,
                np.array([self.split_screen_offset, 0]) + np.array([
                    [self.resolution[0], 0],
                    self.resolution,
                    [self.resolution[0] / 4, self.resolution[1] / 2]
                ])
            )

            # render countdown
            if self.show_countdown:
                # render player 1 closeup
                sprite, accessory = get_splash( # TODO
                    self.client.character_assets,
                    self.client.accessory_assets,
                    self.selections[0],
                    'right'
                )

                drawbox = sprite.get_rect()
                drawbox.centerx = 50 + self.resolution[0] / 8
                drawbox.centery = self.resolution[1] / 2

                default.blit(sprite, drawbox)
                if accessory is not None:
                    default.blit(accessory, drawbox)

                # render player 2 closeup
                sprite, accessory = get_splash( # TODO
                    self.client.character_assets,
                    self.client.accessory_assets,
                    self.selections[1],
                    'left'
                )

                drawbox = sprite.get_rect()
                drawbox.centerx = self.resolution[0] * 7 / 8 - 50
                drawbox.centery = self.resolution[1] / 2

                default.blit(sprite, drawbox)
                if accessory is not None:
                    default.blit(accessory, drawbox)
                
                # render text
                self.client.font.render(
                    default,
                    'vs',
                    np.array(self.resolution) / 2 + np.array([5,5]),
                    (200, 100, 0), # TODO
                    100,
                    style='center'
                )
                self.client.font.render(
                    default,
                    'vs',
                    np.array(self.resolution) / 2 - np.array([5,5]),
                    (200, 0, 100), # TODO
                    100,
                    style='center'
                )
                self.client.font.render(
                    self.client.displays[_Settings.DEFAULT_DISPLAY],
                    'vs',
                    np.array(self.client.resolution) / 2,
                    (255,0,0), # TODO
                    100,
                    style='center'
                )
        

class FightMenu(Menu):
    def __init__(self, client):
        super().__init__(client)

        from ..fight import Goose
        self.goose1 = Goose()
        self.goose2 = Goose()
    
    def _reset_data(self):
        # countdown
        self.countdown = 3

        # winner
        self.winner = None
        self.win_banner_opacity = 0
        self.win_banner_delay = 0

        # bullet time 
        self.bullet_time = False
        self.bullet_time_elapsed = 0

        # zoom and shake
        self.zoom_anchor = np.zeros(2)
        self.zoom_amt = 1
        self.shake_anchor = 0
        
        # bg
        self.bg = 'uwmain'

        # player entities
        self.goose1.reset('right') # TODO
        self.goose2.reset('left')

    def on_load(self):
        super().on_load()

        self._reset_data()

    def update(self, dt: float, events: list[pg.Event]):
        if self.winner is not None: # show winner
            self.win_banner_opacity = min(self.win_banner_opacity + dt, 1)
            self.win_banner_delay += dt
            if self.win_banner_delay >= 5:
                self.goto = 'select'
                self.transition_phase = 1
        elif self.countdown > 0: # countdown
            if self.transition_phase == 0:
                self.countdown -= dt
        else: # input
            self.goose1.input(self.client.keybinds[0], events) # TODO
            self.goose2.input(self.client.keybinds[1], events) 

        # bullet time
        if self.bullet_time:
            self.bullet_time_elapsed -= dt
            # screen shake
            # self.zoom_amt += dt / 2
            # if self.bullet_time_elapsed <= 0:
            #     self.bullet_time = False
            #     self.zoom_amt = 1
            #     self.shake_anchor = np.zeros(2)
            if self.bullet_time_elapsed <= 0:
                self.bullet_time = False
            else:
                dt /= _Settings.BULLET_TIME_FACTOR

        # check colisions
        self.goose1.update(dt) # TODO prevent movement outside of screen boundary
        self.goose2.update(dt)
        hit1 = self.goose1.check_collisions()
        hit2 = self.goose2.check_collisions()

        # enter bullet time
        if hit1 is not None or hit2 is not None:
            self.bullet_time = True
            self.bullet_time_elapsed = _Settings.BULLET_TIME
            # self.zoom_anchor = hit1 if hit1 is not None else hit2
        
        # animate geese
        self.goose1.animate( # TODO
            self.client.character_assets, 
            self.client.accessory_assets,
            self.client.attack_assets,
            dt
        )
        self.goose2.animate( 
            self.client.character_assets,
            self.client.accessory_assets,
            self.client.attack_assets,
            dt
        )
        
        # check winner
        if self.goose1.gpa <= 0 and self.winner is None:
            self.winner = 'goose2'
        if self.goose2.gpa <= 0 and self.winner is None:
            self.winner = 'goose1'
        if self.winner is not None:
            # reset inputs
            self.goose1.movement_inputs = []
            self.goose1.direction_inputs = []
            self.goose2.movement_inputs = []
            self.goose2.direction_inputs = []

        return super().update(dt, events)
    
    def render(self, displays: dict[str, pg.Surface], font):
        super().render(displays, font)

        default = displays['default']
        gaussian_blur = displays['gaussian_blur']

        # render bg
        default.blit(self.client.bgs[self.bg], (0,0))

        # render geese
        gaussian_blur.fill((0, 0, 0))
        self.goose1.render(default, gaussian_blur) 
        self.goose2.render(default, gaussian_blur)

        # render gpa
        pg.draw.rect(
            default,
            (255,255,255),
            pg.Rect(75, 35, 200, 50)
        )
        pg.draw.rect(
            default,
            (255,255,255),
            pg.Rect(self.resolution[0] - 275, 35, 200, 50)
        )
        font.render(
            default,
            f'gpa {round(self.goose1.gpa, 2)}',
            175, 75,
            [_Settings.BLACK, lerp(np.array([255,0,0]), np.array([0,255,0]), self.goose1.gpa / 4)],
            30,
            style='center',
            highlighting='00001111'
        )
        font.render(
            default,
            f'gpa {round(self.f2.gpa, 2)}',
            (self.resolution[0] - 175, 75),
            [_Settings.BLACK, lerp(np.array([255,0,0]), np.array([0,255,0]), self.goose2.gpa / 4)],
            30,
            style='center',
            highlighting='00001111'
        )
        
        # render countdown
        if self.countdown > 0:                
            font.render(
                default,
                f'{int(np.ceil(self.countdown))}',
                np.array(self.client.resolution) / 2,
                (255,255,255),
                100,
                style='center',
            )

        # render winner
        if self.winner is not None:
            banner = pg.Surface((self.client.resolution[0], 200))
            banner.fill((0,0,0))
            font.render(
                banner,
                f'{self.winner} wins!',
                (self.client.resolution[0] / 2, banner.get_height() / 2),
                _Settings.GOLD,
                50,
                style='center'
            )
            banner.set_alpha(self.win_banner_opacity * 255)
            default.blit(banner, (0, self.client.resolution[1] / 2 - banner.get_height() / 2))

        # if self.zoom_amt > 1:
        #     zoomed = pg.Surface((np.array(default.get_size()) / self.zoom_amt).astype(int))
        #     xoffset = np.clip(
        #         self.zoom_anchor[0] - zoomed.get_width() / 2,
        #         a_min=0,
        #         a_max=default.get_width() - zoomed.get_width()
        #     )
        #     yoffset = np.clip(
        #         self.zoom_anchor[1] - zoomed.get_height() / 2,
        #         a_min=0,
        #         a_max=default.get_height() - zoomed.get_height()
        #     )
        #     zoomed.blit(default, (-xoffset,-yoffset))
        #     default = pg.transform.scale(zoomed, default.get_size())

        #     zoomed = pg.Surface((np.array(effects.get_size()) / self.zoom_amt).astype(int))
        #     xoffset = np.clip(
        #         self.zoom_anchor[0] - zoomed.get_width() / 2,
        #         a_min=0,
        #         a_max=effects.get_width() - zoomed.get_width()
        #     )
        #     yoffset = np.clip(
        #         self.zoom_anchor[1] - zoomed.get_height() / 2,
        #         a_min=0,
        #         a_max=effects.get_height() - zoomed.get_height()
        #     )
        #     zoomed.blit(effects, (-xoffset,-yoffset))
        #     effects = pg.transform.scale(zoomed, effects.get_size())


