import unittest
from unittest.mock import patch, MagicMock
from collections import deque
import time
from pybehave.Tasks.TimeoutManager import Timeout

# Placeholder class for the target function
class DemoTarget:
    def execute_me(self, arg1, arg2):
        pass

class TestTimeout(unittest.TestCase):
    def setUp(self):
        """Setup a base Timeout object for all tests."""
        # Mock the target function to ensure it is called correctly later
        self.mock_target = MagicMock()        
        # Create a Timeout instance with a 10-second duration
        self.timeout = Timeout(
            name="MyTimer",
            chamber=1,
            duration=10.0,
            target=self.mock_target,
            args=("arg_a", 123)
        )

    @patch('time.perf_counter')
    def test_time_remaining_while_running(self, mock_perf_counter):
        ''' Verify Time Remaining while Running '''
        # initial 'start' time 
        mock_perf_counter.return_value = 0.0
        self.timeout.start()

        # simulate 4.0 seconds elapsing
        mock_perf_counter.return_value = 4.0 
        # calculate time remaining
        remaining = self.timeout.time_remaining()        
        # the remaining time should be 6.0
        self.assertAlmostEqual(remaining, 6.0, places=3)
        
        # simulate passing the duration (elapsed time = 12.0)
        mock_perf_counter.return_value = 12.0
        remaining = self.timeout.time_remaining()
        # the remaining time should be negative (time has expired)
        self.assertAlmostEqual(remaining, -2.0, places=3)

    @patch('time.perf_counter')
    def test_time_remaining_while_paused(self, mock_perf_counter):
        ''' Verify Time Remaining while Paused ''' 
        mock_perf_counter.return_value = 0.0
        self.timeout.start()
        
        # simulate 3.5 seconds running, then pause
        mock_perf_counter.return_value = 3.5
        self.timeout.pause()        
        # the elapsed time should be recorded
        self.assertAlmostEqual(self.timeout.elapsed_time, 3.5, places=3)
        
        # the start time must be None when paused
        self.assertIsNone(self.timeout.start_time)        
        # calculate time remaining (uses elapsed_time)
        remaining = self.timeout.time_remaining()
        # remaining time should be 10.0 - 3.5 = 6.5
        self.assertAlmostEqual(remaining, 6.5, places=3)
        
    def test_execution(self):
        ''' Verify execution and argument passing '''    
        self.timeout.execute()        
        # Check that the mock target was called once with the correct arguments
        self.mock_target.assert_called_once_with("arg_a", 123)