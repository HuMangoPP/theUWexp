import pygame as pg
import moderngl as mgl

from .pymgl.graphics_engine import GraphicsEngine
from .pyfont.font import Font

from .util.asset_loader import load_character_assets, load_attack_assets, load_keybinds, load_bgs

# import menus #
from .menus import *


class _Settings:
    RESOLUTION = (1280,720)
    MENU_MAP = {
        'start': 0,
        'main': 1,
        'select': 2,
        'fight': 3
    }


class Client:
    def __init__(self):
        self._pg_init()
        self._create_menus()
        self._load_assets()
    
    def _pg_init(self):
        # init
        pg.init()

        # get window and ctx
        self.resolution = _Settings.RESOLUTION
        # self.screen = pg.display.set_mode(self.resolution)
        pg.display.set_mode(self.resolution, pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = (
            mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        )

        # get graphics engine, font, and displays
        self.graphics_engine = GraphicsEngine(self.ctx, self.resolution, './src')
        self.font = Font(pg.image.load('./src/pyfont/font.png').convert())
        self.displays = {
            'default': pg.Surface(self.resolution),
            'gaussian_blur': pg.Surface(self.resolution),
            'black_alpha': pg.Surface(self.resolution)
        }
        self.displays['gaussian_blur'].set_colorkey((0,0,0))
        self.displays['black_alpha'].set_colorkey((0,0,0))

        # clock
        self.clock = pg.time.Clock()

    def _create_menus(self):
        # menus
        self.menus : list[Menu] = [
            StartMenu(self), 
            MainMenu(self),
            SelectMenu(self),
            FightMenu(self)
        ]
        self.current_menu = 0
    
    def _load_assets(self):
        # cursor
        pg.mouse.set_visible(False)
        self.cursor = pg.image.load('./assets/ui/cursor.png').convert()
        self.cursor.set_colorkey((0,0,0))
        
        # assets
        self.bgs, self.bg_thumbs = load_bgs()
        self.character_assets, self.accessory_assets = load_character_assets(scale=3)
        self.attack_assets = load_attack_assets(scale=3)
        keybinds = load_keybinds()
        self.keybinds = {
            'f1': {key: pg.key.key_code(keybinds['f1'][key]) for key in keybinds['f1']},
            'f2': {key: pg.key.key_code(keybinds['f2'][key]) for key in keybinds['f2']},
        }

    def update(self):
        dt = self.clock.get_time() / 1000
        events = pg.event.get()

        for event in events:
            if event.type == pg.QUIT:
                return {
                    'exit': True
                }
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return {
                    'exit': True
                }
        
        return self.menus[self.current_menu].update(events, dt)

    def render(self):
        self.ctx.clear(0.08, 0.1, 0.2)
        displays_to_render = self.menus[self.current_menu].render()
        [
            self.graphics_engine.render(
                self.displays[display], 
                self.displays[display].get_rect(), 
                shader=display
            ) 
            for display in displays_to_render
        ]
        # [self.screen.blit(self.displays[display], (0,0)) for display in displays_to_render]
    
    def run(self):
        self.menus[self.current_menu].on_load()
        while True:
            exit_status = self.update()
            if exit_status:
                if exit_status['exit']:
                    pg.quit()
                    return
                else:
                    if exit_status['goto'] == 'fight':
                        self.menus[_Settings.MENU_MAP['fight']].reset_fight_data()
                        self.menus[_Settings.MENU_MAP['fight']].get_fight_data(self.menus[_Settings.MENU_MAP['select']])
                    if exit_status['goto'] == 'select':
                        self.menus[_Settings.MENU_MAP['select']].reset_meta_data()

                    self.current_menu = _Settings.MENU_MAP[exit_status['goto']]
                    self.menus[self.current_menu].on_load()
            
            self.render()
            self.clock.tick()
            pg.display.flip()

            pg.display.set_caption(f'fps: {self.clock.get_fps()}')
