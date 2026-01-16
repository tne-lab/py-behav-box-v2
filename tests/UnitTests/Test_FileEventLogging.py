import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import collections
from pybehave.Tasks.Task import Task
from pybehave.Tasks.TaskProcess import TaskProcess
from pybehave.Events.LoggerEvent import LoggerEvent
from pybehave.Events.FileEventLogger import FileEventLogger
import time
import math
from pybehave.Events.CSVEventLogger import CSVEventLogger


class MockFileEventLogger(FileEventLogger):
    """Concrete class to allow instantiation and testing."""
    def get_file_path(self) -> str:
        return "/mock/path/log.txt"
    
    def log_events(self, events: collections.deque[LoggerEvent]) -> None:
        super().log_events(events)
        #pass 

class TestFileEventLogger(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_logger_starts_and_stops(self, mock_makedirs, mock_file_open, mock_exists):
        logger = MockFileEventLogger(name="TestLogger")
        logger.output_folder = "/mock/path"    
        # Get the mock file handle that will be returned by open()
        # This must be done before calling start()
        mock_file_handle = mock_file_open.return_value        
        # Ensure's the mock file reports as not closed
        mock_file_handle.closed = False    
        logger.start()
        mock_file_open.assert_called_once_with("/mock/path/log.txt", "w")
        self.assertIs(logger.log_file, mock_file_handle)
        logger.stop()        
        mock_file_handle.close.assert_called_once()        
        # Verify open was only called once 
        self.assertEqual(mock_file_open.call_count, 1)

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists', return_value=True)
    def test_log_events_flushes_file(self, mock_exists, mock_file_open):
        logger = MockFileEventLogger(name="TestLogger")
        logger.output_folder = "/mock/path"        
        # Get the mock file handle that will be returned by open()
        mock_file_handle = mock_file_open.return_value
        logger.start()        
        # Verify logger.log_file is set correctly
        self.assertIs(logger.log_file, mock_file_handle)        
        # Create a mock event deque
        mock_event_deque = collections.deque([
            MagicMock(spec_set=['timestamp', 'type', 'data']),
            MagicMock(spec_set=['timestamp', 'type', 'data'])
        ])        
        logger.log_events(mock_event_deque)
        mock_file_handle.flush.assert_called_once()

## --------------------------------------------------------------
##               CSVEventLogger py file 
## --------------------------------------------------------------

class MockCSVEventLogger(CSVEventLogger):
    """Minimal concrete implementation for testing."""
    def get_file_path(self) -> str:
        # Use the actual timestamp-based logic from parent
        return os.path.join(self.output_folder, f"{int(time.time() * 1000)}.csv")


from state_transition import DemoTask

class TestCSVEventLoggerStartup(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open)
    def test_start_writes_metadata_section(self, 
                                        mock_file_open):
        """Verify start() writes all metadata headers in correct format."""
        
        test_task = DemoTask()        
        logger = MockCSVEventLogger(name="TestLogger")
        logger.output_folder = "/mock/path/"
        logger.task = test_task
        logger.start()        
        # The file handle is stored in logger.log_file
        mock_file_handle = logger.log_file  # mock_file_handle.return_value does not work here
        
        print(f"Has write: {hasattr(mock_file_handle, 'write')}")
        actual_writes = [
            call_args[0][0] 
            for call_args in mock_file_handle.write.call_args_list
        ]      
        expected_writes = [
            "Subject,TestSub\n",
            "Task,DemoTask\n", 
            "Chamber,4\n",
            "Protocol,Protocol_A\n",
            "AddressFile,Address.txt\n",
            "SubjectConfiguration\n",  
            "CONSTANT_A,\"10\"\n",
            "CONSTANT_B,\"Value\"\n",
            "\n",
            "Trial,Time,Type,Code,State,Metadata\n"
        ]        
        self.assertEqual(expected_writes, actual_writes) 