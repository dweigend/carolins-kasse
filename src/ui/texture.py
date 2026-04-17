"""Paper texture generator for UI background.

Generates procedural noise on cream-colored background for organic feel.
"""

import numpy as np
import pygame
from src.constants import CREAM


def generate_paper_texture(width: int, height: int) -> pygame.Surface:
    """Generate a procedural paper texture.

    Creates subtle noise on a cream background for organic, handmade feel.

    Args:
        width: Surface width in pixels
        height: Surface height in pixels

    Returns:
        pygame.Surface with noise texture applied
    """
    # Generate random noise: small variations (-12 to +12 per channel)
    noise = np.random.randint(-12, 12, (height, width, 3), dtype=np.int16)

    # Start with cream base color, add noise to each channel
    r, g, b = CREAM
    pixels = np.clip(
        np.full((height, width, 3), [r, g, b], dtype=np.int16) + noise,
        0,
        255,
    ).astype(np.uint8)

    # Convert numpy array to pygame surface
    # Note: transpose needed because pygame uses (width, height) order
    return pygame.surfarray.make_surface(pixels.transpose(1, 0, 2))
