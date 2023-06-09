from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from GUIs.GUI import GUI

import pygame

from Elements.Element import Element


class LabelElement(Element):
    """
    Class defining a text label in the pygame GUI.

    Parameters
    ----------
    screen : Surface
        The pygame Surface on which the label should be drawn
    x : int
        The x-coordinate of the label
    y : int
        The y-coordinate of the label
    w : int
        The width of the label
    h : int
        The height of the label
    text : str
        The text that should be shown in the label
    f_size : int
        The font size for the label

    Attributes
    ----------
    text : str
        The text that should be shown in the label
    f_size : int
        The font size for the label

    Methods
    -------
    draw():
        Draws the label on screen
     """

    def __init__(self, tg: GUI, x: int, y: int, w: int, h: int, text: str, f_size: int = 20, SF: float = None):
        super().__init__(tg, x, y, pygame.Rect(x, y, w, h), SF)
        self.text = text
        self.f_size = int(self.SF * f_size)
        self.font = pygame.font.SysFont('arial', self.f_size)
        txt_color = (255, 255, 255)  # Font color, could be made a parameter in the future
        self._msg = self.font.render(self.text, True, txt_color)  # Create the font object

    def draw(self) -> None:
        msg_ht = self._msg.get_height()  # Position the label to the left of its containing rectangle
        msg_x = 0
        msg_y = (self.rect.height - msg_ht)/2
        self.screen.blit(self._msg, self.rect.move(msg_x,  msg_y+1))  # Draw the label
