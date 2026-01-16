import unittest
from unittest.mock import MagicMock
from pybehave.Elements.CircleLightElement import CircleLightElement

''' Tests the Elements' functions for:
      1. Interacting with components
      2. Interacting with click events
'''

def test_circle_light_syncs_with_component():
    mock_comp = MagicMock()
    mock_comp.get_state.return_value = True # Simulate light is ON   
    # Initialize element with mock component
    element = CircleLightElement(tg=MagicMock(), x=0, y=0, radius=10, comp=mock_comp, SF=1.0)    
    # Assert internal state matches component
    assert element.on is True
    assert element.has_updated() is False # No changes yet

def test_circle_light_interaction_toggles_component():
    mock_comp = MagicMock()
    element = CircleLightElement(tg=MagicMock(), x=0, y=0, radius=10, comp=mock_comp, SF=1.0)
    element.on = False # Start in OFF state    
    # Simulate a mouse up event
    element.mouse_up_(MagicMock())    
    # Assert that the component's toggle method was called correctly
    mock_comp.toggle.assert_called_with(True)