import pygame as pg
import numpy as np

from ..util import lerp


class _Settings:
    TRANSITION_TIME = 0.5

    def transition_out(overlay: pg.Surface, transition_time: float):
        width, height = overlay.get_size()
        transition_progress = 1.25 * transition_time / _Settings.TRANSITION_TIME
        topleft = [0, 0]
        bottomleft = [0, height]
        topright = [transition_progress * width , 0]
        bottomright = [transition_progress * width - 200, height]
        points = [
            topleft, bottomleft, bottomright, topright
        ]
        overlay.fill((0, 0, 0))
        pg.draw.polygon(overlay, (10, 10, 10), points)

    def transition_in(overlay: pg.Surface, transition_time: float):
        width, height = overlay.get_size()
        transition_progress = 1.25 * transition_time / _Settings.TRANSITION_TIME
        topleft = [transition_progress * width, 0]
        bottomleft = [transition_progress * width - 200, height]
        topright = [width, 0]
        bottomright = [width, height]
        points = [
            topleft, bottomleft, bottomright, topright
        ]
        overlay.fill((0, 0, 0))
        pg.draw.polygon(overlay, (10, 10, 10), points)
    

    GOLD = (255, 213, 0)
    BLACK = (10, 10, 10)
    GRAY = (150, 150, 150)
    LIGHT = (245, 245, 245)

    FIGHTERS = [
        'amath',
        'pmath',
        # 'csse',
        'ece',
        'mechtron',
        'civarch',
        'opto',
        'pharm',
        'kine',
        'physchem',
        'plant',
        'psych',
    ]
    
    BACKGROUNDS = [
        'uwmain',
        'dp',
        'm3',
        'e7',
        'qnc',
        'exp',
        'hh',
        'ev3'
    ]

    BULLET_TIME_FACTOR = 1
    BULLET_TIME = 1
    END_FIGHT_TIME_FACTOR = 10


def _get_splash(
    major: str, facing: str,
    character_assets: dict, 
    accessory_assets: dict,
) -> tuple[pg.Surface, pg.Surface]:
    goose_sprite = pg.transform.scale_by(character_assets[major]['idle'][facing][0], 2)
    goose_sprite.set_colorkey((255, 0, 0))
    accessory = accessory_assets.get(major, None)
    if accessory is None:
        return goose_sprite, None
    accessory_sprite = pg.transform.scale_by(accessory[facing], 2)
    accessory_sprite.set_colorkey((255, 0, 0))

    return goose_sprite, accessory_sprite


import pygame as pg


class Menu:
    def __init__(self, client):
        self.resolution = client.resolution
        self.goto : str = None
    
    def _on_transition(self):
        # 0 = none
        # 1 = fade out
        # 2 = black screen
        # 3 = fade in
        self.transition_phase = 2
        self.transition_time = 0

    def on_load(self, client):
        self._on_transition()
    
    def update(self, client):
        # transition logic
        if self.transition_phase > 0:
            self.transition_time += client.dt
            if self.transition_phase == 1 and self.transition_time > _Settings.TRANSITION_TIME:
                return dict(exit=False, goto=self.goto)
            if self.transition_time > _Settings.TRANSITION_TIME:
                self.transition_time = 0
                self.transition_phase = (self.transition_phase + 1) % 4
        
        return dict()
    
    def _render_overlay(self, display: pg.Surface):
        if self.transition_phase == 1: # fade out
            _Settings.transition_out(display, self.transition_time)
        elif self.transition_phase == 2: # "black" screen
            display.fill(_Settings.BLACK)
        elif self.transition_phase == 3: # fade in
            _Settings.transition_in(display, self.transition_time)

    def render(self, client):
        # render overlay
        self._render_overlay(client.displays['overlay'])

        # fps
        client.font.render(
            client.displays['overlay'],
            f'{int(client.clock.get_fps())}',
            (10, 10),
            _Settings.LIGHT,
            20,
            style='topleft'
        )


