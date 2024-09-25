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
        frame = pg.Surface((frame_width, frame_height))
        frame.blit(spritesheet, (-i * frame_width, 0))
        frame.set_colorkey((255, 0, 0))
        frames.append(frame)
    return frames
    

def _load_spritesheet(path: str) -> dict[str, list[pg.Surface]]:
    sprites = {}
    for filename in os.listdir(path):
        spritesheet_name = filename[:-4].split('-')[0]
        num_frames = int(filename[:-4].split('-')[1])
        sprites[spritesheet_name] = _get_frames(pg.image.load(os.path.join(path, filename)).convert(), num_frames)
    return sprites


def _overlay_frames(base: dict[str, list[pg.Surface]], overlay: dict[str, list[pg.Surface]]) -> dict[str, list[pg.Surface]]:
    sprites = {}
    for spritesheet_name, base_frames in base.items():
        overlay_frames = overlay[spritesheet_name]
        frames = []
        for base_frame, overlay_frame in zip(base_frames, overlay_frames):
            frame = pg.Surface(base_frame.get_size())
            frame.set_colorkey((0, 0, 0))
            frame.blit(base_frame, (0, 0))
            frame.blit(overlay_frame, (0, 0))
            frames.append(frame)
        sprites[spritesheet_name] = frames
    return sprites


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


def load_character_assets(path: str, progress: int, scale: float = 1):
    majors = os.listdir(path)
    if progress >= len(majors):
        return None, None
    major = majors[progress]
    goose_sprites = _scale_frames(_load_spritesheet(os.path.join(path, major)), scale)
    return major, _flip_frames(goose_sprites)


def load_accessory_assets(path: str, progress: int, scale: float = 1):
    majors = os.listdir(path)
    if progress >= len(majors):
        return None, None
    major = majors[progress]
    if len(os.listdir(os.path.join(path, major))) == 1:
        accessory_sprite = pg.transform.scale_by(pg.image.load(os.path.join(path, major, f'{major}.png')), scale)
        accessory_sprite.set_colorkey((0, 0, 0))
        flipped_sprite = pg.transform.flip(accessory_sprite, flip_x=True, flip_y=False)
        flipped_sprite.set_colorkey((0, 0, 0))
        return major, dict(
            right=accessory_sprite,
            left=flipped_sprite
        )
    return major, None


def load_attack_assets(path: str, progress: int, scale: float = 1):
    majors = [major for major in os.listdir(path) if os.path.isdir(os.path.join(path, major))]
    if progress >= len(majors):
        return None, None
    major = majors[progress]
    if len(os.listdir(os.path.join(path, major))) > 0:
        sprites = _flip_frames(_scale_frames(_load_spritesheet(os.path.join(path, major)), scale))
        return major, sprites
    return major, None
