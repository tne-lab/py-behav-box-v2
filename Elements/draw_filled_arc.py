import math
import pygame


def draw_filled_arc(screen, center, arc_angle, r, init_angle, col, ns=100):
    """
    Draws an object on the screen corresponding to a filled circular segment

    Parameters
    ----------
    screen : Surface
        The pygame Surface on which the light should be drawn
    center : tuple
        Tuple indicating the central coordinates of the arc
    arc_angle : int
        The angle swept out by the arc
    r : int
        The radius of the arc
    init_angle : int
        The starting angle for the arc
    col : tuple
        The color of the arc
    ns : int
        Number of points used to draw arc
    """
    p = [center]
    # Get points on arc
    for n in range(ns):
        x = center[0] + int(r * math.cos(init_angle + arc_angle / ns * n))
        y = center[1] - int(r * math.sin(init_angle + arc_angle / ns * n))
        p.append((x, y))
    p.append(center)
    pygame.draw.polygon(screen, col, p)
