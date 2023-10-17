# Designing GUIs to represent behavior

## Overview

Pybehave provides a framework for customizable monitoring and representation of task behavior using task-specific graphical
user interfaces (GUIs). GUIs are written using the [pygame]() library with individual objects in the GUI wrapped as *Element*
classes. GUIs can be used both for visually presenting task data or allow experimenters to interact with the task workflow.

## Elements

Every visual object in the task GUI is represented by an *Element* class that interacts with the pygame library. The base
element constructor requires a reference to the overarching task GUI, an x and y coordinate, and a bounding rectangle:

    def __init__(self, tg: GUI, x: int, y: int, rect: pygame.Rect, SF:float = None):

An additional argument for the scale factor can be provided; if left blank it will be automatically computed. 
Element subclasses can extend this constructor to account for additional information they may need such as colors or references
to task [Components](). The full list of default Elements and their constructors is provided in the [package reference]().

### draw

All Element subclasses must override the `draw` method responsible for visually constructing the component.

### has_updated

### Mouse events

### Interacting with components

## GUI classes

All Tasks must have a GUI class saved in the *GUIs* folder of the *Local* Git submodule `source/Local/GUIs` named *TASK_NAMEGUI*. GUIs are subclasses of the base `GUI`
class and must override the `initialize` method. This method must construct all the Elements in the GUI, add them as class
attributes, and return them as a list. 

### Positioning elements

The base size for a task GUI is 500x900px and all length values should be provided according to this standard. If the GUI changes
size due to the dimensions of the screen or the number of chambers in the Workstation, GUI elements will be scaled by a fixed
scale factor. Each Element has a scale factor attribute `SF` that can be used for maintaining uniform scaling across differently
sized GUIs. All distances used by an Element should be scaled using this factor like so:

    self.f_size = int(self.SF * f_size)

The base Element position and bounding box attributes will be scaled when calling the constructor.

### Handling Events

GUIs are given access to the Task event stream through the `handle_events` method.

## Package reference

### GUI

#### draw

    draw()

By default, the `draw` method will clear the GUI canvas with a gray color and call each GUI Element's `draw` method. This 
functionality can be altered by overriding the method.

#### get_elements

    get_elements()

Returns the Elements in the GUI as a list. This method must be overridden by any GUI subclasses.

*Example override:*

    def get_elements(self) -> List[Element]:
        return [self.fl, self.rl, self.complete_button, *self.info_boxes]

#### handle_events

    handle_events(events)

Called by the Workstation event loop to send keyboard/mouse events in the GUI to each Element.

### SequenceGUI

Additionally calls the standard GUI methods on its `sub_gui` attribute.

### Element 

#### \_\_init\_\_

    __init__(tg, x, y, rect, SF=None)

#### draw

    draw()

#### handle_event

    handle_event(event)

#### mouse_down

    mouse_down(event)

#### mouse_up

    mouse_up(event)

### Default elements

#### BarPressElement

    class BarPressElement(tg: GUI, x: int, y: int, w: int, h: int, comp: BinaryInput = None, SF: float = None)

#### ButtonElement

    class ButtonElement(tg: GUI, x: int, y: int, w: int, h: int, text: str, f_size: int = 12, SF: float = None)

#### CircleLightElement

    class CircleLightElement(tg: GUI, x: int, y: int, radius: int, on_color: tuple[int, int, int] = Colors.lightgray, background_color: tuple[int, int, int] = Colors.darkgray, comp: Toggle = None, SF: float = None)

#### FanElement

    class FanElement(tg: GUI, x: int, y: int, radius: int, comp: Toggle = None)

#### FoodLightElement

    class FoodLightElement(tg: GUI, x: int, y: int, w: int, h: int, on_color: tuple[int, int, int] = Colors.lightgray, comp: Toggle = None, line_color: tuple[int, int, int] = Colors.black, SF: float = None)

#### IndicatorElement

    class IndicatorElement(tg: GUI, x: int, y: int, radius: int, on_color: tuple[int, int, int] = Colors.green, off_color: tuple[int, int, int] = Colors.red)

#### InfoBoxElement

    class InfoBoxElement(tg: GUI, x: int, y: int, w: int, h: int, label: str, label_pos: str, text: list[str], f_size: int = 14, SF: float = None)

#### LabelElement

    class LabelElement(tg: GUI, x: int, y: int, w: int, h: int, text: str, f_size: int = 20, SF: float = None)

#### NosePokeElement

    class NosePokeElement(tg: GUI, x: int, y: int, radius: int, comp: BinaryInput = None, SF: float = None)

#### ShockElement

    class ShockElement(tg: GUI, x: int, y: int, radius: int, color: tuple[int, int, int] = (255, 255, 0), comp: Toggle = None)

#### SoundElement

    class SoundElement(tg: GUI, x: int, y: int, radius: int, comp: Toggle = None)

### Helper functions

#### draw_filled_arc

    draw_filled_arc(screen: pygame.Surface, center: tuple[int, int], arc_angle: float, r: float, init_angle: float, col: tuple[int, int, int], ns: int = 100) -> None

#### draw_light

    draw_light(screen: pygame.Surface, color: Tuple[int, int, int], line_color: Tuple[int, int, int], rect: pygame.Rect, cx: int, cy: int, radius: float) -> None