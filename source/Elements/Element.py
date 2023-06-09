from __future__ import annotations
from typing import TYPE_CHECKING, Any

from Components.Component import Component
from Tasks.TaskEvents import ComponentUpdateEvent

if TYPE_CHECKING:
    from GUIs.GUI import GUI

from abc import ABCMeta, abstractmethod

import pygame


class Element:
    __metaclass__ = ABCMeta
    """
    Abstract class defining the base requirements of an object in the pygame GUI.

    Parameters
    ----------
    screen : Surface
        The pygame Surface on which the Element should be drawn
    x : int
        The x-coordinate of the Element
    y : int
        The y-coordinate of the Element
    rect : Rect
        Pygame Rect object defining the bounds of the Element

    Attributes
    ----------
    screen : Surface
        The pygame Surface on which the Element should be drawn
    x : int
        The x-coordinate of the Element
    y : int
        The y-coordinate of the Element
    rect : Rect
        Pygame Rect object defining the bounds of the Element
    selected : boolean
        Boolean indicating if the Element is currently clicked

    Methods
    -------
    mouse_down(event)
        Callback for when the mouse button is down within the Element with metadata contained in event
    mouse_up(event)
        Callback for when the mouse button is up within the Element with metadata contained in event
    handle_event(event)
        Calls the relevant Element method if the event is within the bounds of the Element
    draw():
        Draws the Element on screen
    """

    def __init__(self, tg: GUI, x: int, y: int, rect: pygame.Rect, SF: float = None):
        if SF is None:
            self.SF = tg.SF
        else:
            self.SF = SF
        self.gui = tg
        self.screen = tg.task_gui
        self.x = int(self.SF * x)
        self.y = int(self.SF * y)
        self.rect = pygame.Rect(int(rect.x * self.SF), int(rect.y * self.SF), int(rect.width * self.SF), int(rect.height * self.SF))
        self.selected = False

    def mouse_down(self, event: pygame.event.Event) -> None:
        pass

    def mouse_up(self, event: pygame.event.Event) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> bool:
        cur_x, cur_y = pygame.mouse.get_pos()
        offset = self.screen.get_offset()  # Correct the position based on the location of the screen
        cur_x -= offset[0]
        cur_y -= offset[1]

        if event.type == pygame.MOUSEBUTTONDOWN:  # If a mouse button was clicked
            if event.button == 1 and self.rect.collidepoint(cur_x, cur_y):  # If a left mouse button within rectangle
                self.selected = True  # Indicate that this Element was clicked
                self.mouse_down(event)  # Callback for mouse down
                return True  # Event handled
        elif event.type == pygame.MOUSEBUTTONUP:  # If a mouse button was released
            if event.button == 1 and self.rect.collidepoint(cur_x, cur_y) and self.selected:  # If a left mouse button within rectangle
                self.mouse_up(event)  # Callback for mouse up
                self.selected = False  # Indicate that this Element is no longer clicked
                return True  # Event handled
            self.selected = False  # Indicate that this Element is no longer clicked
        return False  # Event not handled

    @abstractmethod
    def draw(self) -> None:
        raise NotImplementedError

    def component_changed(self, component: Component, value: Any):
        self.gui.task.task_thread.queue.put(ComponentUpdateEvent(component.id, value))
