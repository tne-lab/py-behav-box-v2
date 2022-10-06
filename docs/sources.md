# Connecting to hardware with Sources

## Overview

Pybehave uses *Sources* to link [Components](components.md) to external systems. Where *Components* are generally hardware-agnostic, 
*Sources* are implementation specific. *Sources* can communicate with a variety of hardware including DAQs, serial controllers,
video, or network events to control components with a unified framework. Sources are shared across [Tasks](tasks.md) and 
specific to each piece of hardware connected to the [Workstation](workstation.md)

## Registering components

The fundamental purpose of a *Source* is to connect a component to specific hardware which is done through the `register_component`
method. The `register_component` method takes a *Task* and *Component* as arguments to associate the component's address
with the corresponding hardware representation. Depending on the hardware that is being interfaced, overriding this method
may be as simple as keeping track of the components or require extensive interfacing with hardware libraries. 

## Reading from and writing to components

To control components *Sources* can override the `read_component` and `write_component` methods. Depending on the type of *Source*
one or both of these methods might be required. `read_component` takes a component ID as input and will return the current
value of the component (the type of the return value is left to the particular *Source* implementation). The `write_component` 
method takes a component ID and a value to write (`msg`) and updates the hardware component accordingly. 

## Closing components

Since some *Sources* might require functionality to relinquish control of certain hardware, two additional methods are provided:
`close_component` and `close_source`. `close_component` takes a component ID as input and alerts the system that the component
is no longer required. `close_component` is called when a task is removed from the chamber or refreshed. In contrast, `close_source`
is called when pybehave is exited.

## Package Reference

### Source base class

### Included sources

#### EmptySource

#### EmptyTouchScreenSource

#### HikVisionSource

#### NIDAQSource

#### NIWhiskerSource

#### OESource

#### OSControllerSource

#### SerialSource

#### VideoSource

#### WhiskerTouchScreenSource