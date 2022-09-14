# Logging events

## Overview

Pybehave's event framework formalizes the process of exporting [task]() data to external systems like the console, file system, 
or across the network. As opposed to [Sources]() which control task [Components](), events are intended solely for logging purposes
and saving data from the task. Towards this end, each task can be associated with any number of *EventLoggers* that are written
to parse certain types of *Events*.

## Event objects

All events subclass the base *Event* class which only requires the task and optional metadata for construction and records the
time of creation based on the task's `cur_time` attribute. This class is heavily subclassed to represent numerous possible 
types of Events that could be required by various tasks or external systems. 

### Core events

While events can be customized for specific needs, there are a few default Event classes that can represent the majority
of task information across systems. When the task begins, the state changes, and the task ends respectively will log
`InitialStateEvents`, `StateChangeEvents`, or `FinalStateEvents`. These three classes have additional attributes for the specific
states they are associated with. Additionally, `InputEvents` can be used to capture inputs to the task from components and
have an additional attribute to represent the input state.

## EventLoggers

