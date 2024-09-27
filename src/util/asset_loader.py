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


def _load_spritesheet(path: str, animations: dict[str, int]) -> dict[str, list[pg.Surface]]:
    spritesheet = pg.image.load(path).convert()
    frame_width = spritesheet.get_width() / max(animations.values())
    frame_height = spritesheet.get_height() / len(animations.keys())

    sprites = {}
    for i, (animation, num_frames) in enumerate(animations.items()):
        sprites[animation] = _get_frames(spritesheet.subsurface(pg.Rect(
            0, frame_height * i,
            frame_width * num_frames, frame_height
        )), num_frames)
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


CHARACTER_ANIMATIONS = dict(
    idle=8,
    move=8,
    dash=4,
    jump=4,
    fall=2,
    nlight=6,
    slight=6,
    dlight=6,
    nair=6,
    sair=6,
    dair=6
)


def load_character_assets(path: str, progress: int, scale: float = 1):
    majors = os.listdir(path)
    if progress >= len(majors):
        return None, None
    major = majors[progress]
    goose_sprites = _flip_frames(_scale_frames(_load_spritesheet(os.path.join(path, major), CHARACTER_ANIMATIONS), scale))
    return major.split('.')[0], goose_sprites


# def load_accessory_assets(path: str, progress: int, scale: float = 1):
#     majors = os.listdir(path)
#     if progress >= len(majors):
#         return None, None
#     major = majors[progress]
#     if len(os.listdir(os.path.join(path, major))) == 1:
#         accessory_sprite = pg.transform.scale_by(pg.image.load(os.path.join(path, major, f'{major}.png')), scale)
#         accessory_sprite.set_colorkey((0, 0, 0))
#         flipped_sprite = pg.transform.flip(accessory_sprite, flip_x=True, flip_y=False)
#         flipped_sprite.set_colorkey((0, 0, 0))
#         return major, dict(
#             right=accessory_sprite,
#             left=flipped_sprite
#         )
#     return major, None


ATTACK_ANIMATIONS = dict(
    nlight=6,
    slight=6,
    dlight=6,
    nair=6,
    sair=6,
    dair=6
)


def load_attack_assets(path: str, progress: int, scale: float = 1):
    majors = os.listdir(path)
    if progress >= len(majors):
        return None, None
    major = majors[progress]
    sprites = _flip_frames(_scale_frames(_load_spritesheet(os.path.join(path, major), ATTACK_ANIMATIONS), scale))
    return major.split('.')[0], sprites
