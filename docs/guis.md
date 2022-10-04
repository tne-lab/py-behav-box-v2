# Designing GUIs to represent behavior

## Overview

Pybehave provides a framework for customizable monitoring and representation of task behavior using task-specific graphical
user interfaces (GUIs). GUIs are written using the [pygame]() library with individual objects in the GUI wrapped as *Element*
classes. GUIs can be used both for visually presenting task data or allow experimenters to interact with the task workflow.

## Elements

Every visual object in the task GUI is represented by an *Element* class that interacts with the pygame library. The base
element constructor requires a reference to the overarching task GUI, an x and y coordinate, and a bounding rectangle:

    def __init__(self, tg, x, y, rect, SF=None):

An additional argument for the scale factor can be provided; if left blank it will be automatically computed. 
Element subclasses can extend this constructor to account for additional information they may need such as colors or references
to task [Components](). All Element subclasses must override the `draw` method responsible for visually constructing the component.
An example class for the LabelElement is shown below:

    class LabelElement(Element):

    def __init__(self, tg, x, y, w, h, text, f_size=20, SF=None):
        super().__init__(tg, x, y, pygame.Rect(x, y, w, h), SF)
        self.text = text
        self.f_size = int(self.SF * f_size)

    def draw(self):
        txt_color = (255, 255, 255)  # Font color
        msg_font = pygame.font.SysFont('arial', self.f_size)
        msg_in_font = msg_font.render(self.text, True, txt_color)  # Create the font object
        msg_ht = msg_in_font.get_height()  # Position the label to the left of its containing rectangle
        msg_x = 0
        msg_y = (self.rect.height - msg_ht)/2
        self.screen.blit(msg_in_font, self.rect.move(msg_x,  msg_y+1))  # Draw the label

The full list of default Elements and their constructors is provided in the [package reference]().

## GUI classes

All Tasks must have a GUI class saved in the `source/GUIs` folder named *TASK_NAMEGUI*. GUIs are subclasses of the base `GUI`
class and are constructed with reference to a pygame `Screen` object named `task_gui` and the corresponding Task object `task`:

    def __init__(self, task_gui, task):

This constructor should be overridden to declare all Elements used in the GUI as class attributes. Additionally, the `get_elements` 
method must be overridden to declare the list of Element objects present in the GUI. GUIs for a `TaskSequence` should instead override
the `SequenceGUI` base class.

### Positioning elements

The base size for a task GUI is 500x900px and all length values should be provided according to this standard. If the GUI changes
size due to the dimensions of the screen or the number of chambers in the Workstation, GUI elements will be scaled by a fixed
scale factor. Each Element has a scale factor attribute `SF` that can be used for maintaining uniform scaling across differently
sized GUIs. All distances used by an Element should be scaled using this factor like so:

    self.f_size = int(self.SF * f_size)

The base Element position and bounding box attributes will be scaled when calling the constructor.

### GUI events

The Element base class provides `mouse_down` and `mouse_up` methods for handling click events. To connect these methods to 
task logic, we recommend overriding them using functions in the task GUI rather than the Element class itself. An example of 
this approach is shown below:

    def feed_mouse_up(self, _):
        self.clicked = False
        task.food.toggle(task.dispense_time)

    self.feed_button = ButtonElement(self, 129, 170, 50, 20, "FEED")
    self.feed_button.mouse_up = MethodType(feed_mouse_up, self.feed_button)

A similar strategy can be used to connect GUI elements to other portions of the task like the `get_text` method in
`InfoBoxElement`:

    def tone_count_text(self):
        return [str(task.cur_trial)]

    tone_count = InfoBoxElement(self, 242, 125, 50, 15, "NTONE", 'BOTTOM', ['0'])
    tone_count.get_text = MethodType(tone_count_text, tone_count)