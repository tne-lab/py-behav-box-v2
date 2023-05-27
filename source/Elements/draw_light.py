from typing import Tuple
import math
import pygame


def draw_light(screen: pygame.Surface, color: Tuple[int, int, int], line_color: Tuple[int, int, int], rect: pygame.Rect, cx: int, cy: int, radius: float) -> None:
    """
    Draws an object on the screen corresponding to a light

    Parameters
    ----------
    screen : Surface
        The pygame Surface on which the light should be drawn
    color : tuple
        Three element tuple corresponding to the on color for the light
    line_color : tuple
        Three element tuple corresponding to the line color of the light
    rect : Rect
        Pygame Rect corresponding to the boundary of the light
    cx : int
        Integer indicating the x-coordinate of the light's center
    cy : int
        Integer indicating the y-coordinate of the light's center
    radius : int
        Integer indicating the radius of the light
    """
    pygame.draw.circle(screen, color, (cx, cy), radius, 0)  # The main bulb
    pygame.draw.circle(screen, (200, 200, 200), (cx + int(.5 * radius), cy - int(.5 * radius)),
                       int(.1 * radius), 0)  # Sparkle
    shadow_color = (int(color[0] * .8), int(color[1] * .8), int(color[2] * .8))  # Color of light's shadow
    shadow_w = int(0.5 * radius)  # The radius of the shadow arc
    if shadow_w > 15:
        shadow_w = 15
    shadow_rect = rect
    pygame.draw.arc(screen, shadow_color, shadow_rect, 190 * math.pi / 180, 270 * math.pi / 180,
                    shadow_w)  # Light shadow
    pygame.draw.circle(screen, line_color, (cx, cy), radius, 2)  # Light border
