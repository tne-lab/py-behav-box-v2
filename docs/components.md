# Creating and using Components

## Overview

Components are abstractions that allow tasks to communicate with external objects like levers, lights, or even network events
without details of the specific implementation. To develop a new component, the user creates a subclass of the base `Component`
class or preexisting component in the *py-behav-box-v2/source/Components* folder.

Typically, components do not enforce a particular physical implementation but abstract functionality that could be implemented
on a variety of hardware. For example, a *Toggle*, a component that can be set to be on or off, could be used
to represent a variety of hardware like lights, motors, or arbitrary digital outputs. Rather than having a separate component class
for each of these equivalent cases, the details of interacting with hardware are instead handled by implementation specific [Sources](sources.md).

## Defining the component type

All components have a type that indicates the types of data components either receive or output. Component types are represented
as an [enum](https://docs.python.org/3/library/enum.html) in the base `Component` class (see the [reference section](components.md#component-base-class) for the full type list). 
All subclasses of `Component` must override the `get_type` method which should return one of the possible indicated types.
Using the example of the `Toggle` component which solely outputs a simple digital on or off signal:

    def get_type():
        return Component.Type.DIGITAL_OUTPUT

## Component states

All components have states which represent how a component is behaving at any given time. There are no requirements for the data
type of a component's state but all components must override the `get_state` method. In the `Toggle` component example,
the method just returns a boolean indicating if the toggle is current on or off. However, `get_state` could return arbitrarily
complex objects for more flexible components like touch screens or analog inputs.

## Component constructor

All components are linked to a particular Source via a `component_id` and `component_address`. This linkage is mediated 
by a Task object `task`. When Components are used outside of Tasks (for Sources or GUIs) the Task parameter can be None. These three variables are
all passed to the component constructor along with `metadata` and configured using local [AddressFiles](protocols_addressfiles.md#addressfiles). 
All metadata will be processed to create class attributes corresponding to the entries in the dictionary. The component
constructor can be overridden if necessary to define variables for the component subclass (if necessary, these variables
can be locally configured using `metadata` in *AddressFiles*). Depending on the Component, some metadata may be required or
option (indicated in the package reference below). The example below shows how
the default constructor could be overridden to keep track of a state variable:

    def __init__(self, task, component_id, component_address):
        super().__init__(task, component_id, component_address)
        self.state = False

## Interacting with sources

To query data from the component's source, use the `Component` `get_state` method. To output to the Source use the `Component`
`write` method with a single input of any type. The type of data returned by `get_state` or required by `write` is flexible and can depend on the
`Source` class. Therefore, we recommend that these methods should be wrapped in component-specific versions like the `toggle`
method for `Toggle` components:

    def toggle(self, on):
        self.write(on)
        self.state = on

Rather than calling `write` or `get_state` directly, methods like `toggle` ensure states are properly updated and conventions for particular
types of components kept to. This is especially helpful when subclassing components when implementation specific features may 
be necessary (look at `BinaryInput` and `OEBinaryInput` for a more in depth example).
When new data is received from a Source, the behavior for updating the state of a Source is handled by the `update` method.
This method should return True if the value of the state was changed and False otherwise.

## Package reference

The methods and classes detailed below are contained in the `Components` package.

### Component base class

The `Component` class in the `Component` module is the super class for all components.

#### \_\_init__

    __init__(task : Task, component_id : str, component_address : str)

Constructor for a new component connecting to *Task* `task` registered with `component_id` at `component_address`.
Values for `task`, `component_id`, `component_address` should be provided by local [AddressFiles](protocols_addressfiles.md#addressfiles).
Any attributes (metadata) necessary for the component should be defined here (ex. frame rates for videos).

#### Type

    class Type(Enum)

Type is an enum representing the possible types of components to indicate expected data to a source. The possible component
types are shown below:

    DIGITAL_INPUT = 0   # The Component solely provides digital input
    DIGITAL_OUTPUT = 1  # The Component solely receives digital output
    ANALOG_INPUT = 2    # The Component solely provides analog input
    ANALOG_OUTPUT = 3   # The Component solely receives analog output
    INPUT = 4           # Arbitrary input type
    OUTPUT = 5          # Arbitrary output type
    BOTH = 6            # The Component both inputs and outputs (arbitrary type)

#### get_type

    get_type() -> None

Returns the component type as one of the symbolic names described in the `Type` class. This method must be overridden by 
all subclasses of `Component`.

*Example override:*

    def get_type(self):
        return Component.Type.DIGITAL_OUTPUT

#### get_state

    get_state() -> Any

Returns the state the component currently is in.

#### write
    
    write(msg : Any) -> None

Outputs a value via the source. The data type of `msg` will depend on the source.

*Example usage:*

    self.write(True)

#### update

    update(value: Any) -> bool

Process new information from the Source to update the Component's state.

#### close

    close() -> None

Notifies the source that the component should be closed.

*Example usage:*

    self.close()

### Component subclasses

#### Output

    class Output(Component)
    Type: OUTPUT

General purpose/non-specific output class. 

*Attributes:*

`state : Any` Current state value

#### Input

    class Input(Component)
    Type: INPUT

General purpose/non-specific input class.

*Attributes:*

`state : Any` Current state value

#### Both

    class Both(Component)
    Type: BOTH

General purpose/non-specific class that supports inputs and outputs.

*Attributes:*

`state : Any` Current state value

#### Toggle

    class Toggle(Output)
    Type: DIGITAL_OUTPUT

Toggles typically represent digital outputs like lights and motors and can be set to on or off states.

*Methods:*

`toggle(on : bool) -> None` Set the on/off state of the toggle.

*Attributes:*

`state : bool` Current state value (active/inactive)

#### BinaryInput

    class BinaryInput(Input)
    Type: DIGITAL_INPUT

BinaryInputs represent inputs that can only be on or off like switches, IR sensors, or levers.

*Attributes:*

`state : bool` Current state value (active/inactive)

#### AnalogInput

    class AnalogInput(Input)
    Type: ANALOG_INPUT

AnalogInputs represent inputs that can take on a continuous range of values like light, pressure, or temperature sensors.

*Methods:*

`check() -> float` Queries and returns the current value of the component.

*Attributes:*

`state : float` Current state value

#### AnalogOutput

    class AnalogOutput(Output)
    Type: ANALOG_OUTPUT

AnalogOutputs represent outputs that can take on a continuous range of values like intensity, frequency, and duration.

*Attributes:*

`state : float` Current state value

#### TimedToggle

    class TimedToggle(Toggle)
    Type: DIGITAL_OUTPUT

TimedToggles will only remain active for a set amount of time.

*Methods:*

`toggle(on : Union[float, bool]) -> None` Set the on/off state of the toggle either as an active duration or a steady on/off value.

*Attributes:*

`count: int` Counter for number of instances a timed event has occurred

#### OEBinaryInput

    class OEBinaryInput(BinaryInput)
    Type: DIGITAL_INPUT

OEBinaryInputs represent TTL broadcast events originating from [OpenEphys](https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Event-Broadcaster.html).
The class overrides the `check` method to handle the JSON data but has identical outputs to the standard BinaryInput.

*Optional Metadata:*

`rising: bool = True` Indicator for whether to respond to rising events

`falling: bool = False` Indicator for whether to respond to falling events

#### TouchBinaryInput

    class TouchBinaryInput(BinaryInput)
    Type: DIGITAL_INPUT

TouchBinaryInputs contain additional information about the location of an input for use with hardware like touchscreens. 

*Attributes:*

`definition: Any` Application specific description of the touch object

`pos: (int, int)` Tuple indicating the last location touched

#### Video

    class Video(Both)
    Type: BOTH

Video components represent the "barebones" information necessary for recording a video file.

*Methods:*

`start() -> None` Starts a video recording

`stop() -> None` Stops a video recording

*Attributes:*

`state: bool` Indicates if the video is currently being recorded

`name: str` Represents the name for the saved video file. Default implementation uses the current timestamp as the name

#### Stimmer

    class Stimmer(Output)
    Type: Output

Stimmer is an abstract class to consolidate the basic functionality required for stimulation.

*Methods:*

`parametrize(pnum : int, outs : list[int], per : int, dur : int, amps : ndarray, durs : list[int]) -> None` 
Defines a pulse train with ID `pnum`. The type of stimulation for each potential channel is indicated by a list of ints `outs`.
The stimulation has a period of `per`. The pulse train itself is described by a set of stages with amplitudes `amps` and durations `durs`.
The number of stages corresponds to the number of columns in `amps` which is equivalent to the length of `durs`. The number of rows in `amps` 
corresponds to the number of channels. This format was inspired by programming for the [StimJim](https://bitbucket.org/natecermak/stimjim/src/master/).

`start(pnum : int, stype: str) -> None` Starts the pulse train with ID `pnum`

#### StimJim

    class StimJim(Output)
    Type: Output

StimJim encapsulates behavior for a component that would accept a list of instructions to generate a stimulation waveform.
The default configuration is readily compatible with the [StimJim](https://bitbucket.org/natecermak/stimjim/src/master/).

*Methods:*

`trigger(ichan : int, pnum : int, falling : int = 0) -> None` Configures input `ichan` on the component to trigger the stimulation
pulse train with ID `pnum`. Defaults to trigger off a rising input but can be configured to falling inputs if `falling` is changed to 1.

`start(pnum : int, stype: str = 'T') -> None` Starts the pulse train with ID `pnum`

#### WaveformStim

    class WaveformStim(Output)
    Type: AnalogOutput

WaveformStim defines a stimulation waveform as a matrix given configuration parameters that could be output using a device like a DAQ.

*Methods:*

`parametrize(pnum : int, _, per : int, dur : int, amps : ndarray, durs : list[int]) -> None` 
Defines a pulse train with ID `pnum`.
The stimulation has a period of `per`. The pulse train itself is described by a set of stages with amplitudes `amps` and durations `durs`.
The number of stages corresponds to the number of columns in `amps` which is equivalent to the length of `durs`. The number of rows in `amps` 
corresponds to the number of channels. This format was inspired by programming for the [StimJim](https://bitbucket.org/natecermak/stimjim/src/master/).

`start(pnum : int, stype: str = None) -> None` Starts the pulse train with ID `pnum`