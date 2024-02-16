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

All Element subclasses must override the `draw` method responsible for visually constructing the element in the GUI using
the various pygame draw methods.

### has_updated

The `has_updated` method should be overridden to indicate when the element should be redrawn. This is typically handled 
through two sets of variables one of which is updated externally and the other tracks the current visual state. These are 
then compared in the `has_updated` method.

### Mouse events

Two methods are provided for interacting with click events: `mouse_up_` and `mouse_down_`. These will be called whenever 
the element is clicked. The `Button` element has an example of how these can be used.

### Interacting with components

Elements can write or read from virtual components represented by the GUI. To read from a component, a component's state should
be compared to an internal variable in `has_updated` (see `NosePokeElement` for an example). To write a new value to a component,
use the `component_changed` method.

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

    draw() -> None

By default, the `draw` method will clear the GUI canvas with a gray color and call each GUI Element's `draw` method. This 
functionality can be altered by overriding the method.

#### initialize

    initialize() -> List[Element]

Creates all the elements in the GUI and returns them as a list. This method must be overridden by any GUI subclasses.

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

    __init__(tg: GUI, x: int, y: int, rect: pygame.Rect, SF=None)

*Inputs:*

`tg` the GUI this Element is being created in

`x` the x-coordinate of the top left corner of the element

`y` the y-coordinate of the top left corner of the element

`rect` the bounding rectangle of the element

`SF` scale factor on the size of the component from the default

#### draw

    draw() -> None

Called by the GUI to redraw the Element whenever it has visually updated.

#### handle_event

    handle_event(event: pygame.event.Event) -> bool

Internal method that will call `mouse_down_` or `mouse_up_` when the Element is clicked. Returns True if the event was
handled.

*Inputs:*

`event` pygame event that associated with this component

#### mouse_down_

    mouse_down_(event: pygame.event.Event) -> None

Called when the left mouse button is pressed.

*Inputs:*

`event` pygame event that associated with this component

#### mouse_up_

    mouse_up_(event: pygame.event.Event) -> None

Called when the left mouse button is released.

*Inputs:*

`event` pygame event that associated with this component

### Default elements

#### BarPressElement

    class BarPressElement(tg: GUI, x: int, y: int, w: int, h: int, comp: BinaryInput = None, SF: float = None)

Element for representing a lever or bar in an operant chamber.

*Inputs:*

`w` the width of the Element

`h` the height of the Element

`comp` the BinaryInput associated with this Element

#### ButtonElement

    class ButtonElement(tg: GUI, x: int, y: int, w: int, h: int, text: str, f_size: int = 12, SF: float = None)

Element representing a text-button in the GUI for adding user interaction/controls.

*Inputs:*

`w` the width of the Element

`h` the height of the Element

`text` the text in the button

`f_size` the font size of the button's text

*Properties:*

`mouse_down` function that will be called when the button is pressed

`mouse_up` function that will be called when the button is released

#### CircleLightElement

    class CircleLightElement(tg: GUI, x: int, y: int, radius: int, on_color: tuple[int, int, int] = Colors.lightgray, background_color: tuple[int, int, int] = Colors.darkgray, comp: Toggle = None, SF: float = None)

Element representing a circle-shaped light.

*Inputs:*

`radius` the radius of the Element

`on_color` RGB triplet representing an active light

`background_color` RGB triplet representing an inactive light

`comp` the Toggle component associated with this light

#### FanElement

    class FanElement(tg: GUI, x: int, y: int, radius: int, comp: Toggle = None)

Element representing a fan.

*Inputs:*

`radius` the radius of the Element

`comp` the Toggle component associated with this fan

#### FoodLightElement

    class FoodLightElement(tg: GUI, x: int, y: int, w: int, h: int, on_color: tuple[int, int, int] = Colors.lightgray, comp: Toggle = None, line_color: tuple[int, int, int] = Colors.black, SF: float = None)

Element representing a light typically associated with a food trough.

*Inputs:*

`w` width of the Element

`h` height of the Element

`on_color` RGB triplet representing an active light

`background_color` RGB triplet representing an inactive light

`comp` the Toggle component associated with this light

`line_color` RGB triplet representing the color of the lines in the Element

#### IndicatorElement

    class IndicatorElement(tg: GUI, x: int, y: int, radius: int, on_color: tuple[int, int, int] = Colors.green, off_color: tuple[int, int, int] = Colors.red)

Element representing a visual indicator in the GUI.

*Inputs:*

`radius` the radius of the Element

`on_color` RGB triplet representing an active state

`off_color` RGB triplet representing an inactive state

*Properties:*

`on` set to True/False to change state of indicator

#### InfoBoxElement

    class InfoBoxElement(tg: GUI, x: int, y: int, w: int, h: int, label: str, label_pos: str, text: list[str], f_size: int = 14, SF: float = None)

Element representing a textbox in the GUI.

*Inputs:*

`w` the width of the Element

`h` the height of the Element

`label` text label for the box

`label_pos` position of the label relative to the box ('TOP','LEFT','RIGHT', or 'BOTTOM')

`text` the text in the box, one element in the list per line in the box

`f_size` the font size of the button's text

*Methods:*

`set_text(new_text: Union[str, List]) -> None` update the text shown in the box

#### LabelElement

    class LabelElement(tg: GUI, x: int, y: int, w: int, h: int, text: str, f_size: int = 20, SF: float = None)

Element representing a label in the GUI.

*Inputs:*

`w` the width of the Element

`h` the height of the Element

`text` the text for the label

`f_size` the font size of the button's text

#### NosePokeElement

    class NosePokeElement(tg: GUI, x: int, y: int, radius: int, comp: BinaryInput = None, SF: float = None)

Element for representing a nosepoke in the operant chamber.

*Inputs:*

`radius` the radius of the Element

`comp` the BinaryInput associated with this Element

#### ShockElement

    class ShockElement(tg: GUI, x: int, y: int, radius: int, color: tuple[int, int, int] = (255, 255, 0), comp: Toggle = None)

Element representing a shocker.

*Inputs:*

`radius` the radius of the Element

`color` RGB triplet representing the color of the bolt

`comp` the Toggle component associated with this shocker

#### SoundElement

    class SoundElement(tg: GUI, x: int, y: int, radius: int, comp: Toggle = None)

Element representing a speaker.

*Inputs:*

`radius` the radius of the Element

`comp` the Toggle component associated with this speaker

### Helper functions

#### draw_filled_arc

    draw_filled_arc(screen: pygame.Surface, center: tuple[int, int], arc_angle: float, r: float, init_angle: float, col: tuple[int, int, int], ns: int = 100) -> None

#### draw_light

    draw_light(screen: pygame.Surface, color: Tuple[int, int, int], line_color: Tuple[int, int, int], rect: pygame.Rect, cx: int, cy: int, radius: float) -> None