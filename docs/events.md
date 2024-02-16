# Logging events

## Overview

The various parts of the Pybehave framework are connected through a single, unified event system. These events are relayed via
inter process communication between the Workstation, main TaskProcess, and Sources.

## Event objects

All events subclass the base *PybEvent* class which sets a number of flags to allow for serialization via the msgspec protocol. 
This class is heavily subclassed to represent numerous possible types of Events that could be leveraged by various tasks or external systems. 

### Task-related events

While events can be customized for specific needs, there are a few default Event classes that can represent the majority
of task information across systems. All task-related events subclass the base *TaskEvent* class which adds a
field representing the chamber the event is associated with. Events that happen during the task also have related timing information
and are represented by the *TimedEvent* subclass of *TaskEvent*. *TimedEvent* has two further subclasses, *StatefulEvent* and *LoggableEvent*,
that are used to forward events to the state-related task methods or event logging system respectively. A full overview of
the available subclasses is described below.

### Source-related events

An additional set of events are available specifically for communicating with Sources. Additional information on interacting
with these events is included in the Sources documentation.

## EventLoggers

EventLoggers handle *LoggableEvents* to complete desired tasks like serialization or forwarding to external systems. 
The core method of the EventLogger class, `log_events` will receive
the list of events produced by its corresponding task in the last event cascade. All EventLoggers will receive the full
list of events. Different logic cases can be written in the method to ensure EventLoggers only capture events of interest and vary behavior based on the *Event* subclass.
For example, the `OENetworkLogger` class has a case for handling `OEEvents` while all other EventLoggers do not.
An example `log_events` override for the core event types is shown below:

    def log_events(self, events):
        for e in events:
            self.event_count += 1
            if isinstance(e, InitialStateEvent):
                # Log for InitialStateEvent
            elif isinstance(e, FinalStateEvent):
                # Log for FinalStateEvent
            elif isinstance(e, StateChangeEvent):
                # Log for end of prior state
                self.event_count += 1
                # Log for beginning of new state
            elif isinstance(e, InputEvent):
                # Log for InputEvent
        super().log_events(events)  # Sometimes the super class method should be called

All EventLoggers have an `event_count` attribute for tracking the number of events that have been handled by the logger.
Additional EventLogger parameters for particular subclasses can be provided when added to the [Workstation](workstation.md).

### start, stop, and close

The EventLogger class also provides three additional methods that will be called when the task begins, ends, or is cleared: `start`, `stop`, and `close`.
These methods do not have to be overridden but the `start` method will reset `event_count` each time it is called.

### FileEventLoggers

FileEventLogger is a subclass of EventLogger with additional functionality for handling file saving. The `start` and `close`
methods of FileEventLogger ensure that files are opened and closed when needed. Additionally, the `log_events` method will flush
the file regularly if called by its subclass. To use a FileEventLogger, the user needs to override the `get_file_path`method
which will return the path to the file that should be saved. This path will then be used to open a file stored in the `log_file`
attribute. FileEventLoggers will default to saving to the *Desktop/py-behav-v2/TASK_NAME/Data/SUBJECT_NAME/DATE* folder which
is represented in the class by the `output_folder` attribute. An example override of `get_file_path` used by CSVEventLogger is shown below:

    def get_file_path(self):
        return "{}{}.csv".format(self.output_folder, math.floor(time.time() * 1000))

## Package reference

The classes detailed below are contained in the `PybEvents` module.

### Core events

#### PybEvent

    class PybEvent(msgspec.Struct, kw_only=True, tag=True, omit_defaults=True, array_like=True):
        metadata: Dict = {}

Base event class

*Attributes:*

`metadata` a dictionary containing any metadata that should be associated with the event

#### ErrorEvent

    class ErrorEvent(PybEvent):
        error: str
        traceback: str

Event class for forwarding errors to the Workstation process. These events should be logged if a user needs to be notified
in the GUI that an error occurred.

*Attributes:*

`error` the name of the error

`traceback` descriptive text related to the error

#### PygameEvent

    class PygameEvent(PybEvent):
        event_type: int
        event_dict: Dict

Associated with internal events in the pygame-based Task GUIs

*Attributes:*

`event_type` pygame event code

`event_dict` all metadata for the event

#### ExitEvent

    class ExitEvent(PybEvent)

