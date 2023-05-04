# Programming tasks in pybehave

## Overview

Behavioral tasks in pybehave are implemented as state machines, the basic elements of which are states and components. To create
a task, the user develops a *task definition file* written in Python. Tasks are associated with a Git submodule contained in the *py-behav-box-v2/source/Local* directory
which must have a nested *Tasks* folder. Task definitions are hardware-agnostic and solely program for task logic and timing, interacting with hardware or implementation specific
[Sources](sources.md) and [Events](events.md). Pybehave tasks are objects that are all subclasses of the base `Task` class with the ability to 
override functionality as necessary.

## States

At any time the task will be in one of a set of states defined by the user. States are represented as an [enum](https://docs.python.org/3/library/enum.html) 
with each state having a name and a corresponding ID:

    class States(Enum):
        INITIATION = 0
        RESPONSE = 1
        INTER_TRIAL_INTERVAL = 2

Each State should have a corresponding method included in the task definition which handles the logic for that state and
transitions. These methods are described in further detail below.

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
an AddressFile is not provided, components can be controlled directly from the task [GUI](guis.md).
Components can be accessed in task code as attributes of the task: `self.COMPONENT_NAME`.

## Constants

Many tasks have constants that control task progression without altering underlying logic. For example, there could be a need
for multiple sequences of trial types, different timing as training progresses, or variable completion criteria. Rather than having
to create new task definitions for changes of this sort, they can instead be explicitly defined using the `get_constants` method
and later modified using [Protocols](protocols_addressfiles.md#protocols). An example for the same operant task is shown below:

    def get_constants(self):
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

    def get_variables(self):
        return {
            'cur_trial': 0,
            'cur_rule': 0,
            'cur_block': 0
        }

It is likely you will see warnings about instance attribute definitions outside `__init__` when using variables; these can be
safely ignored. Constant attributes will already be available when `get_variables` is called and can be used in the method.
Variables can be accessed in task code as attributes of the task: `self.VARIABLE_NAME`.

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

## Time dependent behavior

Time dependent behavior can be implemented by calling methods from the base `Task` class. All timing should use these methods
to ensure no issues arise due to pausing and resuming the task. The `time_elapsed` method can be used to query the amount
of time that has passed since the task started. The `time_in_state` method can be used to query the amount of time since the
last state change. Both methods will not include any time spent paused.

## Events

Events are used to communicate information from the task to [*EventLogger*]() classes that can complete a variety of roles like
saving task data, communicating with external programs, or sending digital codes for synchronization. Every task has an `events`
attribute that can be appended to and later parsed by various *EventLoggers*.

### Inputs

Inputs are used to communicate event information from Components that provide input to the task.
Like states, inputs are also represented as an enum with each input having a name and a corresponding ID. The example below 
shows how to structure inputs for three possible components with distinction between when the component is entered versus exited:

    class Inputs(Enum):
        FRONT_ENTERED = 2
        FRONT_EXIT = 3
        MIDDLE_ENTERED = 4
        MIDDLE_EXIT = 5
        REAR_ENTERED = 6
        REAR_EXIT = 7

An example of how to log such an Input event is shown below:

    self.events.append(InputEvent(self, self.Inputs.FRONT_ENTERED))

## Task lifetime

Every task begins with an initialization via `init` that will contain any code that should be run when the task is first loaded
but before starting. When the task is started the `start` method is called. Unless stopped using `stop`
or paused using `pause`, the task will continuously call the `handle_input` method followed by the current task state method
until it reaches the completion criteria defined by the method `is_complete`. All of these methods can be overridden by the 
task to control behavior over its lifetime.


### start, stop, resume, and pause

Code can be executed when the task starts or stops to ensure certain hardware is enabled/disabled or initialize features 
of the task. Four methods exist for this purpose: `start`, `stop`, `resume`, and `pause`. There is no requirement to override
these methods unless particular behavior is required at these moments. No additional code needs to be written to handle task 
timing when using the `resume`, and `pause` methods.

### handle_input

The `handle_input` method is responsible for querying the values of all input components. These values can be stored in a
variable for future use, logged as events, or responded to directly. An example method which logs events and updates variables
is shown below:

    def handle_input(self):
        food_lever = self.food_lever.check()
        self.pressed = False
        if food_lever == BinaryInput.ENTERED:
            self.events.append(InputEvent(self, self.Inputs.LEVER_PRESSED))
            self.pressed = True
            self.presses += 1
        elif food_lever == BinaryInput.EXIT:
            self.events.append(InputEvent(self, self.Inputs.LEVER_DEPRESSED))

### State methods

State methods are repeatedly called while the task is in the corresponding state. All logic for that particular state
should be handled by the state method along with transitions to subsequent states. The example below shows how a state
method could be used to reward following a bar press and transition to a lockout state:

    def REWARD_AVAILABLE(self):
        if self.pressed:
            self.food.toggle(self.dispense_time)
            if self.reward_lockout:
                self.lockout = self.reward_lockout_min + random.random() * (
                            self.reward_lockout_max - self.reward_lockout_min)
                self.change_state(self.States.REWARD_UNAVAILABLE)

### is_complete

The `is_complete` method returns a boolean indicating if the task has finished. This method must be overridden
and will be called alongside `main_loop` to determine if the task is complete.

    def is_complete(self):
        return self.time_elapsed() > self.duration * 60.0

## Task GUIs

All pybehave tasks have GUIs written using [pygame](https://www.pygame.org/) functions that can monitor task components and variables or control 
task features if necessary. Task GUIs are written as Python files in the *source/GUIs* folder and must be named TASK_NAMEGUI.py.
Further details on GUI development are available on the GUI [page](guis.md).

## Overriding tasks

Tasks can also be subclassed if a new Task has a high degree of overlap with an existing one. Each of the methods mentioned
above can be overriden and augmented as needed.

## Class reference

The methods detailed below are contained in the `Task` class.

### Configuration methods

#### get_components

    get_components()

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

    get_constants()

Returns a dictionary describing all the constants used by the task. Constants can be of any type and modified using [Protocols]().

*Example override:*

    def get_constants(self):
        return {
            'duration': 40,             # Task duration
            'reward_lockout_min': 25,   # Minimum time to lockout reward
            'reward_lockout_max': 35    # Maximum time to lockout reward
        }

#### get_variables

    get_variables()

Returns a dictionary describing all the variables used by the task. Variables can be of any type.

*Example override:*

    def get_variables(self):
        return {
            'lockout': 0,   # Time to lockout reward for
            'presses': 0    # Number of times the bar has been pressed
        }

### Lifetime methods

#### init

    init()

Called when the task is first loaded into the chamber.

#### clear

    clear()

Called when the task is cleared from the chamber.

#### start

    start()

Called when the task begins.

#### stop

    stop()

Called when the task ends.

#### pause

    pause()

Called when the task is paused.

#### resume

    resume()

Called when the task is resumed.

#### is_complete

    is_complete()

### Control and timing methods

#### init_state

    init_state()

Override to return the state the task should begin in (from the `States` enum).

#### change_state

    change_state(state, metadata=None)

Call to change the state the task is currently in. Metadata can be provided which will be passed to the EventLogger
with the event information.

#### time_elapsed

    time_elapsed()

Returns the time that has passed in seconds (and fractions of a second) since the task began.

#### time_in_state

    time_in_state()

Returns the time that has passed in seconds (and fractions of a second) since the current state began.