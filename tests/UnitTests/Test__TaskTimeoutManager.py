
from pybehave.Tasks.Task import Task
from pybehave.Tasks.TaskProcess import TaskProcess
from pybehave.Events import PybEvents
from unittest.mock import MagicMock
from unittest.mock import MagicMock, call
import multiprocessing
import msgspec.msgpack
import collections
from enum import Enum
from pybehave.Components.BinaryInput import BinaryInput
from state_transition import StateTransition

'''Test that TimeoutManager functions are called by Task'''

def test_task_cancels_initial_timeout_in_finish_state():
    """Verify timeout is cancelled in FINISH state."""
    tp, task, mock_manager = StateTransition.setup_task_process_with_mocked_manager()

    CHAMBER_ID = 1
    TIMER_NAME = "TestTimer"

    assert CHAMBER_ID in tp.tasks, f"Task not registered in tp.tasks!"
 
    initial_enter = PybEvents.StateEnterEvent(
        chamber=CHAMBER_ID,
        name="INITIAL",
        value=task.States.INITIAL.value,
        metadata=None
    )
    task.INITIAL(initial_enter) # Timer initialized in INITIAL   
    mock_manager.reset_mock() # Clear calls from set_timeout before assertion
  
    finish_enter = PybEvents.StateEnterEvent(
        chamber=CHAMBER_ID,
        name="FINISH",
        value=task.States.FINISH.value,
        metadata=None
    )
    task.FINISH(finish_enter)  
    mock_manager.cancel_timeout.assert_called_once_with(
        f"{CHAMBER_ID}/{TIMER_NAME}"
    )

def test_task_pauses_timeout_on_pause_event():
        """Verify timeout is paused when pause button is pressed in INITIAL state."""
        tp, task, mock_manager = StateTransition.setup_task_process_with_mocked_manager()
        CHAMBER_ID = 1
        TIMER_NAME =  "TestTimer"

        waiting_enter = PybEvents.StateEnterEvent(
            chamber=CHAMBER_ID,
            name="WAITING",
            value=task.States.INITIAL.value,
            metadata=None
        )
        task.INITIAL(waiting_enter)
        mock_manager.reset_mock()

        pause_button = MagicMock()
        pause_button.state = True
        task.pause_button = [pause_button]
        pause_button_press = PybEvents.ComponentChangedEvent(
             chamber= CHAMBER_ID,
             comp=pause_button,
             index=0
        )
        task.INITIAL(pause_button_press)
        mock_manager.pause_timeout.assert_called_once_with(f"{CHAMBER_ID}/{TIMER_NAME}")

    
def test_task_resumes_timeout_on_resume_event():
        """Verify timeout is resumed when resume button is pressed in PAUSED state."""
        tp, task, mock_manager = StateTransition.setup_task_process_with_mocked_manager()
        CHAMBER_ID = 1
        TIMER_NAME =  "TestTimer"

        resume_button = MagicMock()
        resume_button.state = True
        task.resume_button = [resume_button]

        waiting_enter = PybEvents.StateEnterEvent(
            chamber=CHAMBER_ID,
            name="WAITING",
            value=task.States.INITIAL.value
        )
        task.INITIAL(waiting_enter)
        mock_manager.reset_mock()

        resume_button_press = PybEvents.ComponentChangedEvent(
               chamber= CHAMBER_ID,
               comp=resume_button,
               index=0
        )
        task.PAUSED(resume_button_press)
        mock_manager.resume_timeout.assert_called_once_with(f"{CHAMBER_ID}/{TIMER_NAME}")
 
    