Event associated with Pybehave exiting

#### HeartbeatEvent

    class HeartbeatEvent(PybEvent)

Regular event sent from the main Task process to the Workstation to keep the GUI updated and verify connectivity.

### Task-related events

#### TaskEvent

    class TaskEvent(PybEvent):
        chamber: int

Base class for events specifically related to a Task.

*Attributes:*

`chamber` the chamber ID the Task the event refers to is associated with

#### TimedEvent

    class TimedEvent(TaskEvent, kw_only=True, tag=True, omit_defaults=True, array_like=True):
        timestamp: typing.Optional[float] = None

Base class for events that should be associated with a particular time-point in the task.

*Attributes:*

`timestamp` the time in seconds when the event occurred relative to the beginning of the task

*Methods:*

`acknowledge(timestamp : float) -> None:` record the time when this event was handled

#### StatefulEvent

    class StatefulEvent(TimedEvent)

Base class for events that should be forwarded to the relevant Task state methods

#### LoggableEvent

    class Loggable(TimedEvent)

Base class for events that should be forwarded to EventLoggers

*Methods:*

`format(self) -> LoggerEvent:` must be overridden by subclasses to format an event for logging

#### AddTaskEvent

    class AddTaskEvent(TaskEvent):
        task_name: str
        task_event_loggers: str

Event for instantiating a new Task

*Attributes:*

`task_name` the class name for the Task formatted as a string

`task_event_loggers` a string encoding instructions to create the EventLoggers for the Task

#### ClearEvent

    class ClearEvent(TaskEvent):
        del_loggers: bool

Event for removing a Task

*Attributes:*

`del_loggers` flag indicating if any associated loggers should be closed along with the Task

#### InitEvent

    class InitEvent(TaskEvent)

Event associated with a Task successfully being added

#### StartEvent

    class StartEvent(TaskEvent)

Event associated with a Task starting

#### StopEvent

    class StopEvent(TaskEvent)

Event associated with a Task stopping

#### ResumeEvent

    class ResumeEvent(Loggable, StatefulEvent)

Event associated with a Task resuming

#### PauseEvent

    class PauseEvent(Loggable, StatefulEvent)

Event associated with a Task pausing

#### AddLoggerEvent

    class AddLoggerEvent(TaskEvent):
        logger_code: str

Event associated with adding a new EventLogger to a Task

*Attributes:*

`logger_code` string representation of instruction to instantiate the EventLogger

#### RemoveLoggerEvent

    class RemoveLoggerEvent(TaskEvent):
        logger_name: str

Event associated with removing an EventLogger from a Task

*Attributes:*

`logger_name` the given name for the EventLogger to be removed

#### OutputFileChangedEvent

    class OutputFileChangedEvent(TaskEvent):
        output_file: str
        subject: str

Event associated with a change in the save directory or subject name for the Task

*Attributes:*

`output_file` the path where Task data should be saved

`subject` the name of the subject completing the Task

#### ComponentUpdateEvent

    class ComponentUpdateEvent(TimedEvent):
        comp_id: str
        value: Any

Event associated with a change in the state/value of a Component

*Attributes:*

`comp_id` the ID of the Component

`value` the new value for the Component

#### ComponentChangedEvent

    class ComponentChangedEvent(Loggable, StatefulEvent):
        comp: Component
        index: int

Simplified version of ComponentUpdateEvent to be used by Task state methods

*Attributes:*

`comp` the Component that has recently changed state/value

`index` the internal index of the Component

#### TaskCompleteEvent

    class TaskCompleteEvent(TaskEvent)

Event associated with completion of the Task

#### TimeoutEvent

    class TimeoutEvent(Loggable, StatefulEvent):
        name: str

Event associated with task behavior that should begin after a set period of time

*Attributes:*

`name` a string that identifies the specific timeout

#### StateEnterEvent

    class StateEnterEvent(Loggable, StatefulEvent):
        name: str
        value: int

Event associated with the beginning of a state

*Attributes:*

`name` a string identifying the name of the state matching one of the values in the States enum

`value` a numeric identifier for the state corresponding to the States enum

#### StateExitEvent

    class StateExitEvent(Loggable, StatefulEvent):
        name: str
        value: int

Event associated with the end of a state

*Attributes:*

`name` a string identifying the name of the state matching one of the values in the States enum

