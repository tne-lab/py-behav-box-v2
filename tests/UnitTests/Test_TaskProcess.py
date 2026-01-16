from pybehave.Tasks.Task import Task
from pybehave.Tasks.TaskProcess import TaskProcess
from pybehave.Events import PybEvents
from msgspec.msgpack import Encoder
from msgspec.msgpack import Decoder
from multiprocessing.connection import Connection
import collections
from collections import deque
from unittest.mock import MagicMock
from unittest.mock import MagicMock, call
import multiprocessing
import msgspec.msgpack
import collections
from enum import Enum
from pybehave.Components.BinaryInput import BinaryInput
from state_transition import StateTransition
import typing


''' ----------------Test setups----------------- '''    

def setup_task_process():
    # Mock all required IPC channels (mainq, guiq, sourceq)
    mock_mainq = MagicMock(spec=multiprocessing.connection)
    mock_guiq = MagicMock(spec=multiprocessing.connection)
    mock_sourceq = {} 
    tp = TaskProcess(mock_mainq, mock_guiq, mock_sourceq)
    
    tp.encoder = msgspec.msgpack.Encoder()
    tp.decoder = msgspec.msgpack.Decoder()
    tp.tp_q = collections.deque() 
    tp.logger_q = []
    tp.tm = MagicMock()
    tp.tmq_in = MagicMock()
    tp.tmq_out = MagicMock()
    
    
    tp.event_responses = {
        PybEvents.AddLoggerEvent: tp.add_logger,
        PybEvents.OutputFileChangedEvent: tp.output_file_changed,
        PybEvents.StartEvent: tp.start_task,
        PybEvents.TaskCompleteEvent: tp.task_complete,
        PybEvents.StopEvent: tp.stop_task,
        PybEvents.PauseEvent: tp.pause_task,
        PybEvents.ResumeEvent: tp.resume_task,
        PybEvents.InitEvent: tp.init_task,
        PybEvents.ClearEvent: tp.clear_task,
        PybEvents.ComponentUpdateEvent: tp.update_component,
        PybEvents.UnavailableSourceEvent: tp.source_unavailable,
        PybEvents.AddSourceEvent: tp.add_source,
        PybEvents.RemoveSourceEvent: tp.remove_source,
        PybEvents.ErrorEvent: tp.error,
        PybEvents.ConstantsUpdateEvent: tp.update_constants,
        PybEvents.ConstantRemoveEvent: tp.remove_constant,
        PybEvents.ExitEvent: tp.prepare_exit
    }

    return tp, mock_mainq, mock_guiq

def setup_task_process_for_timed_event_test():
        mock_mainq = MagicMock(spec=multiprocessing.connection)
        mock_guiq = MagicMock(spec=multiprocessing.connection)
        mock_sourceq = {} # Start with an empty dictionary for sources
        # Instantiate the TaskProcess (without starting the process)
        tp = TaskProcess(mock_mainq, mock_guiq, mock_sourceq)
        CHAMBER_ID = 1
        # test_task = StateTransition()
        # Mock the method TaskProcess depends on
        # test_task.time_elapsed = MagicMock(return_value=10.5) #needed for a logger event
        test_task = MagicMock()
        test_task.time_elapsed.return_value = 10.5
        tp.tasks[CHAMBER_ID] = test_task
        tp.logger_q = [] 

        return tp, test_task

def setup_task_process_with_source_mock():
        # Mocks for Constructor
        mock_mainq = MagicMock(spec=Connection)
        mock_guiq = MagicMock(spec=Connection)        
        # Create the real TP
        tp = TaskProcess(mock_mainq, mock_guiq, sourceq= {})        
        # Initialize necessary attributes
        tp.tp_q = deque()
        tp.logger_q = []
        tp.encoder = Encoder(enc_hook=PybEvents.enc_hook)
        tp.decoder = Decoder(type=PybEvents.subclass_union(PybEvents.PybEvent), dec_hook=PybEvents.dec_hook)
        # Create a mock connection that simulates I/O for the Source
        mock_source_conn = MagicMock(spec=Connection)        
        # Manually populate the internal source structures
        SOURCE_ID = "MOCK_LED_SOURCE"
        tp.sourceq[SOURCE_ID] = mock_source_conn
        tp.source_buffers[SOURCE_ID] = [] 
        
        return tp, mock_source_conn

'''-----------Tests for Task Process -------------------'''

