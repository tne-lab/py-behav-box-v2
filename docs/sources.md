# Connecting to hardware with Sources

## Overview

Pybehave uses *Sources* to link [Components]() to external systems. Where *Components* are generally hardware-agnostic, 
*Sources* are implementation specific. *Sources* can communicate with a variety of hardware including DAQs, serial controllers,
video, or network events to control components with a unified framework. Sources are shared across [Tasks]() and are instead
specific to each piece of hardware connected to the [Workstation]()

## Registering components

The fundamental purpose of a *Source* is to connect a component to specific hardware which is done through the `register_component`
method. The `register_component` method takes a *Task* and *Component* as arguments to associate the component's address
with the corresponding hardware representation. Depending on the hardware that is being interfaced, overriding this method
may be as simple as keeping track of the components or require extensive interfacing with hardware libraries. 

## Reading from and writing to components

