import multiprocessing
from unittest.mock import MagicMock
import psutil
from state_transition import StateTransition
from pybehave.Tasks.TaskProcess import TaskProcess
from pybehave.Events import PybEvents
import time
import msgspec
import typing 

def setup_task_process_for_ipc(source_ids):
    # Main: simplex (tp only receives)
    tp_recv_main, test_send_main = multiprocessing.Pipe(duplex=False)    
    # GUI: duplex (bidirectional)
    tp_gui, test_gui = multiprocessing.Pipe(duplex=True)
    # Sources: must be duplex (run() both waits on them AND sends to them)
    sourceq = {}
    source_conns = {}    
    for sid in source_ids:
        tp_source, test_source = multiprocessing.Pipe(duplex=True)  # DUPLEX
        sourceq[sid] = tp_source
        source_conns[sid] = test_source

    tp = TaskProcess(tp_recv_main, tp_gui, sourceq)    
    tp.tasks = {}
    tp.task_event_loggers = {}
    tp.should_exit = False

    return tp, source_conns, test_send_main, test_gui

class DummyTask:
    def __init__(self):
        self.constants = {}
        self.metadata = {"chamber": 1}
        self.started = False
        self.paused = False

    def main_loop(self, event):
        # This is called by TaskProcess.py in update_constants
        pass
    
    def time_elapsed(self):
        return 0.0

def test_taskprocess_ipc_path():
    tp, sources, main_in, gui_conn = setup_task_process_for_ipc(["LED"])      
    # To test IPC, both Task and Task Process are needed
    # Use real Task; MagicMock fails to pickle during Windows IPC tests
    tp.tasks[1] = DummyTask()     
    tp.start()    
    time.sleep(0.5) 
    
    encoder = msgspec.msgpack.Encoder(enc_hook=PybEvents.enc_hook)    
    test_constants = {"LED_BRIGHTNESS": "100"}
    event = PybEvents.ConstantsUpdateEvent(chamber=1, constants=test_constants)
    # TP's internal loop handles decoding and routing; we are testing the full IPC passthrough
    main_in.send_bytes(encoder.encode(event))
    # Act as Source: Decode TP's relayed output to verify IPC passthrough
    src = sources["LED"]
    if src.poll(2.0):
        print(f"Test: Data received!")
        raw = src.recv_bytes() 
        # TaskProcess always sends a LIST from source_buffers
        decoder = msgspec.msgpack.Decoder(
            type=typing.List[PybEvents.subclass_union(PybEvents.PybEvent)], 
            dec_hook=PybEvents.dec_hook
        )        
        decoded_list = decoder.decode(raw)
        decoded = decoded_list[0]
        assert isinstance(decoded, PybEvents.ConstantsUpdateEvent)
        assert "LED_BRIGHTNESS" in decoded.constants
        assert decoded.constants["LED_BRIGHTNESS"] == "100"
    else:
        print(f"Test: No data received after 2 seconds")
        # If it failed, check the GUI pipe for the ErrorEvent from the KeyError
        if gui_conn.poll(0.1):
             print(f"TP Error Logged: {gui_conn.recv_bytes()}")
        assert False, "No data received on LED source"

    # To prevent BrokenPipeError on shutdown
    stop_event = PybEvents.StopEvent(chamber=0)
    main_in.send_bytes(encoder.encode(stop_event))
    time.sleep(0.1)
    tp.terminate()
    gui_conn.close()
        



