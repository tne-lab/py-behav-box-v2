# Creating and using Components

## Overview

Components are abstractions that allow tasks to communicate with external objects like levers, lights, or even network events
without details of the specific implementation. To develop a new component, the user creates a subclass of the base `Component`
class or preexisting component in the *py-behav-box-v2/source/Components* folder.

Typically, components do not enforce a particular physical implementation but abstract functionality that could be implemented
on a variety of hardware. For example, a *Toggle*, a component that can be set to be on or off, could be used
to represent a variety of hardware like lights, motors, or arbitrary digital outputs. Rather than having a separate component class
for each of these equivalent cases, the details of interacting with hardware are instead handled by implementation specific [Sources]().

## Defining the component type

All components have a type that indicates the types of data components either receive or output. Component types are represented
as an [enum](https://docs.python.org/3/library/enum.html) in the base `Component` class (see the [reference section](components.md#component-base-class) for the full type list). 
All subclasses of `Component` must override the `get_type` method which should return one of the possible indicated types.
Using the example of the `Toggle` component which solely outputs a simple digital on or off signal:

    def get_type(self):
        return Component.Type.DIGITAL_OUTPUT

## Component states

All components have states which represent how a component is behaving at any given time. There are no requirements for the data
type of a component's state but all components must override the `get_state` method. In the `Toggle` component example,
the method just returns a boolean indicating if the toggle is current on or off. However, `get_state` could return arbitrarily
complex objects for more flexible components like touch screens or analog inputs.

## Component constructor

All components are linked to a particular `source` via a `component_id` and `component_address`. These three variables are
all passed to the component constructor along with optional `metadata` and configured using local [AddressFiles](). The component
constructor can be overridden if necessary to define variables for the component subclass. The example below shows how
the default constructor could be overridden to keep track of a state variable:

    def __init__(self, source, component_id, component_address):
        super().__init__(source, component_id, component_address)
        self.state = False

## Interacting with sources

To query data from the component's source, use the `Component` `read` method. To output to the source use the `Component`
write method with a single input of any type. The type of data returned by `read` or required by `write` is flexible and can depend on the
`Source` class. Therefore, we recommend that these methods should be wrapped in component-specific versions like the `toggle`
method for `Toggle` components:

    def toggle(self, on):
        self.write(on)
        self.state = on

Rather than calling `write` or `read` directly, methods like `toggle` ensure states are properly updated and conventions for particular
types of components kept to. This is especially helpful when subclassing components when implementation specific features may 
be necessary (look at `BinaryInput` and `OEBinaryInput` for a more in depth example).

## Package reference

The methods and classes detailed below are contained in the `Components` package.

### Component base class

The `Component` class in the `Component` module is the super class for all components.

#### \_\_init__

    __init__(source, component_id, component_address)

Constructor for a new component connecting to *Source* `source` registered with `component_id` at `component_address`.
Values for `source`, `component_id`, `component_address` should be provided by local [AddressFiles](protocols_addressfiles.md).
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

    get_type()

Returns the component type as one of the symbolic names described in the `Type` class. This method must be overridden by 
all subclasses of `Component`.

*Example override:*

    def get_type(self):
        return Component.Type.DIGITAL_OUTPUT

#### get_state

    get_type()

Returns the state the component currently is in. This method must be overridden by all subclasses of `Component`.

*Example override:*

    def get_type(self):
        return self.state   # Assuming the state variable was pre-initialized and modified by other methods

#### read
    
    read()

Queries the current value of the component from the source. The data type returned by `read` will depend
on the source.

*Example usage:*

    value = self.read()

#### write
    
    write(msg)

Outputs a value via the source. The data type of `msg` will depend on the source.

*Example usage:*

    self.write(True)

#### close

    close()

Notifies the source that the component should be closed.

*Example usage:*

    self.close()

### Component subclasses

#### Toggle

    class Toggle(Component)
    DIGITAL_OUTPUT

Toggles typically represent digital outputs like lights and motors and can be set to on or off states.

*Example usage:*

    self.house_light.toggle(True)   # where house_light is a Toggle object

#### TimedToggle

    class TimedToggle(Toggle)
    DIGITAL_OUTPUT

TimedToggles will only remain active for a set amount of time.

*Example usage:*

    self.food.toggle(0.7)   # where food is a TimedToggle object that should be active for 0.7s

#### BinaryInput

    class BinaryInput(Component)
    DIGITAL_INPUT

BinaryInputs represent inputs that can only be on or off like switches, IR sensors, or levers. The `check` method will
indicate if the state has changed compared to the last time it was queried.

*Example usage:*

    value = self.poke.check()
        if value == BinaryInput.ENTERED:
            pass # Do something
        elif value == BinaryInput.EXIT:
            pass # Do something else

#### OEBinaryInput

    class OEBinaryInput(BinaryInput)
    DIGITAL_INPUT

OEBinaryInputs represent TTL broadcast events originating from [OpenEphys](https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Event-Broadcaster.html).
The class overrides the `check` method to handle the JSON data but has identical outputs to the standard BinaryInput.

#### TouchScreen

    class TouchScreen(Component)
    BOTH

TouchScreens are abstracted representations of touch screens that provide a framework for adding images to the screen (the output)
and receiving touches (the input). The `add_image` and `remove_image` methods can be used to add or remove images from the screen
which is updated via the `refresh` method. Touches can be received and handled via the `get_touches` and `handle` methods respectively.

*Example usage:*

    