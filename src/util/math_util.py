import numpy as np


def lerp(v1: np.ndarray, v2: np.ndarray, t: float):
    return np.array(v1) + (np.array(v2) - np.array(v1)) * np.clip(t, a_min=0, a_max=1)