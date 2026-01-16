import multiprocessing
import pytest
from unittest.mock import MagicMock
import sys
from pybehave.Tasks.TaskProcess import TaskProcess
from pybehave.Events import PybEvents
import time
import msgspec.msgpack
from typing import List
from integration_simulation_source import IntegrationSimulationSource
from pybehave.Events.CSVEventLogger import CSVEventLogger
import os
import glob

@pytest.fixture
def temp_environment(tmp_path):

    local_dir = tmp_path / "Local"
    local_dir.mkdir()
    tasks_dir = local_dir / "Tasks"
    tasks_dir.mkdir()
    
    (local_dir / "__init__.py").write_text("")
    (tasks_dir / "__init__.py").write_text("")
    
    sys.path.insert(0, str(tmp_path))

    task_path = tasks_dir / "simple_task.py"
    task_path.write_text("""from pybehave.Tasks.Task import Task
from pybehave.Components.BinaryInput import BinaryInput
from pybehave.Components.TimedToggle import TimedToggle                         
from pybehave.Components.Toggle import Toggle
from pybehave.Events import PybEvents
from enum import Enum

class simple_task(Task):
    class States(Enum):
        START = 0
        WAIT =1

    def init_state(self):
        return self.States.START
                         
    @staticmethod
    def get_components():
        return {
            'nose_pokes': [BinaryInput],
            'nose_poke_lights': [TimedToggle]
        }
    
    def START(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StateEnterEvent):                 
           self.nose_poke_lights.toggle(1.5) #don't change to 1s - too fast, task fails
           self.change_state(self.States.WAIT)
        
    
    def WAIT(self, event: PybEvents.PybEvent):
        pass                 
        #if isinstance(event, PybEvents.ComponentChangedEvent) and event.comp is self.nose_pokes and event.comp.state: 
        #   self.nose_poke_lights.toggle(False)
""")

    address_path = tasks_dir / "simple_task_address.py"
    address_path.write_text("""addresses = AddressFile()
addresses.add_component("nose_pokes", "BinaryInput", "SimSource", 0, 0, {})
addresses.add_component("nose_poke_lights", "TimedToggle", "SimSource", 1, 0, {})
""")
    
    return str(tmp_path), "simple_task", str(address_path)

def test_core_logic_integration(temp_environment):
    
    temp_dir, task_name, address_path = temp_environment
           
    # to ensure sys.path is ready for the TaskProcess
    if temp_dir not in sys.path:
        sys.path.insert(0, temp_dir)
    
    logger_config = "CSVEventLogger((||Output||))"

    # create the pipes for inter-process communication
    main_conn, tp_main_conn = multiprocessing.Pipe()
    gui_conn, tp_gui_conn = multiprocessing.Pipe()
    source_conn, tp_source_conn = multiprocessing.Pipe()

    encoder = msgspec.msgpack.Encoder(enc_hook=PybEvents.enc_hook)
    decoder = msgspec.msgpack.Decoder(
    type=List[PybEvents.subclass_union(PybEvents.PybEvent)], 
    dec_hook=PybEvents.dec_hook
    )
    
    sim_animal = IntegrationSimulationSource()
    sim_animal.sid = 'SimSource'  
    sim_animal.queue = source_conn  
    
    sim_animal.start()  # This calls sim_animal.run() in a new process
  
    # Start TaskProcess with source already registered
    tp = TaskProcess(mainq=tp_main_conn, guiq=tp_gui_conn, sourceq={'SimSource': tp_source_conn})
    tp.start()
    
    metadata = {
        "chamber": 0,
        "subject": "test_subject",
        'task': task_name,
        "protocol": None,  
        "address_file": address_path,
        
    }
    
    add_task_event = PybEvents.AddTaskEvent(
    chamber=0, 
    task_name=task_name, 
    task_event_loggers= logger_config, 
    metadata=metadata
    )
    main_conn.send_bytes(encoder.encode(add_task_event))

    output_path = os.path.join(str(temp_dir), "") # w/o the "" CSVLogger will try to create the file directly in the temp local folder
    output_event = PybEvents.OutputFileChangedEvent(
    chamber=0, 
    output_file=output_path, 
    subject="test_subject"
    )
    main_conn.send_bytes(encoder.encode(output_event))

    if gui_conn.poll(timeout=2.0):
        events = decoder.decode(gui_conn.recv_bytes())
        for e in events:
            if isinstance(e, PybEvents.InitEvent):
                print(" TaskProcess found and read the files!")
            if isinstance(e, PybEvents.ErrorEvent):
                print(f" TaskProcess could not load files. Error: {e.traceback}")

    time.sleep(0.5)
    start_event = PybEvents.StartEvent(chamber=0)
    main_conn.send_bytes(encoder.encode(start_event))
   
    main_conn.send_bytes(encoder.encode(PybEvents.HeartbeatEvent()))
    
    time.sleep(2.0) 
  
    csv_files = glob.glob(os.path.join(temp_dir, "*.csv"))
    if csv_files:
        print(f"Created {csv_files[0]}")
    assert len(csv_files) > 0, "No CSV generated"

    
    test_checkups = {
        "poke_detected": False,
        "poke_released": False,
        "light_off": False
    }
    stop_time = time.time() + 8.0 

    while time.time() < stop_time:
        # Always keep the TP "ticking" for timers
        main_conn.send_bytes(encoder.encode(PybEvents.HeartbeatEvent()))
        if gui_conn.poll(0.01):
            events = decoder.decode(gui_conn.recv_bytes())
            for e in events:
                # debug print
                comp_id = getattr(e, 'comp_id', '')
                val = getattr(e, 'value', '')
               # print(f"Captured: {type(e).__name__} - {comp_id} = {val}")
                if isinstance(e, PybEvents.ErrorEvent):
                    print("\n" + "="*20 + " TASK CRASHED " + "="*20)
                    print(e.traceback) 
                    print("="*54 + "\n")       
                if isinstance(e, PybEvents.ComponentUpdateEvent):
                    if "nose_pokes" in comp_id and val is True:
                        test_checkups["poke_detected"] = True            
                    if "nose_pokes" in comp_id and val is False:
                        test_checkups["poke_released"] = True 
                    if "nose_poke_lights" in comp_id and val is False:
                        test_checkups["light_off"] = True        
        # full circuit is complete
        if test_checkups["poke_released"] and test_checkups["light_off"]:
            break
    with open(csv_files[0], 'r') as f:
        lines = f.readlines()
        print(f"Last logged event: {lines[-1]}")
        last_line = lines[-1].strip() # remove the \n
        row = last_line.split(',')
        
        assert "ComponentChangedEvent" in row[2], f"Expected ComponentChangedEvent, got {row[2]}"
        assert "nose_pokes" in row[4], f"Expected nose_pokes-0-0, got {row[4]}"
        assert "False" in row[5], f"Expected value to be False, got {row[5]}"
    # Final validation
    assert test_checkups["poke_detected"] and test_checkups["poke_released"], "Poke sequence incomplete"
    assert test_checkups["light_off"], "Light never turned off - Task logic failed!"
    print("\n" + "-"*10 + " INTEGRATION TEST COMPLETE: Task Process and Event logging verified " + "-"*10)

    # To prevent BrokenPipeError on shutdown
    stop_event = PybEvents.StopEvent(chamber=0)
    main_conn.send_bytes(encoder.encode(stop_event))
    time.sleep(0.1)
    tp.terminate()
    sim_animal.terminate()
    tp.join()
    sim_animal.join()
    main_conn.close()
    gui_conn.close()
    source_conn.close()
