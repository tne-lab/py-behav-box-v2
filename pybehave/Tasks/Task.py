from __future__ import annotations

import time
from abc import ABCMeta, abstractmethod
import importlib
from enum import Enum
import runpy
from typing import Any, Type, overload, Dict, List, TYPE_CHECKING, Tuple

from pybehave.Events import PybEvents
from pybehave.Tasks.TimeoutManager import Timeout
from pybehave.Utilities.AddressFile import AddressFile
import pybehave.Utilities.Exceptions as pyberror

if TYPE_CHECKING:
    from pybehave.Tasks.TaskProcess import TaskProcess
    from pybehave.Components.Component import Component


class Task:
    __metaclass__ = ABCMeta
    """
        Abstract class defining the base requirements for a behavioral task. Tasks are state machines that transition 
        via a continuously running loop. Tasks rely on variables and components to dictate transition rules and receive 
        inputs respectively.
        
        Attributes
        ---------
        state : Enum
            An enumerated variable indicating the state the task is currently in
        entry_time : float
            The time in seconds when the current state began
        cur_time : float
            The current time in seconds for the task loop
        events : List<Event>
            List of events related to the current loop of the task

        Methods
        -------
        get_components() -> Dict
            Abstract method defining all variables necessary for the task as a dictionary relating variable names to 
            default values.
        change_state(new_state)
            Updates the task state
        start()
            Begins the task
        pause()
            Pauses the task
        stop()
            Ends the task
        main_loop()
            Repeatedly called throughout the lifetime of the task. State transitions are executed within.
        get_variables()
            Abstract method defining all variables necessary for the task as a dictionary relating variable names to 
            default values.
        is_complete()
            Abstract method that returns True if the task is complete
    """

    class SessionStates(Enum):
        PAUSED = 0

    def __init__(self):
        self.state = None
        self.entry_time = self.start_time = self.pause_time = self.time_into_trial = self.time_paused = 0
        self.paused = self.started = self.complete = False
        self.timeouts = {}
        self.state_timeouts = {}
        self.tp = None
        self.metadata = None
        self.components = {}
        self.state_methods = {}
        self.complete = False
        self._complete = False
        self.initial_constants = {}

    @overload
    def initialize(self, tp: TaskProcess, metadata: Dict[str, Any]) -> None:
        ...

    @overload
    def initialize(self, task: Task, components: Dict[Tuple], protocol: str) -> None:
        ...

    def initialize(self, *args) -> None:

        component_definition = self.get_components()

        # Get all default values for task constants
        for key, value in self.get_constants().items():
            setattr(self, key, value)

        comp_index = 0

        # If this task is being created as part of a Task sequence
        if isinstance(args[0], Task):
            # Assign variables from base Task
            self.tp = args[0].tp
            self.metadata = args[0].metadata
            for component_tuple in args[1].values():
                component = component_tuple[0]  # Index 0 in tuple is the Component
                cid = component.id.split('-')[0]  # Get simple name of Component
                if cid in component_definition:  # If Component is part of this Task
                    if not hasattr(self, cid):
                        setattr(self, cid, component)
                    else:  # If the Component is part of an already registered list
                        # Update the list with the Component at the specified index
                        if isinstance(getattr(self, cid), list):
                            getattr(self, cid).append(component)
                        else:
                            setattr(self, cid, [getattr(self, cid), component])
                    self.components[component.id] = (component, comp_index, component_tuple[2])
                    comp_index += 1
            # Load protocol is provided
            protocol = args[2]
        else:  # If this is a standard Task
            self.tp = args[0]
            self.metadata = args[1]
            protocol = self.metadata["protocol"]
            address_file = self.metadata["address_file"]

            # Open the provided AddressFile
            if isinstance(address_file, str) and len(address_file) > 0:
                try:
                    file_globals = runpy.run_path(address_file, {"AddressFile": AddressFile})
                except:
                    raise pyberror.MalformedAddressFileError
                for cid in file_globals['addresses'].addresses:
                    if cid in component_definition:
                        comps = file_globals['addresses'].addresses[cid]
                        for i, comp in enumerate(comps):
                            if comp is None:
                                if not hasattr(self, cid):
                                    # If the Component is part of a list
                                    if len(comps) > 1:
                                        # Create the list and add the Component at the specified index
                                        component_list = [None] * int(len(comps))
                                        setattr(self, cid, component_list)
                            else:
                                # Import and instantiate the indicated Component with the provided ID and address
                                component_type = getattr(importlib.import_module("pybehave.Components." + comp.component_type),
                                                         comp.component_type)
                                if issubclass(component_type, component_definition[cid][i]):
                                    component = component_type(self, "{}-{}-{}".format(cid, str(self.metadata["chamber"]),
                                                                                 str(i)), comp.component_address)
                                    if comp.metadata is not None:
                                        component.initialize(comp.metadata)
                                        metadata = comp.metadata.copy()
                                    else:
                                        metadata = {}
                                    metadata.update({"chamber": self.metadata["chamber"], "subject": self.metadata["subject"],
                                                    "task": type(self).__name__})
                                    self.tp.source_buffers[comp.source_name].append(
                                        PybEvents.ComponentRegisterEvent(comp.component_type, component.id, component.address,
                                                                         metadata=metadata))
                                    # If the ID has yet to be registered
                                    if not hasattr(self, cid):
                                        # If the Component is part of a list
                                        if len(comps) > 1:
                                            # Create the list and add the Component at the specified index
                                            component_list = [None] * int(len(comps))
                                            component_list[i] = component
                                            setattr(self, cid, component_list)
                                        else:  # If the Component is unique
                                            setattr(self, cid, component)
                                    else:  # If the Component is part of an already registered list
                                        # Update the list with the Component at the specified index
                                        component_list = getattr(self, cid)
                                        component_list[i] = component
                                        setattr(self, cid, component_list)
                                    self.components[component.id] = (component, comp_index, comp.source_name)
                                    comp_index += 1
                                else:
                                    raise pyberror.InvalidComponentTypeError

            for name in component_definition:
                for i in range(len(component_definition[name])):
                    if not hasattr(self, name) or (
                            type(getattr(self, name)) is list and getattr(self, name)[i] is None):
                        component = component_definition[name][i](self,
                                                                  name + "-" + str(
                                                                      self.metadata["chamber"]) + "-" + str(i),
                                                                  str(comp_index))
                        if not hasattr(self, name):
                            # If the Component is part of a list
                            if len(component_definition[name]) > 1:
                                # Create the list and add the Component at the specified index
                                component_list = [None] * int(len(component_definition[name]))
                                component_list[i] = component
                                setattr(self, name, component_list)
                            else:  # If the Component is unique
                                setattr(self, name, component)
                        else:  # If the Component is part of an already registered list
                            # Update the list with the Component at the specified index
                            component_list = getattr(self, name)
                            component_list[i] = component
                            setattr(self, name, component_list)
                        self.components[component.id] = (component, comp_index, None)
                        comp_index += 1

        # If a Protocol is provided, replace all indicated variables with the values from the Protocol
        if isinstance(protocol, str) and len(protocol) > 0:
            try:
                file_globals = runpy.run_path(protocol)
            except:
                raise pyberror.MalformedProtocolError
            for cons in file_globals['protocol']:
                if hasattr(self, cons):
                    setattr(self, cons, file_globals['protocol'][cons])

        # Get all default values for task variables
        for key, value in self.get_variables().items():
            setattr(self, key, value)

        if hasattr(self, "States"):
            for e in self.States:
                self.state_methods[e.name] = getattr(self, e.name)

    def init(self) -> None:
        """Called when the task is first loaded into the chamber."""
        pass

    def clear(self) -> None:
        """Called when the task is cleared from the chamber."""
        pass

    @abstractmethod
    def init_state(self) -> Enum | Tuple[Enum, Dict]:
        """ Override to return the state the task should begin in (from the States enum).

        Returns
        -------
        Enum | Tuple[Enum, Dict]
            the state or tuple of state and metadata
        """
        raise NotImplementedError

    def change_state(self, new_state: Enum, metadata: Dict = None) -> None:
        """ Call to change the state the task is currently in. Metadata can be provided which will be passed to the EventLogger with the event information.

        Parameters
        ----------
        new_state : Enum
            the state in the Task States enum that should be entered
        metadata : dict
            a dictionary containing any metadata that should be associated with the state change event.
        """
        metadata = metadata or {}
        self.entry_time = time.perf_counter()
        self.log_event(PybEvents.StateExitEvent(self.metadata["chamber"], self.state.name, self.state.value, metadata=metadata))
        if not self.is_complete_():
            self.log_event(PybEvents.StateEnterEvent(self.metadata["chamber"], new_state.name, new_state.value, metadata=metadata.copy()))
        else:
            self.task_complete()

    def start__(self) -> Dict:
        self._complete = False
        self.complete = False
        init_info = self.init_state()
        if isinstance(init_info, tuple):
            self.state = init_info[0]
            metadata = init_info[1]
        else:
            self.state = init_info
            metadata = {}
        for key, value in self.get_variables().items():
            setattr(self, key, value)
        self.start()
        self.started = True
        self.entry_time = self.start_time = time.perf_counter()

        return metadata

    def start(self) -> None:
        """Called when the task begins."""
        pass

    def pause(self) -> None:
        """Called when the task is paused."""
        pass

    def pause__(self) -> None:
        self.paused = True
        self.time_into_trial = self.time_in_state()
        self.pause_time = time.perf_counter()
        for name in self.timeouts.keys():
            self.pause_timeout(name)
        self.pause()

    def resume(self) -> None:
        """Called when the task is resumed."""
        pass

    def resume__(self) -> None:
        self.paused = False
        self.time_paused += time.perf_counter() - self.pause_time
        self.entry_time = time.perf_counter() - self.time_into_trial
        for name in self.timeouts.keys():
            self.resume_timeout(name)
        self.resume()

    def stop__(self) -> None:
        self.started = False
        for name in self.timeouts.keys():
            self.cancel_timeout(name)
        self.timeouts = {}
        self.stop()

    def stop(self) -> None:
        """Called when the task ends."""
        pass

    def main_loop(self, event: PybEvents.PybEvent) -> None:
        if isinstance(event, PybEvents.StateEnterEvent):
            self.state = self.States(event.value)
        elif isinstance(event, PybEvents.StateExitEvent):
            if self.state in self.state_timeouts:
                for tm in self.state_timeouts[self.state].values():
                    if tm[1]:
                        self.cancel_timeout(tm[0].name)
        elif isinstance(event, PybEvents.TimeoutEvent):
            del self.timeouts[event.name]
        all_handled = self.all_states(event)
        if not all_handled and self.state.name in self.state_methods:
            self.state_methods[self.state.name](event)
        if self.is_complete_():
            self.task_complete()

    def all_states(self, event: PybEvents.PybEvent) -> bool:
        pass

    def time_elapsed(self) -> float:
        """Returns the time that has passed in seconds (and fractions of a second) since the task began."""
        if self.start_time == 0:
            return 0
        else:
            return time.perf_counter() - self.start_time - self.time_paused

    def time_in_state(self) -> float:
        """Returns the time that has passed in seconds (and fractions of a second) since the current state began."""
        return time.perf_counter() - self.entry_time

    @staticmethod
    def get_constants() -> Dict[str, Any]:
        """Returns a dictionary describing all the constants used by the task. Constants can be of any type and modified using Protocols.

        Returns
        -------
        Dict[str, Any]
            the dictionary of constants
        """
        return {}

    @staticmethod
    def get_variables() -> Dict[str, Any]:
        """ Returns a dictionary describing all the variables used by the task. Variables can be of any type.

        Returns
        -------
        Dict[str, Any]
            the dictionary of variables
        """
        return {}

    @staticmethod
    def get_components() -> Dict[str, List[Type[Component]]]:
        """ Returns a dictionary describing all the components used by the task. Each component name is linked to a list of Component types.

        Returns
        -------
        Dict[str, List[Type[Component]]]
            the dictionary of Components
        """
        return {}

    def is_complete(self) -> bool:
        return False

    def is_complete_(self) -> bool:
        if not self._complete and (self.complete or self.is_complete()):
            self._complete = True
            return True
        return False

    def task_complete(self) -> None:
        """Log task completion"""
        self.log_event(PybEvents.TaskCompleteEvent(self.metadata["chamber"]))

    def _send_timeout(self, name: str, metadata: Dict) -> None:
        self.log_timeout(PybEvents.TimeoutEvent(self.metadata["chamber"], name, metadata=metadata))

    def set_timeout(self, name: str, timeout: float, end_with_state=True, metadata: Dict = None) -> None:
        """ Begins a timer that will add a TimeoutEvent to the event stream after a prescribed duration.

        Parameters
        ----------
        name : str
            a string representing the name to be associated with the timeout
        timeout : float
            duration of the timeout in seconds
        end_with_state : bool
            flag indicating whether the timeout should be removed when the state it was created in ends
        metadata : dict
            a dictionary containing any metadata that should be associated with the TimeoutEvent
        """
        metadata = metadata or {}
        if name not in self.timeouts:
            tm = Timeout(name, self.metadata["chamber"], timeout, self._send_timeout, (name, metadata))
            self.timeouts[name] = tm
            if self.state not in self.state_timeouts:
                self.state_timeouts[self.state] = {}
            self.state_timeouts[self.state][name] = (tm, end_with_state)
            self.tp.tm.add_timeout(tm)
        else:
            self.timeouts[name].duration = timeout
            self.tp.tm.reset_timeout(self.timeouts[name])

    def cancel_timeout(self, name: str):
        """Ends the indicated timeout early without adding an event to the stream."""
        if name in self.timeouts:
            self.tp.tm.cancel_timeout(str(self.metadata["chamber"]) + "/" + name)

    def pause_timeout(self, name: str):
        """Pauses the indicated timeout."""
        if name in self.timeouts:
            self.tp.tm.pause_timeout(str(self.metadata["chamber"]) + "/" + name)

    def resume_timeout(self, name: str):
        """Resumes a paused timeout."""
        if name in self.timeouts:
            self.tp.tm.resume_timeout(str(self.metadata["chamber"]) + "/" + name)

    def extend_timeout(self, name: str, timeout: float):
        """Adds a prescribed amount of time to a running timeout."""
        if name in self.timeouts:
            self.tp.tm.extend_timeout(str(self.metadata["chamber"]) + "/" + name, timeout)

    def log_event(self, event: PybEvents.TaskEvent):
        self.tp.tp_q.append(event)

    def log_custom_event(self, event_type: str, metadata, stateful=False):
        if stateful:
            self.tp.tp_q.append(PybEvents.StatefulCustomEvent(self.metadata["chamber"], event_type, metadata=metadata))
        else:
            self.tp.tp_q.append(PybEvents.CustomEvent(self.metadata["chamber"], event_type, metadata=metadata))

    def log_timeout(self, event: PybEvents.TimeoutEvent):
        self.tp.tmq_out.send_bytes(self.tp.encoder.encode(event))

    def write_component(self, cid: str, value: Any, metadata: Dict = None):
        metadata = metadata or {}
        e = PybEvents.ComponentUpdateEvent(self.metadata["chamber"], cid, value, metadata=metadata)
        self.tp.log_gui_event(e)
        if self.components[cid][2] is not None:
            self.tp.source_buffers[self.components[cid][2]].append(e)

    def close_component(self, cid: str):
        if self.components[cid][2] is not None:
            self.tp.source_buffers[self.components[cid][2]].append(PybEvents.ComponentCloseEvent(cid))
