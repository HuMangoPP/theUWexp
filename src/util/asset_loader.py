import pygame as pg
import os
import json


def load_keybinds(path: str) -> list[dict[str, str]]:
    keybinds = []
    with open(path) as saved_keybinds:
        keybinds = json.load(saved_keybinds)
    return keybinds


def load_backgrounds(path: str, scale_to: tuple) -> tuple[dict[str, pg.Surface], dict[str, pg.Surface]]:
    backgrounds = {}
    for filename in os.listdir(path):
        background_name = filename[:-4]
        backgrounds[background_name] = pg.transform.scale(
            pg.image.load(os.path.join(path, filename)).convert(), 
            scale_to
        )
    
    background_thumbnails = {}
    for name, bg in backgrounds.items():
        background_thumbnails[name] = pg.transform.scale_by(bg, 1 / 5)
    
    return backgrounds, background_thumbnails


def _get_frames(spritesheet: pg.Surface, num_frames: int) -> list[pg.Surface]:
    frames = []
    frame_width = spritesheet.get_width() // num_frames
    frame_height = spritesheet.get_height()
    for i in range(num_frames):
        frame = spritesheet.subsurface(pg.Rect(
            i * frame_width, 0,
            frame_width, frame_height
        ))
        frame.set_colorkey((255, 0, 0))
        frames.append(frame)
    return frames


def _load_spritesheet(path: str, animations: list[tuple[str, int]]) -> dict[str, list[pg.Surface]]:
    spritesheet = pg.image.load(path).convert()
    frame_width = spritesheet.get_width() / max([num_frames for _, num_frames in animations])
    frame_height = spritesheet.get_height() / len(animations)

    return {
        animation: _get_frames(spritesheet.subsurface(pg.Rect(
            0, frame_height * i,
            frame_width * num_frames, frame_height
        )), num_frames)
        for i, (animation, num_frames) in enumerate(animations)
    }


def _scale_frames(sprites: dict[str, list[pg.Surface]], scale: float):
    return {
        spritesheet_name: [pg.transform.scale_by(frame, scale) for frame in frames]
        for spritesheet_name, frames in sprites.items()
    }


def _flip_frames_and_set_colorkey(frames: list[pg.Surface]):
    for frame in frames:
        flipped_frame = pg.transform.flip(frame, flip_x=True, flip_y=False)
        flipped_frame.set_colorkey((255, 0, 0))
        yield flipped_frame


def _flip_frames(sprites: dict[str, list[pg.Surface]]) -> dict[str, dict[str, list[pg.Surface]]]:
    return {
        spritesheet_name: dict(
            right=frames,
            left=[frame for frame in _flip_frames_and_set_colorkey(frames)]
        )
        for spritesheet_name, frames in sprites.items()
    }


def load_character_assets(path: str, meta_data: dict, progress: int, scale: float = 1):
    majors = meta_data['geese']
    if progress >= len(majors):
        return None, None
    major = majors[progress]
    animations = meta_data['base'] + [
        [attack_type, num_frames]
        for attack_type, num_frames in zip(meta_data['light_attacks'], meta_data[major]['light'])
    ]
    goose_sprites = _flip_frames(_scale_frames(_load_spritesheet(os.path.join(path, f'{major}.png'), animations), scale))
    return major, goose_sprites


def load_accessory_assets(path: str, meta_data: list, scale: float = 1):
    majors = meta_data['accessories']
    accessories = pg.image.load(os.path.join(path, f'accessories.png')).convert()
    frame_width = accessories.get_width() // len(majors)
    frame_height = accessories.get_height()
    accessory_sprites = {}
    for i, major in enumerate(majors):
        accessory = pg.transform.scale_by(pg.Surface.subsurface(accessories, pg.Rect(i * frame_width, 0, frame_width, frame_height)), scale)
        accessory.set_colorkey((255, 0, 0))
        flipped = pg.transform.flip(accessory, True, False)
        flipped.set_colorkey((255, 0, 0))
        accessory_sprites[major] = dict(
            right=accessory,
            left=flipped
        )
    return accessory_sprites


def load_attack_assets(path: str, meta_data: dict, progress: int, scale: float = 1):
    majors = meta_data['attacks']
    if progress >= len(majors):
        return None, None
    major = majors[progress]
    animations = [
        [animation, num_frames]
        for animation, num_frames in zip(meta_data['animations'], meta_data[major])
    ]
    sprites = _flip_frames(_scale_frames(_load_spritesheet(os.path.join(path, f'{major}.png'), animations), scale))
    return major.split('.')[0], sprites
