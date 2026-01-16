import pytest
from state_transition import StateTransition

'''
 Test's for two functions within Task.                          
    1. The state transitioned i.e change_state works                            
    2. The component name was created and registered - 
       (write_component & add to source buffer)                          

'''

def test_change_state_logging():
    '''  Verifying change_state logs correct events''' 
    task, mock_tp = StateTransition.setup_task()   
    task.change_state(StateTransition.States.PAUSED)
    logged_events = mock_tp.tp_q
    assert len(logged_events) == 2
    exit_event = logged_events[0]
    #print(exit_event)
    assert exit_event.name == StateTransition.States.INITIAL.name
    assert exit_event.chamber == 1 
    enter_event = logged_events[1]
    assert enter_event.name == StateTransition.States.PAUSED.name
    assert enter_event.chamber == 1

def test_write_component_command():
    ''' Verifying write_component logs to both GUI and Source Buffer'''
    task, mock_tp = StateTransition.setup_task()
    COMPONENT_KEY = 'light-1-0'
    MOCK_SOURCE_ID = 'MOCK_SOURCE'
    assert COMPONENT_KEY in task.components 
    # Reconfigure component to use the Mock Source
    config = list(task.components[COMPONENT_KEY])
    config[2] = MOCK_SOURCE_ID  # Component tuple format: (0: Object, 1: Address, 2: Source ID)    
    task.components[COMPONENT_KEY] = tuple(config) # no index at config- KeyError 'C', str->tup breaks the string (M,O,C..)    
    # Set up the mock source buffer
    mock_tp.source_buffers= {MOCK_SOURCE_ID: []}  
    task.write_component('light-1-0', True)     
    mock_tp.log_gui_event.assert_called_once()
     
    # The Task class appends the event to the source buffer
    source_buffer = mock_tp.source_buffers['MOCK_SOURCE']   
    assert len(source_buffer) == 1   
    # Check the event created for the source buffer
    component_event = source_buffer[0]
    print(component_event)
    assert component_event.comp_id == 'light-1-0'
    assert component_event.value is True

