# Creating a new component

In the following tutorial, we will show all the basic features that need to be programmed to build a Component from scratch
in pybehave. A user might decide to create a new component if their specific hardware has additional features that aren't fully
captured by the existing abstractions. 

## Component overview

Creating new components is relatively simple requiring only four steps: choosing which subclass of Component to extend,
defining the Component type, setting up the `__init__` method, and specifying update behavior. Additional methods and functionality
can of course be added and interacted with from a Task or GUI but these four steps are the only ones that are absolutely required.

## Subclassing

All components inherit at some level from the base Component class. However, a new custom component can inherit one of the many 
subclasses to reuse some functionality. The choice of which class gets extended depends on how much behavior the new custom component
needs to add/replace. Additionally, subclassing a component can make the custom component compatible with tasks that only specify
the base class in their `get_components` methods. One good example is the OEBinaryInput component that adds additional functionality
to the base BinaryInput class to make it compatible with the information format received from OpenEphys. This component has
the following class declaration:

    class OEBinaryInput(BinaryInput):

## Component types

All components are one of six types: DIGITAL_INPUT, DIGITAL_OUTPUT, ANALOG_INPUT, ANALOG_OUTPUT, INPUT, OUTPUT, or BOTH.
These types have varying levels of restrictions on the kind of data that component is expected to handle which can be used
by a connected Source to format the data it forwards to a component. The type for a custom component is indicated by overriding
the `get_type` method:

    @staticmethod
        def get_type() -> Component.Type:
            return Component.Type.DIGITAL_INPUT

This method only needs to be overridden if extending the base Component class or if the type of the custom component differs
from the class it's extending.

## The `__init__` method

The component `__init__` method takes the task, component ID, and component address as inputs. The method only needs to be
overridden if the custom component has to set default values for the component state that differ from the super class or define
other attributes. If new attributes are declared, these can be overridden with values from the metadata field in the corresponding
AddressFile entry. An example of declaring these custom attributes is shown below for the OEBinaryInput:

    def __init__(self, task: Task, component_id: str, component_address: str):
        super().__init__(task, component_id, component_address)
        self.rising = True
        self.falling = False

## `update`

The `update` method should be overridden to specify the data type that this component expects to receive from a Source and 
implement the correct behavior in response. If the state of the component has changed based on the information it has received,
this method should return true and false otherwise. An example override for the OEBinaryInput is shown below that handles
input data specifically in the form of a `dict`:

    def update(self, value: dict) -> bool:
        if self.rising and self.falling:
            if not self.state and value['metaData']['Direction'] == '1' and value['data']:
                self.state = True
                return True
            elif self.state and value['metaData']['Direction'] == '0' and not value['data']:
                self.state = False
                return True
        else:
            if not self.state and value['data']:
                self.state = True
                return True
            elif self.state and not value['data']:
                self.state = False
                return True
        return False