def test_add_source_event():
    tp, mock_mainq, mock_guiq = setup_task_process()
    SOURCE_ID = "NewSourceA"
  
    mock_conn = MagicMock(spec=multiprocessing.connection)    
    # Create the event the main process would send
    event = PybEvents.AddSourceEvent(sid=SOURCE_ID, conn=mock_conn)
    tp.add_source(event)

    assert SOURCE_ID in tp.sourceq
    assert tp.sourceq[SOURCE_ID] is mock_conn
    # Source buffer should be initialized as an empty list
    assert SOURCE_ID in tp.source_buffers
    assert tp.source_buffers[SOURCE_ID] == []
    # Connection list should be updated (connections are used by select/poll)
    assert mock_conn in tp.connections

def test_log_event_queuing():
    tp, _ = setup_task_process_for_timed_event_test()
    
    # loggable event
    STATE_NAME = "FINISH" 
    STATE_VALUE = 2           
    log_event = PybEvents.StateEnterEvent(
        chamber=1, 
        name=STATE_NAME, 
        value=STATE_VALUE, 
        metadata=None
    )
    tp.log_event(log_event)
    assert len(tp.logger_q) == 1
    # print(log_event.format)
    assert isinstance(tp.logger_q[0],PybEvents.LoggerEvent) 
    
def test_tpq_event_handling():
    tp, _, _ = setup_task_process()    
    # Mock a Task and add it to the TP
    mock_task = MagicMock(spec=Task)
    mock_task.time_elapsed.return_value = 100.0 # Mock time
    tp.tasks[1] = mock_task    
    # Simulate a Task logging an event to the internal TP queue
    task_log_event = PybEvents.StateExitEvent(chamber=1, name="INITIAL",value=None)
    tp.tp_q.append(task_log_event) 
    # processing step (in run())  
    if tp.tp_q:
      
        event = tp.tp_q.popleft() 
        if hasattr(event, "chamber") and event.chamber in tp.tasks:
            tp.log_event(event)             
    logged_item = tp.logger_q[0] 
    # check if type is correct 
    assert isinstance(logged_item, PybEvents.LoggerEvent)     

def test_tp_serialization_deserialization():
    tp, mock_source_conn = setup_task_process_with_source_mock()
    SOURCE_ID = "MOCK_LED_SOURCE"  

    # --- Part 1: Test Outbound (TaskProcess -> Source) ---

    # ConstantsUpdateEvent sent between the GUI/Source
    sync_event = PybEvents.ConstantsUpdateEvent(
        chamber=1, 
        constants={"LED_BRIGHTNESS": "100"}
    )    
    # TaskProcess sends a LIST of events in the buffer
    events_to_send = [sync_event]
    tp.source_buffers[SOURCE_ID].extend(events_to_send) #list.extend to queue the events   
    # Simulate the outbound communication step
    if len(tp.source_buffers[SOURCE_ID]) > 0:
        payload = tp.encoder.encode(tp.source_buffers[SOURCE_ID])
        tp.sourceq[SOURCE_ID].send_bytes(payload)
        tp.source_buffers[SOURCE_ID] = []
    sent_bytes = mock_source_conn.send_bytes.call_args[0][0]
    assert isinstance(sent_bytes, bytes)
    # Verify bytes sent by TP can be decoded to correct Events
    decoder = msgspec.msgpack.Decoder(
        type=typing.List[PybEvents.subclass_union(PybEvents.PybEvent)], 
        dec_hook=PybEvents.dec_hook
    )
    decoded_list = decoder.decode(sent_bytes)
    assert isinstance(decoded_list, list)
    assert isinstance(decoded_list[0], PybEvents.ConstantsUpdateEvent)
    assert decoded_list[0].constants["LED_BRIGHTNESS"] == "100"

    # --- Part 2: Test Inbound (Source -> TaskProcess) ---

    command_event = PybEvents.ComponentUpdateEvent(
        chamber=1, comp_id="LED_1", value=1, metadata={}
    )
    encoded_input_bytes = tp.encoder.encode(command_event)
    mock_source_conn.recv_bytes.return_value = encoded_input_bytes
    # Simulate the TaskProcess receiving and decoding 
    received_event = tp.decoder.decode(mock_source_conn.recv_bytes())
    assert isinstance(received_event, PybEvents.ComponentUpdateEvent)
    assert received_event.comp_id == "LED_1"
    assert received_event.value == 1