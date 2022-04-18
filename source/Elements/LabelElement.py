import pygame

from source.Elements.Element import Element


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

    def __init__(self, screen, x, y, w, h, text, f_size=20):
        super().__init__(screen, x, y, pygame.Rect(x, y, w, h))
        self.text = text
        self.f_size = f_size

    def draw(self):
        txt_color = (255, 255, 255)  # Font color, could be made a parameter in the future
        msg_font = pygame.font.SysFont('arial', self.f_size)
        msg_in_font = msg_font.render(self.text, True, txt_color)  # Create the font object
        msg_ht = msg_in_font.get_height()  # Position the label to the left of its containing rectangle
        msg_x = 0
        msg_y = (self.rect.height - msg_ht)/2
        self.screen.blit(msg_in_font, self.rect.move(msg_x,  msg_y+1))  # Draw the label
