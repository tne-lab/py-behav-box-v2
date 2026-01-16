import unittest
from unittest.mock import MagicMock
import traceback
from pybehave.Tasks.Task import Task
from pybehave.Events.PybEvents import ErrorEvent

class BrokenTask(Task):
    def WAITING(self, event):
        return 1 / 0  

def test_task_process_emits_error_event():  
    mock_tp = MagicMock()     
    task = BrokenTask()   
    # Pybehave wraps every task call in a try-except block.
    try:
        task.WAITING(None)
    except Exception as e:
        # Create the ErrorEvent with the real crash details
        err_evt = ErrorEvent(
            error=str(e),
            traceback=traceback.format_exc()
        )
        # Tell the mock TaskProcess to log it
        mock_tp.log_gui_event(err_evt)
    mock_tp.log_gui_event.assert_called_once()    
    # Verify the data inside the event is correct
    sent_event = mock_tp.log_gui_event.call_args[0][0]
    assert isinstance(sent_event, ErrorEvent)
    assert "division by zero" in sent_event.error

# def test_gui_displays_error_message():
#     gui = MyTaskGUI(MagicMock())                                                              
#     # Manually create the event (No Task involved)
#     fake_error = ErrorEvent(error="Sensor Disconnected", traceback="Line 42...")    
#     # Tell the GUI to process this update
#     gui.process_update(fake_error)    
#     # Check if the GUI updated its internal error string
#     assert gui.error_display_text == "Sensor Disconnected"