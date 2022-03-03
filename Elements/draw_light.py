import math
import pygame


def draw_light(screen, color, line_color, rect, cx, cy, radius):
    pygame.draw.circle(screen, color, (cx, cy), radius, 0)
    pygame.draw.circle(screen, (200, 200, 200), (cx + int(.5 * radius), cy - int(.5 * radius)),
                       int(.1 * radius), 0)
    shadow_color = (int(color[0] * .8), int(color[1] * .8), int(color[2] * .8))
    shadow_w = int(0.5 * radius)
    if shadow_w > 15:
        shadow_w = 15
    shadow_rect = rect
    pygame.draw.arc(screen, shadow_color, shadow_rect, 190 * math.pi / 180, 270 * math.pi / 180,
                    shadow_w)  # SHADOW
    pygame.draw.circle(screen, line_color, (cx, cy), radius, 2)
