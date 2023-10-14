import pygame as pg

TRANSITION_TIME = 0.5

def transition_out(overlay: pg.Surface, transition_time: float):
    width, height = overlay.get_size()
    transition_progress = 1.25 * transition_time / TRANSITION_TIME
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
    transition_progress = 1.25 * transition_time / TRANSITION_TIME
    topleft = [transition_progress * width, 0]
    bottomleft = [transition_progress * width - 200, height]
    topright = [width, 0]
    bottomright = [width, height]
    points = [
        topleft, bottomleft, bottomright, topright
    ]
    overlay.fill((0, 0, 0))
    pg.draw.polygon(overlay, (10, 10, 10), points)