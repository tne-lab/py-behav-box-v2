# Connecting to hardware with Sources

## Overview

Pybehave uses *Sources* to link [Components](components.md) to external systems. Where *Components* are generally hardware-agnostic, 
*Sources* are implementation specific. *Sources* can communicate with a variety of hardware including DAQs, serial controllers,
video, or network events to control components with a unified framework. Sources are shared across [Tasks](tasks.md) and 
specific to each piece of hardware connected to the [Workstation](workstation.md)

## Initialization

Sources have two methods related to initialization: the standard Python `__init__` and the pybehave specific `initialize`.
The former is used to declare all class attributes and indicate which variables are required to construct the Source from 
the Workstation interface. This method is called from the Workstation process and all variables declared in the method must 
be copied and sent via inter-process communication to create the Source. All code related to actually connecting the Source 
to hardware and any non-basic processing of class attributes should happen in the `initialize` method. 

## Registering components

The fundamental purpose of a *Source* is to connect a component to specific hardware which is done through the `register_component`
method. The `register_component` method takes a *Task* and *Component* as arguments to associate the component's address
with the corresponding hardware representation. Depending on the hardware that is being interfaced, overriding this method
may be as simple as keeping track of the components or require extensive interfacing with hardware libraries. 

## Reading from and writing to components

*Sources* are responsible for writing new values for Components out to hardware and reading new values for Components from hardware.
Depending on the type of *Source* one or both of these functionalities might be required. To implement behavior for writing to 
a Source, a user should override the `write_component` method. The `write_component` method is responsible for taking a component ID 
and a value to write (`msg`) and updates the hardware component accordingly. 
Reading from a *Source* typically requires the implementation of some form of asynchronous programming. One available option is
to instead have a custom *Source* overr
To control components *Sources* can override the `read_component` and `write_component` methods. Depending on the type of *Source*
one or both of these methods might be required. `read_component` takes a component ID as input and will return the current
value of the component (the type of the return value is left to the particular *Source* implementation). The `write_component` 
method takes a component ID and a value to write (`msg`) and updates the hardware component accordingly. 

## Closing components

Since some *Sources* might require functionality to relinquish control of certain hardware, two additional methods are provided:
`close_component` and `close_source`. `close_component` takes a component ID as input and alerts the system that the component
is no longer required. `close_component` is called when a task is removed from the chamber or refreshed. In contrast, `close_source`
is called when pybehave is exited or the *Source* is removed from the *Workstation*.

## Package Reference

### Source

#### register_component

    register_component(component: Component, metadata: Dict) -> None

Can be overridden to configure connection from the task to the selected component.

*Inputs:*

`component` the new Component to be registered with the Source.

`metadata` any metadata associated with this Component.

#### write_component

    write_component(component_id: str, msg: Any) -> None

Can be overridden to implement behavior for modifying the value of the indicated component through the interface represented by the Source.

*Inputs:*

`component_id` the ID associated with a Component connected to the Source that should be updated.

`msg` the new value for the Component.

#### update_component

    update_component(cid: str, value: Any, metadata: Dict = None) -> None

This method should be called to indicate a Component has updated based on new information from the Source.

*Inputs:*

`cid` the ID associated with the updated Component

`value` the new value received from the Source for the Component.

#### close_source

    close_source() -> None

Override to close all connections with the interface represented by the Source.

#### close_component

    close_component(component_id: str) -> None

Override to close the connection between a specific component and the interface represented by the Source.

#### output_file_changed

    output_file_changed(event: PybEvents.OutputFileChangedEvent) -> None

Override to implement behavior that should be executed when the output file is changed in the Workstation GUI.

#### constants_updated

    constants_updated(event: PybEvents.ConstantsUpdateEvent) -> None

Override to implement behavior that should be executed when constants are updated through the SubjectConfiguration widget.

#### unavailable

    unavailable() -> None

Call to signal to other processes that the Source has lost connection to the hardware.

### Included sources

#### WhiskerLineSource

    class WhiskerLineSource(ThreadSource):
        address: str ='localhost'
        port: int = 3233
        whisker_path: str = r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe")

