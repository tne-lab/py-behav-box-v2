from __future__ import annotations
import time
import traceback
from abc import ABCMeta, abstractmethod
import importlib
from enum import Enum
import runpy
from typing import Any, Type, overload, Dict, List

from Components.Component import Component
from Events import PybEvents
from Sources.Source import Source
from Tasks.Timeout import Timeout
from Utilities.AddressFile import AddressFile
import Utilities.Exceptions as pyberror
from Workstation.Workstation import Workstation


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
        self.entry_time = self.start_time = self.cur_time = self.time_into_trial = self.time_paused = 0
        self.paused = self.started = self.complete = False
        self.timeouts = {}
        self.state_timeouts = {}
        self.ws = None
        self.metadata = None
        self.components = {}

    @overload
    async def initialize(self, workstation: Workstation, metadata: Dict[str, Any], sources: Dict[str, Source]) -> None:
        ...

    @overload
    async def initialize(self, task: Task, components: List[Component], protocol: str) -> None:
        ...

    async def initialize(self, *args) -> None:

        component_definition = self.get_components()

        # Get all default values for task constants
        for key, value in self.get_constants().items():
            setattr(self, key, value)

        comp_index = 0

        # If this task is being created as part of a Task sequence
        if isinstance(args[0], Task):
            # Assign variables from base Task
            self.ws = args[0]
            self.metadata = args[0].metadata
            for component in args[1]:
                if component.id.split('-')[0] in component_definition:
                    if not hasattr(self, component.id.split('-')[0]):
                        setattr(self, component.id.split('-')[0], component)
                    else:  # If the Component is part of an already registered list
                        # Update the list with the Component at the specified index
                        if isinstance(getattr(self, component.id.split('-')[0]), list):
                            getattr(self, component.id.split('-')[0]).append(component)
                        else:
                            setattr(self, component.id.split('-')[0],
                                    [getattr(self, component.id.split('-')[0]), component])
                    self.components[component.id] = (component, comp_index)
                    comp_index += 1
            # Load protocol is provided
            protocol = args[2]
        else:  # If this is a standard Task
            self.ws = args[0]
            self.metadata = args[1]
            sources = args[2]
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
                            # Import and instantiate the indicated Component with the provided ID and address
                            component_type = getattr(importlib.import_module("Components." + comp.component_type),
                                                     comp.component_type)
                            if issubclass(component_type, component_definition[cid][i]):
                                if sources[comp.source_name].is_available():
                                    component = component_type(sources[comp.source_name],
                                                               "{}-{}-{}".format(cid, str(self.metadata["chamber"]),
                                                                                 str(i)), comp.component_address)
                                    if comp.metadata is not None:
                                        component.initialize(comp.metadata)
                                    try:
                                        await sources[comp.source_name].register_component(self, component)
                                    except:
                                        print(traceback.format_exc())
                                        raise pyberror.ComponentRegisterError
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
                                    self.components[component.id] = (component, comp_index)
                                    comp_index += 1
                                else:
                                    raise pyberror.SourceUnavailableError
                            else:
                                raise pyberror.InvalidComponentTypeError

            for name in component_definition:
                for i in range(len(component_definition[name])):
                    if not hasattr(self, name) or (
                            type(getattr(self, name)) is list and getattr(self, name)[i] is None):
                        component = component_definition[name][i](sources["es"],
                                                                  name + "-" + str(
                                                                      self.metadata["chamber"]) + "-" + str(i),
                                                                  sources["es"].next_id)
                        await sources["es"].register_component(self, component)
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
                        self.components[component.id] = (component, comp_index)
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

    def init(self) -> None:
        pass

    def clear(self) -> None:
        pass

    @abstractmethod
    def init_state(self) -> Enum:
        raise NotImplementedError

    def change_state(self, new_state: Enum, metadata: Any = None) -> None:
        self.entry_time = self.cur_time
        self.log_event(PybEvents.StateExitEvent(self, self.state, metadata))
        if not self.is_complete_():
            self.log_event(PybEvents.StateEnterEvent(self, new_state, metadata))
        else:
            self.log_event(PybEvents.TaskCompleteEvent(self))

    def start__(self) -> None:
        self.complete = False
        self.state = self.init_state()
        for key, value in self.get_variables().items():
            setattr(self, key, value)
        self.start()
        self.started = True
        self.entry_time = self.start_time = self.cur_time = time.perf_counter()

    def start(self) -> None:
        pass

    def pause__(self) -> None:
        self.paused = True
        self.time_into_trial = self.time_in_state()
        for name in self.timeouts.keys():
            self.pause_timeout(name)

    def resume__(self) -> None:
        self.paused = False
        time_temp = time.perf_counter()
        self.time_paused += time_temp - self.cur_time
        self.cur_time = time_temp
        self.entry_time = self.cur_time - self.time_into_trial
        for name in self.timeouts.keys():
            self.resume_timeout(name)

    def stop__(self) -> None:
        self.started = False
        for name in self.timeouts.keys():
            self.cancel_timeout(name)
        self.timeouts = {}
        self.stop()

    def stop(self) -> None:
        pass

    def main_loop(self, event: PybEvents.PybEvent) -> None:
        self.cur_time = time.perf_counter()
        if isinstance(event, PybEvents.StateEnterEvent):
            self.state = event.state
        elif isinstance(event, PybEvents.StateExitEvent):
            if self.state in self.state_timeouts:
                for tm in self.state_timeouts[self.state].values():
                    if tm[1]:
                        tm[0].stop()
        all_handled = self.all_states(event)
        if not all_handled and hasattr(self, self.state.name):
            state_method = getattr(self, self.state.name)
            state_method(event)

    def all_states(self, event: PybEvents.PybEvent) -> bool:
        pass

    def time_elapsed(self) -> float:
        return self.cur_time - self.start_time - self.time_paused

    def time_in_state(self) -> float:
        return self.cur_time - self.entry_time

    # noinspection PyMethodMayBeStatic
    def get_constants(self) -> Dict[str, Any]:
        return {}

    # noinspection PyMethodMayBeStatic
    def get_variables(self) -> Dict[str, Any]:
        return {}

    @staticmethod
    def get_components() -> Dict[str, List[Type[Component]]]:
        return {}

    def is_complete(self) -> bool:
        return False

    def is_complete_(self) -> bool:
        return self.complete or self.is_complete()

    def task_complete(self):
        self.log_event(PybEvents.TaskCompleteEvent(self))

    def _send_timeout(self, name: str, metadata: Dict):
        self.log_event(PybEvents.TimeoutEvent(self, name, metadata))
        del self.timeouts[name]

    def set_timeout(self, name: str, timeout: float, end_with_state=True, metadata: Dict = None):
        if name not in self.timeouts:
            tm = Timeout(lambda: self._send_timeout(name, metadata))
            self.timeouts[name] = tm
            if self.state not in self.state_timeouts:
                self.state_timeouts[self.state] = {}
            self.state_timeouts[self.state][name] = (tm, end_with_state)
            self.timeouts[name].start(timeout)
        else:
            self.timeouts[name].stop()
            self.timeouts[name].start(timeout)

    def cancel_timeout(self, name: str):
        if name in self.timeouts:
            self.timeouts[name].stop()

    def pause_timeout(self, name: str):
        if name in self.timeouts:
            self.timeouts[name].pause()

    def resume_timeout(self, name: str):
        if name in self.timeouts:
            self.timeouts[name].resume()

    def extend_timeout(self, name: str, timeout: float):
        if name in self.timeouts:
            self.timeouts[name].extend(timeout)

    def log_event(self, event: PybEvents.TaskEvent):
        self.ws.queue.put_nowait(event)