class StartMenu(Menu):
    def __init__(self, client):
        # init Menu
        super().__init__(client)
        self._load_banner_data(client.font)
        
        # override
        self.goto = 'main'

    def _load_banner_data(self, font):
        # title will fade in and out
        self.banner = pg.Surface((self.resolution[0], 50))
        self.banner.fill(_Settings.GRAY)
        font.render(
            self.banner, 
            'press anywhere to continue', 
            (self.resolution[0] / 2, 25),
            (255, 255, 255), 
            20, 
            style='center', 
        )

        self.highlight = 1
        self.dim_direction = -1
        self.dim_speed = 1 / 2

    def on_load(self, client):
        super().on_load(client)

    def update(self, client):
        # handle transitions
        for event in client.events:
            if event.type == pg.MOUSEBUTTONUP and self.transition_phase == 0:
                # goto next menu
                self.transition_phase = 1
                self.transition_time = 0
                self.goto = 'main'
        
        # title highlighting
        self.highlight += self.dim_speed * self.dim_direction * client.dt
        if self.highlight >= 1:
            self.highlight = 1
            self.dim_direction = -1
        if self.highlight <= 0:
            self.highlight = 0
            self.dim_direction = 1

        return super().update(client)

    def render(self, client):
        default = client.displays['default']
        default.fill(_Settings.LIGHT)

        # render the logo
        default.blit(client.assets.uw_logo, np.array(self.resolution) / 2 - np.array(client.assets.uw_logo.get_size()) / 2 - np.array([0, 50]))
        client.font.render(
            default,
            'the',
            (self.resolution[0] / 2, 50),
            [_Settings.BLACK, _Settings.GOLD],
            50,
            style='center',
            highlighting='101'
        )
        client.font.render(
            default,
            'experience',
            (self.resolution[0] / 2, self.resolution[1] - 150),
            [_Settings.BLACK, _Settings.GOLD],
            50,
            style='center',
            highlighting='0101010101'
        )
        
        # render the banner
        self.banner.set_alpha(int(self.highlight * 255))
        default.blit(self.banner, (0, self.resolution[1] - 75))

        super().render(client)


