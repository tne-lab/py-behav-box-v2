# TaskSequences in pybehave

## Overview

TaskSequences provide a way to run multiple tasks consecutively without loading each one individually. This is helpful in the case where multiple different tasks should be run back-to-back with no delay in between. The TaskSequence class is a subclass of Task, so many of the characteristics are similar, although they have a slightly different meaning. Creating TaskSequences requires no changes to the underlying Tasks that are being run. See the [tutorial](tutorials/creating_task_sequence.md) for an example of creating a TaskSequence

## Differences from Tasks

### States

In TaskSequences, each member of the States enum represents an instance of a Task. The enum entries can be named anything and do not need to correspond to the names of the Tasks they represent. Thus if the same Task should be run multiple times within the sequence, we can differentiate them by giving the State entries different names. 

    class States(Enum):
        PRE_RAW = 0
        BAR_PRESS = 1
        POST_RAW = 2

Similar to Tasks, each of these States should have a corresponding method which dictates how events are handled within this state.


### Event handling and switching tasks
Event handling in TaskSequences is similar to Tasks in that the sequence `all_states` method will be called with the event first. If the event isn't handled here, then the funcion corresponding to the sequence's current state method will be called. 

One critical event that should be handled by TaskSequences is the `TaskCompleteEvent`. This event indicates that the current Task has completed, and the sequence should move on to the next Task.

Rather than calling the `change_state` method like a normal Task, a TaskSequence should call the `switch_task` method.

    def switch_task(self, task: Type[Task], seq_state: Enum, protocol: str, metadata: Any = None) -> None:

This method takes the new Task type, the TaskSequence state to change to, the protocol file for the new task, and optionally any metadata. An example use is as follows:

    def PRE_RAW(self, event):
        if isinstance(event, PybEvents.TaskCompleteEvent):
            self.switch_task(BarPress, self.States.BAR_PRESS, self.bar_press_protocol, event.metadata)
            return True
        return False


### Constants
Protocol files for the underlying Tasks as well as other sequence-level constants can be defined within the `get_constants` method. To use the default values for a Task's constants, `None` can be provided for the protocol file. For example:

    def get_constants():
        return {
            'pre_raw_protocol': "/path/to/pre_raw/protocol",
            'bar_press_protocol': "/path/to/bar_press/protocol",
            'post_raw_protocol': None
        }

In this case, the first run of the Raw task will use a specific protocol while the second will be run with the default values. 

Similar to Tasks, the default values for sequence-level constants can be overridden by providing a protocol file for the TaskSequence itself through the GUI. In other words, a protocol file at the TaskSequence level can be used to load various protocol files for each of the individual Tasks being run.

### Additional Methods
There are a few methods that must be implemented in TaskSequences that aren't present in normal Tasks.

#### get_tasks

Every TaskSequence must implement the `get_tasks` method which returns a list of all of the Task classes that are contained within the sequence. For example, let's say the BarPress and Raw tasks should be combined in a sequence, then the `get_tasks` method would look be as follows:

    @staticmethod
    def get_tasks():
        return [BarPress, Raw]

Note that each Task should only be included once in this list, regardless of how many times it runs within the sequence.

#### Components
Each of the Tasks within the sequence will already have its own Components declared within it, but Components can also be declared at the TaskSequence level meaning they can be interacted with throughout the entire sequence, regardless of which Task is running. To add such components, the `get_sequence_components` method can be overriden. 

    @staticmethod
    def get_sequence_components():
        return {
            'cam': [Video]
        }

#### Initial State and sequence

Similar to Tasks, a TaskSequence must override the `init_state` method which returns one of the members of its States enum.

Additionally, TaskSequences must override the `init_sequence` method which returns a tuple containing the first Task and the file location of the first protocol.

    def init_sequence(self) -> tuple[Type[Task], str]

For example:

    def init_sequence(self):
        return Raw, self.pre_raw_protocol


## TaskSequence GUIs

SequenceGUIs are programmed in the same way as [Task GUIs](/guis). Elements in the SequenceGUI will be overlaid on top of the GUI for the current task throughout the entire duration of the sequence.

## Task similarities
[Variables](tasks.md#variables), [timing dependent behavior](tasks.md#time-dependent-behavior) and [task lifetime methods](tasks.md#task-lifetime) for TaskSequences are identical to Tasks.


## Class reference

In addition to the [methods](tasks.md#configuration-methods) included in the `Task` class, the following methods detailed below are contained in the `TaskSequence` class.

### Configuration methods

#### get_tasks

    get_tasks() -> List[Type[Task]]

Returns a list of all the Task classes used in the sequence.

*Example override:*

    @staticmethod
    def get_tasks():
        return [Raw, BarPress]

#### init_sequence

    init_sequence(self) -> tuple(Type[Task], str)

Returns a tuple containing the type of the first Task and the protocol file to be used for that Task.

*Example override:*

    def init_sequence(self):
        return Raw, self.pre_raw_protocol

#### get_sequence_components

    get_sequence_components() -> Dict[str, List[Type[Component]]]

Returns a dictionary describing all the components used by the sequence. Each component name is linked to a list of Component types.

*Example override:*

    def get_sequence_components():
        return {
            'cam': [Video]
        }
