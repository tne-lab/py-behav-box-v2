from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from GUIs.GUI import GUI
    from Components.BinaryInput import BinaryInput

import pygame as pygame

from Elements.Element import Element
from GUIs import Colors


class NosePokeElement(Element):
    def __init__(self, tg: GUI, x: int, y: int, radius: int, comp: BinaryInput = None, SF: float = None):
        super().__init__(tg, x, y, pygame.Rect(x, y, radius * 2, radius * 2), SF)
        self.radius = int(self.SF * radius)
        self.entered = comp.get_state()
        self.comp = comp

    def draw(self) -> None:
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        self.entered = self.comp.get_state()

        pygame.draw.circle(self.screen, Colors.lightgray, (cx, cy), self.radius, 0)  # MAIN BULB
        surf1 = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        surf2 = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf1, Colors.darkgray, (self.radius, self.radius), self.radius)
        pygame.draw.circle(surf2, Colors.darkgray, (self.radius + self.radius / 2, self.radius - self.radius / 2), self.radius)
        surf1.blit(surf2, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.screen.blit(surf1, (cx-self.radius, cy-self.radius))
        pygame.draw.circle(self.screen, Colors.black, (cx, cy), self.radius + 2, 3)  # Black circle

        if self.entered:
            pygame.draw.polygon(self.screen, Colors.black, [(cx, cy), (cx - self.radius / 2, cy + self.radius), (cx + self.radius / 2, cy + self.radius)])

    def has_updated(self) -> bool:
        return self.entered != self.comp.get_state()

    def mouse_up(self, event: pygame.event.Event) -> None:
        self.component_changed(self.comp, False)

    def mouse_down(self, event: pygame.event.Event) -> None:
        self.component_changed(self.comp, True)