`value` a numeric identifier for the state corresponding to the States enum

#### GUIEvent

    class GUIEvent(Loggable, StatefulEvent):
        name: str
        value: int

Event associated with a user input in the Task's GUI

*Attributes:*

`name` a string identifying the name of the event

`value` a numeric identifier for the event

#### InfoEvent

    class InfoEvent(Loggable):
        name: str
        value: int

Event associated with information that should be sent to EventLoggers and GUI but won't be handled by the Task event methods.

*Attributes:*

`name` a string identifying the name of the event

`value` a numeric identifier for the event

### Source-related events

#### AddSourceEvent

    class AddSourceEvent(PybEvent):
        sid: str
        conn: PipeConnection

Event associated with adding a new Source to pybehave.

*Attributes:*

`sid` the unique identifier/name given to the Source

`conn` a Pipe object for interprocess communication

#### RemoveSourceEvent

    class RemoveSourceEvent(PybEvent):
        sid: str

Event associated with removing a Source from pybehave.

*Attributes:*

`sid` the unique identifier/name given to the Source

#### CloseSourceEvent
    
    class CloseSourceEvent(PybEvent)

Event associated with ending a Source.

#### UnavailableSourceEvent

    class UnavailableSourceEvent(PybEvent):
        sid: str

Event associated with a Source signaling to the main process that it no longer has an active connection to its corresponding
hardware/software.

*Attributes:*

`sid` the unique identifier/name given to the Source

#### ComponentRegisterEvent

    class ComponentRegisterEvent(PybEvent):
        comp_type: str
        cid: str
        address: typing.Union[str, typing.List[str]]

Event associated with registering a Component with the Source.

*Attributes:*

`comp_type` the object type of the Component

`cid` the ID of the component

`address` the address in the Source that should be associated with this Component

#### ComponentClosedEvent

    class ComponentCloseEvent(PybEvent):
        comp_id: str

Event associated with the request to close the hardware/software connection with a particular Component.

*Attributes:*

`comp_id` the ID of the component

### EventLoggers

The classes detailed below are contained in the `Events` package and associated with event logging.

#### EventLogger

    class EventLogger:
        name: str

Base EventLogger class

*Attributes:*

`name` a string identifying the name associated with this EventLogger

*Methods:*

`start() -> None:` called when the Task is started

`stop() -> None:` called when the Task is stopped

`close() -> None:` called when the Task is cleared. Should be used to free resources that require it.

`set_task(task: Task) -> None:` called when the EventLogger is first associated with a Task

`log_events(events: collections.deque[LoggerEvent]) -> None:` must be overriden to specify how events should be logged

`format_event(le: LoggerEvent, event_type: str) -> str:` translates a LoggerEvent into a representative string

#### LoggerEvent

     class LoggerEvent:
        event: TaskEvent
        name: str
        eid: int
        entry_time: float

Container class for encapsulating all the information necessary to log a TaskEvent

*Attributes:*

`event` the TaskEvent to be logged
`name` the name to be associated with the event
`eid` the numeric representation of the event
`entry_time` the time when the event occurred

#### FileEventLogger

    class FileEventLogger(EventLogger):
        name: str

Base class for EventLoggers that are exporting events to files. Has default behavior to open a file stream in `start`, flush
events regularly during `log_events`, and close the file in `stop`.

*Attributes:*

`output_folder` a string representing the path where the file will be saved

`log_file` the file object

*Methods:*

`get_file_path() -> str:` abstract method returning the full path to the file

#### CSVEventLogger

    class CSVEventLogger(FileEventLogger):
        name: str

Default EventLogger for all Tasks that saves event stream to a CSV file. Saved files include a header with subject,task,
protocol, address file, and other configuration-related information. The default filename is set to the timestamp in seconds when
the task began.

#### OENetworkLogger

    class OENetworkLogger(EventLogger):
        name: str
        address: str
        port: str

EventLogger that transmits pybehave events as strings to OpenEphys to aid in synchronization.
This logger should be paired with a NetworkEvents plugin in OpenEphys.

*Required Extras:* `oe`

*Attributes:*

`address` the IP address of the device running OpenEphys. Use localhost if both pybehave and OpenEphys are running on the
same system.

`port` the port of the corresponding NetworkEvents plugin for OpenEphys.