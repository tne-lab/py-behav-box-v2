import time
from abc import ABCMeta, abstractmethod
import importlib
from enum import Enum
import runpy

from Components import *
from Events.StateChangeEvent import StateChangeEvent
from Events.InitialStateEvent import InitialStateEvent
from Events.FinalStateEvent import FinalStateEvent
from Utilities.AddressFile import AddressFile


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

    # ws, metadata, sources, address_file="", protocol=""
    # task, components, protocol
    def __init__(self, *args):
        self.events = []  # List of Events from the current task loop
        self.state = None  # The current task state
        self.entry_time = 0  # Time when the current state began
        self.start_time = 0  # Time the task started
        self.cur_time = 0  # The time for the current task loop
        self.paused = False  # Boolean indicator if task is paused
        self.started = False  # Boolean indicator if task has started
        self.time_into_trial = 0  # Tracks time into trial for pausing purposes
        self.time_paused = 0

        component_definition = self.get_components()

        # Get all default values for task constants
        for key, value in self.get_constants().items():
            setattr(self, key, value)

        # Get all default values for task variables
        for key, value in self.get_variables().items():
            setattr(self, key, value)

        # If this task is being created as part of a Task sequence
        if isinstance(args[0], Task):
            # Assign variables from base Task
            self.ws = args[0].ws
            self.metadata = args[0].metadata
            self.components = []
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
                    self.components.append(component)
            # Load protocol is provided
            if len(args) > 2 and args[2] is not None:
                for key in args[2]:
                    setattr(self, key, args[2][key])
        else:  # If this is a standard Task
            self.ws = args[0]
            self.metadata = args[1]
            sources = args[2]
            protocol = ""
            address_file = ""
            if len(args) >= 4:
                address_file = args[3]
            if len(args) >= 5:
                protocol = args[4]
            self.components = []

            # Open the provided AddressFile
            if isinstance(address_file, str) and len(address_file) > 0:
                file_globals = runpy.run_path(address_file, {"AddressFile": AddressFile})
                for cid in file_globals['addresses'].addresses:
                    if cid in component_definition:
                        comps = file_globals['addresses'].addresses[cid]
                        for i, comp in enumerate(comps):
                            # Import and instantiate the indicated Component with the provided ID and address
                            component_type = getattr(importlib.import_module("Components." + comp.component_type), comp.component_type)
                            if issubclass(component_type, component_definition[cid][i]):
                                component = component_type(sources[comp.source_name], "{}-{}-{}".format(cid, str(self.metadata["chamber"]), str(i)), comp.component_address)
                                if comp.metadata is not None:
                                    component.initialize(comp.metadata)
                                sources[comp.source_name].register_component(self, component)
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
                                self.components.append(component)
                            else:
                                raise InvalidComponentTypeError

            for name in component_definition:
                for i in range(len(component_definition[name])):
                    if not hasattr(self, name) or (type(getattr(self, name)) is list and getattr(self, name)[i] is None):
                        component = component_definition[name][i](sources["es"],
                                                                  name + "-" + str(
                                                                      self.metadata["chamber"]) + "-" + str(i),
                                                                  sources["es"].next_id)
                        sources["es"].register_component(self, component)
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
                        self.components.append(component)

            # If a Protocol is provided, replace all indicated variables with the values from the Protocol
            if isinstance(protocol, str) and len(protocol) > 0:
                file_globals = runpy.run_path(protocol)
                for cons in file_globals['protocol']:
                    if hasattr(self, cons):
                        setattr(self, cons, file_globals['protocol'][cons])
        self.init()

    def init(self):
        pass

    @abstractmethod
    def init_state(self):
        raise NotImplementedError

    def change_state(self, new_state, metadata=None):
        self.entry_time = self.cur_time
        # Add a StateChangeEvent to the events list indicated the pair of States representing the transition
        self.events.append(StateChangeEvent(self, self.state, new_state, metadata))
        self.state = new_state

    def start__(self):
        self.state = self.init_state()
        for key, value in self.get_variables().items():
            setattr(self, key, value)
        self.start()
        self.started = True
        self.entry_time = self.start_time = self.cur_time = time.time()
        self.events.append(InitialStateEvent(self, self.state))

    def start(self):
        pass

    def pause__(self):
        self.paused = True
        self.time_into_trial = self.time_in_state()
        self.events.append(StateChangeEvent(self, self.state, self.SessionStates.PAUSED, None))
        self.ws.log_events(self.metadata["chamber"])
        self.pause()

    def pause(self):
        pass

    def resume__(self):
        self.resume()
        self.paused = False
        time_temp = time.time()
        self.time_paused += time_temp - self.cur_time
        self.cur_time = time_temp
        self.entry_time = self.cur_time - self.time_into_trial
        self.events.append(StateChangeEvent(self, self.SessionStates.PAUSED, self.state, None))

    def resume(self):
        pass

    def stop__(self):
        self.started = False
        self.events.append(FinalStateEvent(self, self.state))
        self.stop()

    def stop(self):
        pass

    def main_loop__(self):
        self.cur_time = time.time()
        self.main_loop()

    def main_loop(self):
        pass

    def time_elapsed(self):
        return self.cur_time - self.start_time - self.time_paused

    def time_in_state(self):
        return self.cur_time - self.entry_time

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {}

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {}

    @staticmethod
    def get_components():
        return {}

    @abstractmethod
    def is_complete(self):
        raise NotImplementedError


class InvalidComponentTypeError:
    pass
