from pybehave.Tasks.Task import Task
from pybehave.Tasks.TaskProcess import TaskProcess
from pybehave.Events import PybEvents
from unittest.mock import MagicMock
from unittest.mock import MagicMock, call
from msgspec.msgpack import Encoder
from msgspec.msgpack import Decoder
import multiprocessing
import msgspec.msgpack
import collections
from collections import deque
from enum import Enum
from multiprocessing.connection import Connection
from pybehave.Components.BinaryInput import BinaryInput
from pybehave.Tasks.TimeoutManager import TimeoutManager

class StateTransition(Task):

    class States(Enum):
        INITIAL = 0
        PAUSED = 1
        FINISH =2

    def get_components(self): return {'light': [BinaryInput],
                                     'pause_button': [BinaryInput],  
                                     'resume_button': [BinaryInput] }
    def get_variables(self) : return {}
    def init_state(self) : return self.States.INITIAL
    def is_complete(self) : return False
   
    def INITIAL(self, event: PybEvents.PybEvent):
            if isinstance(event, PybEvents.StateEnterEvent):
                timeout_duration = 10  
                timeout_name = "TestTimer"
                self.set_timeout(timeout_name, timeout_duration)
                #print(self.get_components)
                self.write_component('light-1-0', True)  # COMPONENT FORMAT: name-chamber-index
                self.change_state(self.States.FINISH)
            elif isinstance(event, PybEvents.ComponentChangedEvent):
                if event.comp is self.pause_button[event.index] and event.comp.state:
                    self.pause_timeout("TestTimer")
                    self.change_state(self.States.PAUSED)   
                     
            elif isinstance(event, PybEvents.TimeoutEvent):
                if event.name == "TestTimer":
                    self.change_state(self.States.FINISH)

    def PAUSED(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            #self.change_state(self.States.FINISH) 
            self.write_component('light-1-0', False) 
        elif isinstance(event, PybEvents.ComponentChangedEvent):
          if event.comp is self.resume_button[event.index] and event.comp.state:
            self.resume_timeout("TestTimer")
            self.change_state(self.States.INITIAL)
    
    def FINISH(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):
            self.cancel_timeout("TestTimer")  # Clean up any remaining timeout
            self.write_component('light-1-0', False)  
           
    # --- 2. Setup the Task instances ---

    def setup_task():
        mock_tp = MagicMock()
        mock_tp.tp_q = [] # Mock event queue
        #mock_tp.source_buffers = {'MOCK_SOURCE': []} #for write_component
        mock_tp.tm = MagicMock() # Mock Timeout Manager
        metadata = {
            "chamber": 1,
            "subject": "CORE_TEST",
            "protocol": None,
            "address_file": None
        }
        # Initialize the Task 
        task = StateTransition()
        task.initialize(mock_tp, metadata)
        task.start__() # Start to set initial state and times   
        return task, mock_tp
    

    def setup_task_process_with_mocked_manager():

        mock_event_queue = MagicMock()
        mock_gui_queue = MagicMock()
        config = {}

        tp = TaskProcess(mock_event_queue, mock_gui_queue, config)
        tp.tp_q = []       
        mock_manager = MagicMock(spec=TimeoutManager)
        tp.tm = mock_manager

        test_task = StateTransition()
        test_task.timeouts = {}
        test_task.state_timeouts = {}

        CHAMBER_ID = 1
        metadata = {
            "chamber": CHAMBER_ID,
            "subject": "CORE_TEST",
            "protocol": None,
            "address_file": None
        }
        test_task.initialize(tp, metadata)
        test_task.start__()
        tp.tasks[CHAMBER_ID] = test_task

        # #  # **DEBUG: Check what happened during initialization**
        # print(f"After initialize:")
        # print(f"  hasattr(test_task, 'components'): {hasattr(test_task, 'components')}")
        # if hasattr(test_task, 'components'):
        #     print(f"  test_task.components: {test_task.components}")
        # print(f"  test_task.get_components(): {test_task.get_components()}")
        
        # test_task.start__()
        # tp.tasks[CHAMBER_ID] = test_task
        
        # # **DEBUG: Check after start**
        # print(f"After start__:")
        # print(f"  hasattr(test_task, 'components'): {hasattr(test_task, 'components')}")
        # if hasattr(test_task, 'components'):
        #     print(f"  test_task.components: {test_task.components}")

        return tp, test_task, mock_manager

class DemoTask: 
    """Simple test task object with known values."""
    def __init__(self):
        self.metadata = {
            "subject": "TestSub",
            "chamber": 3,
            "protocol": "Protocol_A",
            "address_file": "Address.txt"
        }
        self.initial_constants = {
            "CONSTANT_A": 10,
            "CONSTANT_B": "Value"
        }
        # Set the actual attributes for getattr 
        self.CONSTANT_A = 10
        self.CONSTANT_B = "Value"
   
