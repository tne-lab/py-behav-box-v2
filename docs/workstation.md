# Running tasks with the pybehave Workstation

## Overview

The Workstation GUI is responsible for controlling all user interactions with [Tasks](tasks.md). The interface presents all the necessary
controls for running tasks, configuring [Sources](sources.md), [Widgets](guis.md), and [EventLoggers](events.md), and visualizing behavior in real-time. Most configuration
is accessible from the menu bar while Tasks are controlled via *ChamberWidgets*.

![workstation.png](img/workstation.png)

## Adding a Task

To add a new Task to the Workstation, select *File->Add Task* from the menu bar. This will produce the following pop-up:

![add_task.png](img/add_task.png)

The *Task* dropdown allows for selection of which Task should be added. The list of tasks is generated based on the module 
names in the *source/Local/Tasks* folder. The *Chamber* dropdown indicates what index the Workstation should associate the Task with.
The number of chambers the Workstation supports is configurable and is described further [below](#workstation-settings). Once the desired values
have been selected from the dropdowns, the task can be added by clicking *OK*. Alternatively, the task can be loaded from a
[configuration file](#configurations) by clicking *Load Configuration*.

## ChamberWidgets

Each added task is associated with a *ChamberWidget* that provides all controls necessary for interacting with the task:

![chamber_widget](img/chamber_widget.png)

The number in the top-left indicates the chamber the task is associated with. The name/ID of the subject or participant can 
be indicated using the *Subject* textbox. The type of task currently loaded in this chamber is shown by the *Task* dropdown.
The user can load an [AddressFile](protocols_addressfiles.md#addressfiles) or [Protocol](protocols_addressfiles.md#protocols) by clicking the folder 
icons next to the corresponding fields which will bring up a file browser interface. Any data saved by the task using 
[EventLoggers](events.md) or linked external systems will be saved in the folder indicated by *Output Folder*. This path defaults to the 
*Desktop/py-behav-box-v2/TASK_NAME/Data/SUBJECT_NAME/DATE* directory. The task can be started by clicking the green play button
which will transition to an orange pause button and enable the red stop button once begun. All events logged by the task will
appear in the textbox at the bottom of the widget. To clear the chamber, right-click the widget and select *Clear Chamber*
from the menu.

### Configurations

Configurations allow tasks, AddressFiles, Protocols, subjects, chambers, and other information to be associated to streamline
the process of adding tasks to the Workstation. The configuration for a given task can be saved by right-clicking the ChamberWidget
and selecting *Save Configuration* from the menu. This will create a file in the *Desktop/py-behav-box/v2/Configurations* folder
that can later be loaded while adding a task to repopulate all previously configured fields. Further aspects of the configuration
can be modified by right-clicking the ChamberWidget and selecting *Edit Configuration* which will produce the following pop-up:

![edit_configuration.png](img/edit_configuration.png)

Any text entered in the *Prompt* textbox will be included in an alert before the task begins. This can serve as a reminder 
to start any required programs/processes or turn on external hardware. The add and remove buttons at the bottom of the pop-up
allow for configuring [EventLoggers](). The add button will produce a pop-up to select the type of EventLogger/Widget:

![event_loggers.png](img/event_loggers.png)

Depending on the type of EventLogger/Widget, a further pop-up may be raised to configure other attributes. Selectable options
in the dropdown are generated from the module names in *source/Events* that end in "EventLogger" or "Widget".

### Widgets

Additional GUI elements can be added to each ChamberWidget using subclasses of Widget. Each ChamberWidget includes a single TerminalWidget by
default but can be associated with any number of additional Widgets. Widgets are primarily used for sending Events via user input
to the associated Task or its EventLoggers or controlling external hardware/software manually from the pybehave GUI. 
While similar functionality can be implemented in Task GUIs, Widgets will have identical behavior regardless of the Task they are associated with.

#### Accessing events with EventWidget

EventWidget is an abstract subclass of Widget that provides access to the Task event stream. This functionality should only be necessary if
the Widget is intended for visualizing/displaying Task information or requires feedback from the Task

#### Configuration with SubjectConfigWidget

SubjectConfigWidget is a special purpose Widget that is integrated into the pybehave core. This Widget allows for overriding the
value of any Task constant for a particular subject. This is useful if constants need to be set on a per-subject basis. 
Values can also be made specific to the address file or protocol the subject is running on. Constants can also be updated while a task is running and will log 
ConstantUpdateEvents which can be analyzed offline or handled in Task code.

![subject_config.png](img/subject_config.png)

## Workstation Settings

Further settings for configuring the Workstation can be accessed from the menu bar by selecting *File->Settings* bringing 
up the following pop-up:

![settings.png](img/settings.png)

The number of chambers that can be controlled by this Workstation can be indicated by editing the *Chamber Count* textbox.
The list of sources indicating their names/IDs and types is shown in the *Sources* textbox.
The add and remove buttons at the bottom of the pop-up can be used to configure the Sources available to the Workstation.
The add button will produce a pop-up:

![add_source.png](img/add_source.png)

A name/ID for the source can be indicated by the *Name* textbox along with the *Source* type from the dropdown. Sources
in the dropdown are generated from the module names in *source/Sources*.

## Class reference

### Widget

The classes below are in the `Events` package and associated with Widgets.

#### Widget

    class Widget(QWidget):
        name: str

*Attributes:*

`name: str` the identifier given to this Widget

`cw: ChamberWidget` the ChamberWidget this Widget is associated with

*Methods:*

`set_chamber(cw: ChamberWidget) -> None` called when the Widget is successfully initialized and associated with the GUI

`close() -> None` called when the chamber is being cleared

#### EventWidget

    class EventWidgetWidget):
        name: str

*Attributes:*

`name: str` the identifier given to this Widget

*Methods:*

`handle_event(event: PybEvents.PybEvent) -> None` called when a new event is generated

`start() -> None` called when the Task starts

`stop() -> None` called when the Task ends

#### TerminalWidget

    class TerminalWidget(EventWidget):
        name: str

Widget showing the event stream in a terminal-like interface. Defaults to only display Loggable events.

#### SubjectConfigWidget
    
    class SubjectConfigWidget(EventWidget)

#### ManualWidget

    class ManualWidget(Widget):
        name: str

Widget providing the option to manually send an event to the stream. This is accomplished through a custom ManualEvent class 
which can be provided with a name/value pair by the GUI.

#### OEWidget

    class OEWidget(Widget):
        name: str
        address: str
        port: str

*Attributes:*

`name: str` the identifier given to this Widget

`address: str` the IP address for the computer running OpenEphys (localhost if on the same device)

`port: str` the port for the connection to OpenEphys

*Required Extras:* `oe`

Widget providing control over the OpenEphys acquisition system