Communicates with digital input and output lines represented via a connection to Whisker. This Source is only compatible with Windows.

*Unique Dependencies:*

`win32gui` used to check if there is an actively running Whisker Server 

*Attributes:*

`address` IP address for the computer running the Whisker Server. Use "localhost" if pybehave and Whisker are on the same machine.

`port` the port associated with the Whisker Server.

`whisker_path` the path to the Whisker executable

#### WhiskerTouchScreenSource

    class WhiskerTouchScreenSource(ThreadSource):
        address='localhost'
        port=3233
        display_num=0
        whisker_path=r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe")

Communicates with touchscreen objects represented via a connection to Whisker.

*Unique Dependencies:*

`win32gui` used to check if there is an actively running Whisker Server 

*Attributes:*

`address` IP address for the computer running the Whisker Server. Use "localhost" if pybehave and Whisker are on the same machine.

`port` the port associated with the Whisker Server.

`whisker_path` the path to the Whisker executable

#### OESource

    class OESource(ThreadSource):
        address: str
        in_port: str
        out_port: str

Source for coordinating connections to the networking system in OpenEphys. Make sure all events to/from OpenEphys are received/sent
in JSON mode.

*Attributes:*

`address` IP address for the computer running OpenEphys. Use "localhost" if pybehave and OpenEphys are on the same machine.

`in_port` the port associated with receiving messages from OpenEphys. Should typically correspond to the EventBroadcaster plugin.

`out_port` the port associated with sending message to OpenEphys. Should typically correspond to the NetworkEvents plugin.

#### OSControllerSource

    class OSControllerSource(ThreadSource):
        coms: List[str]

Source for coordinating connections to the Open Source Controller for Animal Research (OSCAR). Has functionality for digital and analog inputs and outputs.

*Unique Dependencies:*

`pyserial` used to communicate with the serial ports

*Attributes:*

`coms` list of serial port IDs corresponding to OSCAR interfaces.

#### SerialSource

    class SerialSource(Source)

Source for coordinating connections to serial devices.

*Unique Dependencies:*

`pyserial` used to communicate with the serial ports

#### VideoSource

    class VideoSource(ThreadSource):
        screen_width: int = None
        screen_height: int = None
        rows: int = None
        cols: int = None

Source for coordinating video recording with Webcams. Generally intended for sole use with Video components. Currently supports
standard USB webcams. 

*Unique Dependencies:*

`opencv` used to coordinate video acquisition, display, and serialization

`imutils` used to process the video stream

`qasync` used to visualize the video stream

*Attributes:*

`screen_width` the width of the display for the video interface in pixels

`screen_height` the height of the display for the video interface in pixels

`rows` the number of rows for the grid of individual videos in the interface

`cols` the number of columns for the grid of individual videos in the interface

#### HikVisionSource

    class HikVisionSource(Source):
        ip : str
        user : str
        password : str

Source for coordinating video recording with HikVision CCTV systems. Generally intended for sole use with Video components.
Recordings will start when the Video component is started and downloaded in a separate thread when the video is stopped.
By default, the source will draw a small black rectangle in the bottom left of the video to assist with synchronization.

*Unique Dependencies:*

`hikload` used to interface with the Hikvision ISAPI

*Attributes:*

`ip` the IP of the DVR

`user` the username of the administrator account on the DVR

`password` the password for the administrator account on the DVR

#### NIDAQSource

    class NIDAQSource(Source):
        dev : str

Source for coordinating connections to National Instruments hardware. Has functionality for digital and analog outputs.
Input functionality is currently not implemented.

*Unique Dependencies:*

`nidaqmx` used to interface with the NIDAQ API

*Attributes:*

`dev` the device ID of the DAQ


#### BayesOptSource

    class BayesOptSource()

Source for coordinating selection of arbitrary parameters (like stimulation or task variables) according to an outcome of interest 
using Bayesian optimization with gaussian process regression. Typically used with the general purpose `Both` component class.