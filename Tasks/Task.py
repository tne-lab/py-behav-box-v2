import os
import time
from abc import ABCMeta, abstractmethod
import csv
import importlib

from Components import *
from Events.StateChangeEvent import StateChangeEvent
from Events.InitialStateEvent import InitialStateEvent
from Events.FinalStateEvent import FinalStateEvent
from Utilities.read_protocol_variable import read_protocol_variable


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

    def __init__(self, metadata, sources, address_file="", protocol=""):
        self.metadata = metadata
        self.events = []  # List of Events from the current task loop
        self.state = None  # The current task state
        self.entry_time = 0  # Time when the current state began
        self.start_time = 0  # Time the task started
        self.cur_time = 0  # The time for the current task loop
        self.paused = False
        self.started = False
        self.time_into_trial = 0
        # Open the provided AddressFile
        with open(address_file if len(address_file) > 0 else "Defaults/{}.csv".format(type(self).__name__), newline='') as csvfile:
            address_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            # Each row in the AddressFile corresponds to a Task Component
            for row in address_reader:
                # Import and instantiate the indicated Component with the provided ID and address
                component_type = getattr(importlib.import_module("Components." + row[1]), row[1])
                if len(row) > 6:
                    component = component_type(sources[row[2]], row[0] + "-" + str(metadata["chamber"]) + "-" + str(row[4]), row[3], row[6])
                else:
                    component = component_type(sources[row[2]], row[0] + "-" + str(metadata["chamber"]) + "-" + str(row[4]), row[3])
                sources[row[2]].register_component(self, component)
                # If the ID has yet to be registered
                if not hasattr(self, row[0]):
                    # If the Component is part of a list
                    if int(row[5]) > 1:
                        # Create the list and add the Component at the specified index
                        component_list = [None] * int(row[5])
                        component_list[int(row[4])] = component
                        setattr(self, row[0], component_list)
                    else:  # If the Component is unique
                        setattr(self, row[0], component)
                else:  # If the Component is part of an already registered list
                    # Update the list with the Component at the specified index
                    component_list = getattr(self, row[0])
                    component_list[int(row[4])] = component
                    setattr(self, row[0], component_list)
        # Get all default values for task variables
        for key, value in self.get_variables().items():
            setattr(self, key, value)
        # If a Protocol is provided, replace all indicated variables with the values from the Protocol
        if len(protocol) > 0:
            with open(protocol, newline='') as csvfile:
                protocol_reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
                for row in protocol_reader:
                    setattr(self, row[0], read_protocol_variable(row))

    def change_state(self, new_state, metadata=None):
        self.entry_time = self.cur_time
        # Add a StateChangeEvent to the events list indicated the pair of States representing the transition
        self.events.append(StateChangeEvent(self.state, new_state, self.entry_time-self.start_time, metadata))
        self.state = new_state

    def start(self):
        self.events = []
        self.started = True
        self.entry_time = self.start_time = self.cur_time = time.time()
        self.events.append(InitialStateEvent(self.state, self.cur_time - self.start_time))

    def pause(self):
        self.paused = True
        self.time_into_trial = time.time() - self.entry_time

    def resume(self):
        self.paused = False
        self.entry_time = time.time() - self.time_into_trial

    def stop(self):
        self.started = False
        self.events = []
        self.events.append(FinalStateEvent(self.state, self.cur_time - self.start_time))

    def main_loop(self):
        self.cur_time = time.time()

    @abstractmethod
    def get_variables(self):
        raise NotImplementedError

    @abstractmethod
    def is_complete(self):
        raise NotImplementedError
