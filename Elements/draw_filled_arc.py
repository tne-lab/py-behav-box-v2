import math
import pygame


def draw_filled_arc(screen, center, arc_angle, r, init_angle, col, ns=100):
    p = [center]
    # Get points on arc
    for n in range(ns):
        x = center[0] + int(r * math.cos(init_angle + arc_angle / ns * n))
        y = center[1] - int(r * math.sin(init_angle + arc_angle / ns * n))
        p.append((x, y))
    p.append(center)
    pygame.draw.polygon(screen, col, p)
