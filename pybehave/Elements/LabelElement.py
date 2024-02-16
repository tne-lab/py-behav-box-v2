from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pybehave.GUIs.GUI import GUI

import pygame

from pybehave.Elements.Element import Element


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
        self.txt_color = (255, 255, 255)  # Font color, could be made a parameter in the future
        self.shown_text = self.text

    def has_updated(self) -> bool:
        return self.shown_text != self.text

    def draw(self) -> None:
        self.shown_text = self.text
        _msg = self.font.render(self.text, True, self.txt_color)
        msg_ht = _msg.get_height()  # Position the label to the left of its containing rectangle
        msg_x = 0
        msg_y = (self.rect.height - msg_ht)/2
        self.screen.blit(_msg, self.rect.move(msg_x,  msg_y+1))  # Draw the label