class MainMenu(Menu):
    def __init__(self, client):
        super().__init__(client)
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
    
    def on_load(self, client):
        super().on_load(client)

    def update(self, client):
        # button actions
        for event in client.events:
            if event.type == pg.MOUSEBUTTONUP:
                if self.training_rect.collidepoint(event.pos):
                    self.transition_phase = 1
                    self.transition_time = 0
        
        # hovering, button animations
        mpos = pg.mouse.get_pos()
        if self.training_rect.collidepoint(mpos):
            self.training_opacity = np.maximum(self.training_opacity - client.dt * self.fade_speed, 0)
        else:
            self.training_opacity = np.minimum(self.training_opacity + client.dt * self.fade_speed,1)
        
        if self.options_rect.collidepoint(mpos):
            self.options_opacity = np.maximum(self.options_opacity - client.dt * self.fade_speed, 0)
        else:
            self.options_opacity = np.minimum(self.options_opacity + client.dt * self.fade_speed, 1)

        return super().update(client)

    def render(self, client):
        default = client.displays['default']
        default.fill(_Settings.LIGHT)

        # render buttons
        pg.draw.rect(
            default,
            lerp(_Settings.GOLD, _Settings.BLACK, self.training_opacity),
            self.training_rect
        )
        client.font.render(
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
        client.font.render(
            default,
            'options',
            self.options_rect.center,
            lerp(_Settings.BLACK, _Settings.GOLD, self.options_opacity),
            35, 
            style='center'
        )

        super().render(client)


class SelectMenu(Menu):
    def __init__(self, client):
        super().__init__(client)
        # self._load_assets()
        self._setup_variables()

        # override
        self.goto = 'fight'
    
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
        self._reset_data()

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
        self.selected_background = 0
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

    def on_load(self, client):
        super().on_load(client)
        self._reset_data()

    def update(self, client):
        for event in client.events:
            if event.type == pg.MOUSEBUTTONUP:
                # check player selecting a goose
                for i, box in enumerate(self.boxes):
                    if box.collidepoint(event.pos):
                        if self.currently_selecting < len(self.selections):
                            self.selections[self.currently_selecting] = _Settings.FIGHTERS[i]
                            self.currently_selecting = 2

                # check player select bg
                if self.scroll_boxes[0].collidepoint(event.pos):
                    self.selected_background = (self.selected_background - 1) % len(_Settings.BACKGROUNDS)
                if self.scroll_boxes[1].collidepoint(event.pos):
                    self.selected_background = (self.selected_background + 1) % len(_Settings.BACKGROUNDS)

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
            self.split_screen_countdown -= client.dt
            if self.split_screen_countdown < 0:
                self.transition_phase = 1
        elif self.show_split_screen: # split screen
            self.split_screen_sliding -= client.dt
            if self.split_screen_sliding < 0:
                self.show_countdown = True
                self.split_screen_offset = 0
            else:
                self.split_screen_offset -= self.resolution[0] * client.dt

        return super().update(client)

    def render(self, client):
        default = client.displays['default']
        default.fill(_Settings.LIGHT)

        # title
        client.font.render(
            default,
            'character select',
            (self.resolution[0] / 2, 50),
            _Settings.BLACK,
            25,
            style='center'
        )

        # render goose boxes and goose names
        for i, (fighter_name, box) in enumerate(zip(_Settings.FIGHTERS, self.boxes)):
            pg.draw.rect(default, lerp(_Settings.BLACK, _Settings.GOLD, float(i == self.box_hover)), box)
            client.font.render(
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
                pg.Rect(50, 50, self.resolution[0] / 4, self.resolution[1] - 100),
                10
            )
        elif self.currently_selecting == 1:
            pg.draw.rect(
                default,
                _Settings.GOLD,
                pg.Rect(self.resolution[0] * 3 / 4 - 50, 50, self.resolution[0] / 4, self.resolution[1] - 100),
                10
            )
        
        # render goose sprite for player 1
        if self.selections[0] is not None:
            goose1_sprite, goose1_accessory = _get_splash(
                self.selections[0], 'right',
                client.assets.character_assets,
                client.assets.accessory_assets
            )

            goose1_drawbox = goose1_sprite.get_rect()
            goose1_drawbox.centerx = 50 + self.resolution[0] / 8
            goose1_drawbox.centery = self.resolution[1] / 2

            default.blit(goose1_sprite, goose1_drawbox)
            if goose1_accessory is not None:
                accessory_drawbox = goose1_accessory.get_rect()
                accessory_drawbox.bottomright = goose1_drawbox.center
                default.blit(goose1_accessory, accessory_drawbox)
        
        # render goose sprite for player 2
        if self.selections[1] is not None:
            goose2_sprite, goose2_accessory = _get_splash(
                self.selections[1], 'left',
                client.assets.character_assets,
                client.assets.accessory_assets
            )

            goose2_drawbox = goose2_sprite.get_rect()
            goose2_drawbox.centerx = self.resolution[0] * 7 / 8 - 50
            goose2_drawbox.centery = self.resolution[1] / 2

            default.blit(goose2_sprite, goose2_drawbox)
            if goose2_accessory is not None:
                accessory_drawbox = goose2_accessory.get_rect()
                accessory_drawbox.bottomleft = goose2_drawbox.center
                default.blit(goose2_accessory, accessory_drawbox)

        # render the selected bg
        selected_bg = client.assets.background_thumbnails[_Settings.BACKGROUNDS[self.selected_background]]
        rect = selected_bg.get_rect()
        rect.center = (self.resolution[0] / 2, 200)
        default.blit(selected_bg, rect)
        # render scroll boxes
        for i, box in enumerate(self.scroll_boxes):
            pg.draw.rect(default, _Settings.GOLD, box)
            angle_offset = (i + 1) * np.pi
            angles = 2 * np.pi / 3 * np.arange(3) + angle_offset
            vertices = np.array(box.center) + box.width / 3 * np.column_stack([np.cos(angles), np.sin(angles)])
            pg.draw.polygon(default, _Settings.BLACK, vertices)

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
                default.blit(goose1_sprite, goose1_drawbox)
                if goose1_accessory is not None:
                    accessory_drawbox = goose1_accessory.get_rect()
                    accessory_drawbox.bottomright = goose1_drawbox.center
                    default.blit(goose1_accessory, accessory_drawbox)

                # render player 2 closeup
                default.blit(goose2_sprite, goose2_drawbox)
                if goose2_accessory is not None:
                    accessory_drawbox = goose2_accessory.get_rect()
                    accessory_drawbox.bottomleft = goose2_drawbox.center
                    default.blit(goose2_accessory, accessory_drawbox)
                
                # render text
                client.font.render(
                    default,
                    'vs',
                    np.array(self.resolution) / 2,
                    _Settings.LIGHT,
                    100,
                    style='center'
                )
        
        super().render(client)
        

class FightMenu(Menu):
    def __init__(self, client):
        super().__init__(client)

        from ..fight import Goose
        self.goose1 = Goose(dict(major=None, x=100, facing='right'))
        self.goose2 = Goose(dict(major=None, x=self.resolution[0] - 100, facing='left'))
    
    def _reset_data(self, geese_data: list[dict], background: str):
        # countdown
        self.countdown = 3

        # loser
        self.loser = None
        self.lose_banner_opacity = 0
        self.lose_banner_delay = 0

        # bullet time 
        self.bullet_time = 0
        
        # bg
        self.background = _Settings.BACKGROUNDS[background]

        # player entities
        self.goose1.reset_state(geese_data[0])
        self.goose2.reset_state(geese_data[1])

    def on_load(self, client):
        super().on_load(client)

        self._reset_data(**client.get_fight_data())

    def update(self, client):
        if self.loser is not None: # show loser
            self.goose1.reset_input()
            self.goose2.reset_input()
            self.lose_banner_opacity = min(self.lose_banner_opacity + client.dt, 1)
            self.lose_banner_delay += client.dt
            if self.lose_banner_delay >= 5:
                self.goto = 'select'
                self.transition_phase = 1
        elif self.countdown > 0: # countdown
            if self.transition_phase == 0:
                self.countdown -= client.dt
        else: # input
            self.goose1.input(client.events, client.assets.keybinds[0])
            # self.goose2.input(events, kwargs['assets'].keybinds[1]) 

        # bullet time
        if self.loser is not None and self.transition_phase == 0:
            client.dt /= _Settings.END_FIGHT_TIME_FACTOR
        elif self.bullet_time > 0:
            self.bullet_time -= client.dt
            client.dt /= _Settings.BULLET_TIME_FACTOR

        # check colisions
        self.goose1.update(client.dt, self.resolution[0]) 
        self.goose2.update(client.dt, self.resolution[0])
        hit1 = self.goose1.check_collide(self.goose2, client.assets.attack_damages, client.assets.attack_knockbacks)
        hit2 = self.goose2.check_collide(self.goose1, client.assets.attack_damages, client.assets.attack_knockbacks)

        # enter bullet time
        if hit1 or hit2:
            self.bullet_time = _Settings.BULLET_TIME
        
        # animate geese
        self.goose1.animate(
            client.dt,
            client.assets.character_assets, 
            client.assets.accessory_assets,
            client.assets.attack_assets,
        )
        self.goose2.animate(
            client.dt, 
            client.assets.character_assets,
            client.assets.accessory_assets,
            client.assets.attack_assets,
        )
        
        # check winner
        if self.goose1.gpa <= 0 and self.loser is None:
            self.loser = 'goose 1'
        if self.goose2.gpa <= 0 and self.loser is None:
            self.loser = 'goose 2'

        return super().update(client)
    
    def render(self, client):
        default = client.displays['default']
        gaussian_blur = client.displays['gaussian_blur']

        # render bg
        default.blit(client.assets.backgrounds[self.background], (0, 0))

        # render geese
        self.goose1.render(default, gaussian_blur) 
        self.goose2.render(default, gaussian_blur)

        # render gpa
        font_size = 30
        margin = 20
        padding = 10
        text = f'gpa {round(self.goose1.gpa, 2)}'
        rect = pg.Rect(margin, margin, 2 * padding + client.font.text_width(text, font_size), 2 * padding + client.font.char_height(font_size))
        pg.draw.rect(default, _Settings.LIGHT, rect)
        client.font.render(
            default, 
            text, 
            rect.center,
            [_Settings.BLACK, lerp(np.array([255,0,0]), np.array([0,255,0]), self.goose1.gpa / 4)],
            font_size,
            style='center',
            highlighting='00001111'
        )
        text = f'gpa {round(self.goose2.gpa, 2)}'
        rect = pg.Rect(0, margin, 2 * padding + client.font.text_width(text, font_size), 2 * padding + client.font.char_height(font_size))
        rect.right = self.resolution[0] - margin
        pg.draw.rect(default, _Settings.LIGHT, rect)
        client.font.render(
            default,
            text,
            rect.center,
            [_Settings.BLACK, lerp(np.array([255,0,0]), np.array([0,255,0]), self.goose2.gpa / 4)],
            font_size,
            style='center',
            highlighting='00001111'
        )
        
        # render countdown
        if self.countdown > 0:                
            client.font.render(
                default,
                f'{int(np.ceil(self.countdown))}',
                np.array(self.resolution) / 2,
                (255,255,255),
                100,
                style='center',
            )

        # render winner
        if self.loser is not None:
            banner = pg.Surface((self.resolution[0], 200))
            banner.fill((0,0,0))
            client.font.render(
                banner,
                f'{self.loser} expelled',
                (self.resolution[0] / 2, banner.get_height() / 2),
                _Settings.GOLD,
                50,
                style='center'
            )
            banner.set_alpha(self.lose_banner_opacity * 255)
            default.blit(banner, (0, self.resolution[1] / 2 - banner.get_height() / 2))

        super().render(client)
