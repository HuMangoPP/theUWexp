import pygame as pg
import os
import json
import time


def load_keybinds(path='./assets/player_settings'):
    keybinds = {}
    with open(os.path.join(path, 'keybinds.json')) as saved_bindings:
        keybinds = json.load(saved_bindings)
    return keybinds


def generate_frames(spritesheet: pg.Surface, num_frames: int, scale: float) -> dict[str, list[pg.Surface]]:
    right = []
    width = spritesheet.get_width() // num_frames
    height = spritesheet.get_height()

    for i in range(num_frames):
        frame = pg.Surface((width,height))
        frame.blit(spritesheet, (-i * width, 0))
        frame = pg.transform.scale(frame, (width * scale, height * scale))
        frame.set_colorkey((0,0,0))
        right.append(frame)
    
    left = [pg.transform.flip(frame, True, False) for frame in right]
    return {
        'right': right,
        'left': left,
    }


def generate_frame(frame: pg.Surface, scale: float) -> dict[str, pg.Surface]:
    frame = pg.transform.scale(frame, (frame.get_width() * scale, frame.get_height() * scale))
    frame.set_colorkey((0,0,0))
    return {
        'right': frame,
        'left': pg.transform.flip(frame, True, False)
    }


def load_character_assets(path='./assets/fighters', scale: float = 1):
    start_time = time.perf_counter()

    basic_spritesheet = {
        filename[:-4]: pg.image.load(os.path.join(path, 'basic', filename)).convert()
        for filename in os.listdir(os.path.join(path, 'basic'))
        if filename[-3:] == 'png'
    }

    spritesheets = {}
    accessories = {}
    for character_type in os.listdir(os.path.join(path)):
        if not os.path.isdir(os.path.join(path, character_type)):
            continue
        if character_type == 'basic':
            spritesheets['basic'] = {
                file_data.split('-')[0]: generate_frames(spritesheet, int(file_data.split('-')[1]), scale)
                for file_data, spritesheet in basic_spritesheet.items()
            }
        filenames = os.listdir(os.path.join(path, character_type))
        filenames = [filename for filename in filenames if filename[-3:] == 'png']
        if len(filenames) == 1:
            accessories[character_type] = generate_frame(pg.image.load(os.path.join(path, character_type, filenames[0])).convert(), scale)
        else:
            actions = {}
            for filename in filenames:
                file_data = filename[:-4]
                spritesheet = basic_spritesheet[file_data].copy()
                overlay = pg.image.load(os.path.join(path, character_type, filename)).convert()
                overlay.set_colorkey((0,0,0))
                spritesheet.blit(overlay, (0,0))
                actions[file_data.split('-')[0]] = generate_frames(spritesheet, int(file_data.split('-')[1]), scale)
            spritesheets[character_type] = actions

    end_time = time.perf_counter()

    print(f'Took {end_time - start_time}')
    return spritesheets, accessories


def load_attack_assets(path='./assets/attacks', scale: float = 1):
    start_time = time.perf_counter()

    spritesheets = {}
    for character_type in os.listdir(path):
        if not os.path.isdir(os.path.join(path, character_type)):
            continue
        attack_sprites = {}
        for filename in os.listdir(os.path.join(path, character_type)):
            if filename[-3:] == 'png':
                file_data = filename[:-4].split('-')
                attack_sprites[file_data[0]] = generate_frames(
                    pg.image.load(os.path.join(path, character_type, filename)).convert(), 
                    int(file_data[1]),
                    scale
                )
        spritesheets[character_type] = attack_sprites

    end_time = time.perf_counter()

    print(f'Took {end_time - start_time}')
    return spritesheets


def load_bgs(path='./assets/backgrounds', size: tuple = (1280,720)):
    bgs = {}
    for filename in os.listdir(path):
        if filename[-3:] == 'png':
            bgs[filename[:-4]] = pg.transform.scale(pg.image.load(os.path.join(path, filename)).convert(), size)
    
    return bgs