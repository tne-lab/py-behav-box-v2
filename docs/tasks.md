# Programming tasks in pybehave

## Overview

Behavioral tasks in pybehave are implemented as state machines, the basic elements of which are states and events. To create
a task, the user develops a *task definition file* written in Python. Tasks are associated with a separate repository contained in the *py-behav-box-v2/source/Local* directory
which must have a nested *Tasks* folder. Task definitions are hardware-agnostic and solely program for task logic and timing, interacting with hardware or implementation specific
[Sources](sources.md) and [Events](events.md). Pybehave tasks are objects that are all subclasses of the base `Task` class with the ability to 
override functionality as necessary. All Tasks run in a separate Python process from the Workstation and Sources.

## States

At any time the task will be in one of a set of states defined by the user. States are represented as an [enum](https://docs.python.org/3/library/enum.html) 
with each state having a name and a corresponding ID:

    class States(Enum):
        INITIATION = 0
        RESPONSE = 1
        INTER_TRIAL_INTERVAL = 2

Each State should have a corresponding method included in the task definition which handles how the state responds to
relevant events. These methods are described in further detail below.

## Components

[Components](components.md) are abstractions that allow the task to communicate with external objects like levers, lights, or even network events
without details of the specific implementation. Every task must declare the names, numbers, and types of each Component by overriding
the `get_components` method. An example for a typical operant task is shown below:

    @staticmethod
    def get_components():
        return {
            'nose_pokes': [BinaryInput, BinaryInput, BinaryInput],
            'nose_poke_lights': [Toggle, Toggle, Toggle],
            'food': [TimedToggle],
            'house_light': [Toggle]
        }

This task utilizes infrared nose poke sensors, LED and incandescent lights, and a food dispenser that are abstracted as BinaryInputs,
Toggles, and a TimedToggle.

Components will be instantiated as attributes of the Task either as single objects or lists depending on the structure of each
entry in the `get_components` method. The specific [Source](sources.md) for these components can be specified using local [Address Files](protocols_addressfiles.md#addressfiles).
The indicated class type for each object only prescribes a super class; subclasses of the indicated type are also valid. If
an AddressFile is not provided, components can still be controlled directly from the task [GUI](guis.md).
Components can be accessed in task code as attributes of the task: `self.COMPONENT_NAME`.

## Constants

Many tasks have constants that control task progression without altering underlying logic. For example, there could be a need
for multiple sequences of trial types, different timing as training progresses, or variable completion criteria. Rather than having
to create new task definitions for changes of this sort, they can instead be explicitly defined using the `get_constants` method
and later modified using [Protocols](protocols_addressfiles.md#protocols). An example for the same operant task is shown below:

    def get_constants():
        return {
            'max_duration': 90,
            'inter_trial_interval': 7,
            'response_duration': 3,
            'n_random_start': 10,
            'n_random_end': 5,
            'rule_sequence': [0, 1, 0, 2, 0, 1, 0, 2],
            'correct_to_switch': 5,
            'light_sequence': random.sample([True for _ in range(27)] + [False for _ in range(28)], 55)
        }

This task has constants for controlling timing like task or trial durations as well as a default rule sequence. Additionally,
constants need not necessarily be identical every time the task is run but could be generated according to constant rules like the pseudo random `light_sequence`
in this example. Constants can be accessed in task code as attributes of the task: `self.CONSTANT_NAME`.

## Variables

Variables are used to track task features like trial counts, reward counts, or the value of particular inputs. The default values for variables
should be configured using the `get_variables` method:

    def get_variables():
        return {
            'cur_trial': 0,
            'cur_rule': 0,
            'cur_block': 0
        }

It is likely you will see warnings about instance attribute definitions outside `__init__` when using variables; these can be
safely ignored. Variables can be accessed in task code as attributes of the task: `self.VARIABLE_NAME`.

## Initial State

Every task must define the initial state it will be in by overriding the `init_state` method. Variables and constants are accessible 
as attributes when this method is called should the initial state depend on them. An example override is shown below:

    def init_state(self):
        return self.States.INITIATION

## Changing states

The current state can be changed using the `change_state` method. `change_state` will implicitly log *StateChangeEvents* that
can be handled by external *EventLoggers*. Additional metadata can also be passed to `change_state` if necessary for event
purposes. An example of using `change_state` with metadata is shown below:

    self.change_state(self.States.RESPONSE, {"correct": True})

## Task lifetime

Every task begins with an initialization via `init` that will contain any code that should be run when the task is first loaded
but before starting. When the task is started the `start` method is called. Unless stopped using `stop`
or paused using `pause`, the task will continuously call the `all_states` method followed by the current task state method
until it reaches the completion criteria defined by the method `is_complete` or the complete attribute is set to True. 
All of these methods can be overridden by the task to control behavior over its lifetime.


### init, start, stop, resume, and pause

Code can be executed when the task is loaded, starts, or stops to ensure certain hardware is enabled/disabled or initialize features 
of the task. Five methods exist for this purpose: `init`, `start`, `stop`, `resume`, and `pause`. There is no requirement to override
these methods unless particular behavior is necessary at these moments. No additional code needs to be written to handle task 
timing when using the `resume`, and `pause` methods.

### all_states

The `all_states` method is responsible for handling any event-related behavior that is independent of a particular state.
This can be useful for logging task completion after a certain timeout is reached, handling user input in the GUI, or general
task features that are identical across states.
An example implementation is shown below that handles a completion timeout:
    
    def all_states(self, event: PybEvents.PybEvent) -> bool:
        if isinstance(event, PybEvents.TimeoutEvent) and event.name == "task_complete":
            self.complete = True
            return True

### State methods

State methods are called when an event is received while the task is in the corresponding state. All logic for that particular state
should be handled by the state method along with transitions to subsequent states. The example below shows how a state
method could be used to reward following a bar press and transition to a lockout state:

    def REWARD_AVAILABLE(self):
        if self.pressed:
            self.food.toggle(self.dispense_time)
            if self.reward_lockout:
                self.lockout = self.reward_lockout_min + random.random() * (
                            self.reward_lockout_max - self.reward_lockout_min)
                self.change_state(self.States.REWARD_UNAVAILABLE)

## Time dependent behavior

Time dependent behavior can be implemented by calling methods from the base `Task` class. All timing should use these methods
to ensure no issues arise due to pausing and resuming the task. The `time_elapsed` method can be used to query the amount
of time that has passed since the task started. The `time_in_state` method can be used to query the amount of time since the
last state change. Both methods will not include any time spent paused. To have an event queued after a certain amount of time,
users can call one of a variety of timeout related methods described in more detail [below]():

### is_complete

The `is_complete` method returns a boolean indicating if the task has finished. This method will be called after events 
are handled to determine if the task has completed.

## Task GUIs

All pybehave tasks have GUIs written using [pygame](https://www.pygame.org/) functions that can reflect the state of task components and variables or control 
task features if necessary. Task GUIs are written as Python files in the *source/GUIs* folder and must be named TASK_NAMEGUI.py.
Further details on GUI development are available on the GUI [page](guis.md).

## Overriding tasks

Tasks can also be subclassed if a new Task has a high degree of overlap with an existing one. Each of the methods mentioned
above can be overriden and augmented as needed.

## Task Sequences

TaskSequences provide a way to run multiple tasks consecutively without loading each one individually. This is helpful in the case where multiple different tasks should be run back-to-back with no delay in between. The TaskSequence class is a subclass of Task, so many of the characteristics are similar, although they have a slightly different meaning. Creating TaskSequences requires no changes to the underlying Tasks that are being run. See the [tutorial](tutorials/creating_task_sequence.md) for an example of creating a TaskSequence

### Differences from Tasks

#### States

In TaskSequences, each member of the States enum represents an instance of a Task. The enum entries can be named anything and do not need to correspond to the names of the Tasks they represent. Thus if the same Task should be run multiple times within the sequence, we can differentiate them by giving the State entries different names. 

    class States(Enum):
        PRE_RAW = 0
        BAR_PRESS = 1
        POST_RAW = 2

Similar to Tasks, each of these States should have a corresponding method which dictates how events are handled within this state.


#### Event handling and switching tasks
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


#### Constants
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

Every TaskSequence must implement the `get_tasks` method which returns a list of all the Task classes that are contained within the sequence. For example, let's say the BarPress and Raw tasks should be combined in a sequence, then the `get_tasks` method would look be as follows:

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


### TaskSequence GUIs

SequenceGUIs are programmed in the same way as [Task GUIs](/guis). Elements in the SequenceGUI will be overlaid on top of the GUI for the current task throughout the entire duration of the sequence.

### Task similarities
[Variables](tasks.md#variables), [timing dependent behavior](tasks.md#time-dependent-behavior) and [task lifetime methods](tasks.md#task-lifetime) for TaskSequences are identical to Tasks.


## Class reference

The methods detailed below are contained in the `Task` class.

### Configuration methods

#### get_components

    get_components() -> Dict[str, List[Type[Component]]]

Returns a dictionary describing all the components used by the task. Each component name is linked to a list of Component types.

*Example override:*

    @staticmethod
    def get_components(): # Define components for a motorized bar press task
        return {
            'food_lever': [BinaryInput],
            'cage_light': [Toggle],
            'food': [TimedToggle],
            'fan': [Toggle],
            'lever_out': [ByteOutput],
            'food_light': [Toggle],
            'cam': [Video]
        }

#### get_constants

    get_constants() -> Dict[str, Any]

Returns a dictionary describing all the constants used by the task. Constants can be of any type and modified using [Protocols]().

*Example override:*

    @staticmethod
    def get_constants():
        return {
            'duration': 40,             # Task duration
            'reward_lockout_min': 25,   # Minimum time to lockout reward
            'reward_lockout_max': 35    # Maximum time to lockout reward
        }

#### get_variables

    get_variables() -> Dict[str, Any]

Returns a dictionary describing all the variables used by the task. Variables can be of any type.

*Example override:*

    @staticmethod
    def get_variables():
        return {
            'lockout': 0,   # Time to lockout reward for
            'presses': 0    # Number of times the bar has been pressed
        }

### Lifetime methods

#### init

    init() -> None

Called when the task is first loaded into the chamber.

#### clear

    clear() -> None

Called when the task is cleared from the chamber.

#### start

    start() -> None

Called when the task begins.

#### stop

    stop() -> None

Called when the task ends.

#### pause

    pause() -> None

Called when the task is paused.

#### resume

    resume() -> None

Called when the task is resumed.

#### is_complete

    is_complete() -> bool

### Control and timing methods

#### init_state

    init_state() -> Enum

Override to return the state the task should begin in (from the `States` enum).

#### change_state

    change_state(state : Enum, metadata : Any = None)

Call to change the state the task is currently in. Metadata can be provided which will be passed to the EventLogger
with the event information.

*Parameters:*

`state` the state in the Task States enum that should be entered.

`metadata` a dictionary containing any metadata that should be associated with the state change event.

#### time_elapsed

    time_elapsed() -> float

Returns the time that has passed in seconds (and fractions of a second) since the task began.

#### time_in_state

    time_in_state() -> float

Returns the time that has passed in seconds (and fractions of a second) since the current state began.

### Timeout methods

The methods below are associated with adding events to the stream related to timing.

#### set_timeout

    set_timeout(name: str, timeout: float, end_with_state=True, metadata: Dict = None) -> None

Begins a timer that will add a TimeoutEvent to the event stream after a prescribed duration.

*Parameters:*

`name` a string representing the name to be associated with the timeout.

`timeout` duration of the timeout in seconds.

`end_with_state` flag indicating whether the timeout should be removed when the state it was created in ends.

`metadata` a dictionary containing any metadata that should be associated with the TimeoutEvent.

#### cancel_timeout

    cancel_timeout(name: str) -> None

Ends the indicated timeout early without adding an event to the stream.

*Parameters:*

`name` the name for the timeout that should be cancelled.

#### pause_timeout

    pause_timeout(name: str) -> None

Pauses the indicated timeout.

*Parameters:*

`name` the name for the timeout that should be paused.

#### resume_timeout

    resume_timeout(name: str) -> None

Resumes a paused timeout.

*Parameters:*

`name` the name for the timeout that should be resumed.

#### extend_timeout

    extend_timeout(name: str, timeout: float) -> None

Adds a prescribed amount of time to a running timeout.

*Parameters:*

`name` the name for the timeout that should be extended.

`timeout` a duration in seconds to be added to the timeout.

### TaskSequence Methods

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