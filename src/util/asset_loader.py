import pygame as pg
import os
import json


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


def load_character_assets(path='./assets/fighters', scale: float = 1, progress: int = -1):
    basic_spritesheet = {
        filename[:-4]: pg.image.load(os.path.join(path, 'basic', filename)).convert()
        for filename in os.listdir(os.path.join(path, 'basic'))
        if filename[-3:] == 'png'
    }
    if progress < 0:
        spritesheets = {}
        accessories = {}
        for character_type in os.listdir(path):
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

        return spritesheets, accessories
    
    character_types = os.listdir(path)
    if progress >= len(character_types):
        return {}, {}
    character_types = character_types[progress:]
    for character_type in character_types:
        if not os.path.isdir(os.path.join(path, character_type)):
            continue
        if character_type == 'basic':
            return {'basic': {
                file_data.split('-')[0]: generate_frames(spritesheet, int(file_data.split('-')[1]), scale)
                for file_data, spritesheet in basic_spritesheet.items()
            }}, {}
        filenames = os.listdir(os.path.join(path, character_type))
        filenames = [filename for filename in filenames if filename[-3:] == 'png']
        if len(filenames) == 1:
            return {}, {
                character_type: generate_frame(pg.image.load(os.path.join(path, character_type, filenames[0])).convert(), scale)
            }
        actions = {}
        for filename in filenames:
            file_data = filename[:-4]
            spritesheet = basic_spritesheet[file_data].copy()
            overlay = pg.image.load(os.path.join(path, character_type, filename)).convert()
            overlay.set_colorkey((0,0,0))
            spritesheet.blit(overlay, (0,0))
            actions[file_data.split('-')[0]] = generate_frames(spritesheet, int(file_data.split('-')[1]), scale)
        return {character_type: actions}, {}
    return {}, {}


def load_attack_assets(path='./assets/attacks', scale: float = 1, progress: int = -1):
    if progress < 0:
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
            
        return spritesheets
    
    character_types = os.listdir(path)
    if progress >= len(character_types):
        return {}
    character_types = character_types[progress:]
    for character_type in character_types:
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
        return {
            character_type: attack_sprites
        }
    return {}


def load_bgs(path='./assets/backgrounds', size: tuple = (1280,720), progress: int = -1):
    if progress < 0:
        bgs = {}
        for filename in os.listdir(path):
            if filename[-3:] == 'png':
                bgs[filename[:-4]] = pg.transform.scale(pg.image.load(os.path.join(path, filename)).convert(), size)
        
        thumbnails = {}
        for name, bg in bgs.items():
            thumbnails[name] = pg.transform.scale(bg, (size[0] // 5, size[1] // 5))
        
        return bgs, thumbnails
    
    filenames = os.listdir(path)
    if progress >= len(filenames):
        return {}, {}
    filenames = filenames[progress:]
    for filename in filenames:
        if filename[-3:] == 'png':
            bg = pg.transform.scale(pg.image.load(os.path.join(path, filename)).convert(), size)
            return (
                {filename[:-4]: bg},
                {filename[:-4]: pg.transform.scale(bg, (size[0] // 5, size[1] // 5))}
            )
    return {}, {}
