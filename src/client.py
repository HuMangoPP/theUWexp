import numpy as np
import pygame as pg
import moderngl as mgl

from .pymgl import GraphicsEngine
from .pyfont import Font

from .util.asset_loader import load_character_assets, load_attack_assets, load_keybinds, load_bgs

from .menus import *


class _Settings:
    RESOLUTION = (1280,720)
    MENU_MAP = dict(
        start=0,
        main=1,
        select=2,
        fight=3
    )


class Client:
    def __init__(self):
        self._pg_init()
        self._create_menus()
        self._asset_load_progress = 0
        self.finished_loading = False
        self._load_assets()
    
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

    def _create_menus(self):
        # menus
        self.menus : list[Menu] = [
            StartMenu(), 
            MainMenu(),
            SelectMenu(),
            FightMenu()
        ]
        self.current_menu = 0
    
    def _load_assets(self):
        if self._asset_load_progress == 0:
            # cursor
            pg.mouse.set_visible(False)
            self.cursor = pg.image.load('./assets/ui/cursor.png').convert()
            self.cursor.set_colorkey((0,0,0))
            
            # keybinds
            keybinds = load_keybinds()
            self.keybinds = dict(
                f1={key: pg.key.key_code(keybinds['f1'][key]) for key in keybinds['f1']},
                f2={key: pg.key.key_code(keybinds['f2'][key]) for key in keybinds['f2']},
            )

            # art assets
            self.bgs = {}
            self.bg_thumbs = {}
            self.character_assets = {}
            self.accessory_assets = {}
            self.attack_assets = {}

        # load bgs
        bgs, bg_thumbs = load_bgs(progress=self._asset_load_progress)
        self.bgs = {
            **self.bgs,
            **bgs
        }
        self.bg_thumbs = {
            **self.bg_thumbs,
            **bg_thumbs
        }
        
        # load characters
        character_assets, accessory_assets = load_character_assets(scale=3, progress=self._asset_load_progress)
        self.character_assets = {
            **self.character_assets,
            **character_assets
        }
        self.accessory_assets = {
            **self.accessory_assets,
            **accessory_assets
        }

        # load attacks
        attack_assets = load_attack_assets(scale=3, progress=self._asset_load_progress)
        self.attack_assets = {
            **self.attack_assets,
            **attack_assets
        }

        # done loading
        if (
            not bgs and
            not character_assets and
            not accessory_assets and 
            not attack_assets
        ):
            self.finished_loading = True

        self._asset_load_progress += 1

    def update(self):
        dt = self.clock.get_time() / 1000
        events = pg.event.get()

        # quit client
        for event in events:
            if event.type == pg.QUIT:
                return dict(exit=True)
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return dict(exit=True)
        
        # not done loading assets
        if not self.finished_loading:
            self._load_assets()
            self.menus[self.current_menu].transition_time = 0
        
        # menu update
        return self.menus[self.current_menu].update(dt, events)

    def render(self):
        self.ctx.clear(0.08, 0.1, 0.2)

        # render to pg surface
        self.menus[self.current_menu].render(self.displays, self.font)

        # not done loading assets
        if not self.finished_loading:
            num_dots = self._asset_load_progress % 3 + 1
            self.font.render(
                self.displays['black_alpha'],
                f"loading{'.' * num_dots}{' ' * (3 - num_dots)}",
                np.array(self.resolution) / 2,
                (255, 255, 255),
                25,
                style='center'
            )
        
        # render using graphics engine to screen
        [self.graphics_engine.render(
            display, 
            shader=shader
        ) for shader, display in self.displays.items()]
    
    def run(self):
        # on load
        self.menus[self.current_menu].on_load()
        while True:
            # update
            exit_status = self.update()
            self.clock.tick()
            if exit_status:
                if exit_status['exit']:
                    pg.quit()
                    return
                else: # menu transitions
                    self.current_menu = _Settings.MENU_MAP[exit_status['goto']]
                    self.menus[self.current_menu].on_load()
            
            # render
            self.render()
            pg.display.flip()
