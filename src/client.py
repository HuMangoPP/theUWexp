import numpy as np
import pygame as pg
import moderngl as mgl

from .pymgl import GraphicsEngine
from .pyfont import Font

from .util import (
    load_keybinds, 
    load_backgrounds,
    load_character_assets, 
    load_accessory_assets,
    load_attack_assets, 
)

from .menus import *


class _Settings:
    RESOLUTION = (1280,720)
    MENU_MAP = dict(start=0, main=1, select=2, fight=3)


class Client:
    def __init__(self):
        self._pg_init()
        self.assets = self.Assets('./assets/', self.resolution)
        self._setup_menus()
    
    def _pg_init(self):
        # init
        pg.init()

        # get window and ctx
        self.resolution = _Settings.RESOLUTION
        pg.display.set_mode(self.resolution, pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = (
            mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        )
        pg.display.set_caption('The UW Experience')

        # get graphics engine, font, and displays
        self.graphics_engine = GraphicsEngine(self.ctx, self.resolution, './src')
        self.font = Font('./src/pyfont/font.png')
        self.displays = dict(
            default=pg.Surface(self.resolution),
            gaussian_blur=pg.Surface(self.resolution),
            overlay=pg.Surface(self.resolution)
        )

        # clock
        self.clock = pg.time.Clock()
        self.dt = 0
        
        # events
        self.events = []

    def _setup_menus(self):
        # menus
        self.menus : list[Menu] = [
            StartMenu(self), 
            MainMenu(self),
            SelectMenu(self),
            FightMenu(self)
        ]
        self.current_menu = 0
    
    def get_fight_data(self):
        select_menu = self.menus[_Settings.MENU_MAP['select']]
        return dict(
            geese_data=[
                dict(major=select_menu.selections[0], x=100, facing='right'),
                dict(major=select_menu.selections[1], x=self.resolution[0] - 100, facing='left')
            ],
            background=select_menu.selected_background
        )

    def update(self):
        # quit client
        for event in self.events:
            if event.type == pg.QUIT:
                return dict(exit=True)
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return dict(exit=True)
        
        # not done loading assets
        if not self.assets.finished_loading:
            self.assets.load_assets()
            self.menus[self.current_menu].transition_time = 0
        
        # menu update
        return self.menus[self.current_menu].update(self)

    def render(self):
        self.ctx.clear(0.08, 0.1, 0.2)

        # render to pg surface
        [display.fill((0, 0, 0)) for display in self.displays.values()]
        self.menus[self.current_menu].render(self)

        # not done loading assets
        if not self.assets.finished_loading:
            font_size = 25
            num_dots = (self.assets.progress // 5) % 3 + 1
            self.font.render(
                self.displays['overlay'],
                "loading",
                np.array(self.resolution) / 2 + np.array([-font_size * 1.5, 0]),
                (255, 255, 255),
                font_size,
                style='center'
            )
            self.font.render(
                self.displays['overlay'],
                "." * num_dots,
                np.array(self.resolution) / 2 + np.array([font_size * 2, -self.font.char_height(font_size) / 2]),
                (255, 255, 255),
                font_size,
                style='topleft'
            )
        
        # render cursor
        self.displays['overlay'].blit(self.assets.cursor, pg.mouse.get_pos())

        # render using graphics engine to screen
        [self.graphics_engine.render(
            display, 
            shader=shader
        ) for shader, display in self.displays.items()]
    
    def run(self):
        # on load
        self.menus[self.current_menu].on_load(self)
        while True:
            # update
            self.dt = self.clock.get_time() / 1000
            self.clock.tick()
            self.events = pg.event.get()
            exit_status = self.update()
            if exit_status:
                if exit_status['exit']:
                    pg.quit()
                    return
                else: # menu transitions
                    self.current_menu = _Settings.MENU_MAP[exit_status['goto']]
                    self.menus[self.current_menu].on_load(self)
            
            # render
            self.render()
            pg.display.flip()

    class Assets:
        def __init__(self, path: str, resolution: tuple):
            self.path = path

            # progress
            self.finished_loading = False
            self.progress = 0

            # cursor and logo
            pg.mouse.set_visible(False)
            self.cursor = pg.image.load(f'{self.path}/ui/cursor.png').convert()
            self.cursor.set_colorkey((0,0,0))
            self.uw_logo = pg.transform.scale(pg.image.load(f'{self.path}/ui/uw.png').convert_alpha(), (400, 400))
            
            # keybinds
            self.keybinds = [
                {pg.key.key_code(key): action for action, key in keybinds.items()}
                for keybinds in load_keybinds(f'{self.path}/settings/keybinds.json')
            ]

            # art assets
            self.backgrounds, self.background_thumbnails = load_backgrounds(f'{self.path}/backgrounds', resolution)
            self.character_assets = {}
            self.attack_assets = {}

        def load_assets(self):
            # load characters
            goose_major, sprites = load_character_assets(f'{self.path}/new_geese', self.progress, scale=3)
            if sprites is not None:
                self.character_assets[goose_major] = sprites

            # load attacks
            # attack, sprites = load_attack_assets(f'{self.path}/attacks', self.progress, scale=1)
            # if sprites is not None:
            #     self.attack_assets[attack] = sprites

            # done loading
            if goose_major is None:
                self.finished_loading = True
            else:
                self.progress += 1
