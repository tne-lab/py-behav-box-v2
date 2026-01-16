import pytest
import msgspec
from pybehave.Events import PybEvents

@pytest.mark.parametrize("event_cls, args", [
    (PybEvents.StateEnterEvent, {"chamber": 1, "name": "TRIAL", "value": 1}),
    (PybEvents.StateExitEvent, {"chamber": 1, "name": "TRIAL", "value": 2}),
   #(PybEvents.ComponentChangedEvent, {"chamber": 1, "comp": 9 , "index": 3}),
    (PybEvents.GUIEvent, {"chamber": 1, "name": "TRIAL", "value": 4}),
    (PybEvents.ConstantUpdateEvent, {"chamber": 1,"name": "target_speed", "value": 50}),
])
def test_loggable_event_logic(event_cls, args):
    event = event_cls(**args)  
    # These events must support timestamping
    event.acknowledge(123.4)
    assert event.timestamp == 123.4
    
    # These events must be able to turn into a LoggerEvent
    log_entry = event.format()
    assert isinstance(log_entry, PybEvents.LoggerEvent)
    assert log_entry.entry_time == 123.4

# FUNCTIONAL/SETUP EVENTS
@pytest.mark.parametrize("event_cls, args", [
    (PybEvents.ConstantRemoveEvent, {"chamber": 1,"constant": "target_speed"}),
    (PybEvents.ComponentUpdateEvent, {"chamber": 1, "comp_id": "TRIAL", "value": 3}),
    (PybEvents.ComponentRegisterEvent, {
        "comp_type": "DigitalInput", 
        "cid": "Lever1", 
        "address": [1, "GPIO_4"]
    }),
])
def test_functional_event_storage(event_cls, args):
    # These don't need 'format()', we just check if they hold data correctly
    event = event_cls(**args)
    for key, val in args.items():
        assert getattr(event, key) == val

def test_subclass_union_registration():
    # Get the union of all valid events
    event_union = PybEvents.subclass_union(PybEvents.PybEvent)  
    # Extract the actual classes allowed by the Union
    allowed_types = event_union.__args__  
    # This proves that the dynamic discovery logic is picking up your classes
    assert PybEvents.StateEnterEvent in allowed_types
    assert PybEvents.ErrorEvent in allowed_types
    assert PybEvents.ComponentUpdateEvent in allowed_types

def test_event_serialization_hooks():
    encoder = msgspec.msgpack.Encoder(enc_hook=PybEvents.enc_hook)
    decoder = msgspec.msgpack.Decoder(
        type=PybEvents.subclass_union(PybEvents.PybEvent), 
        dec_hook=PybEvents.dec_hook
    )
    # Create an event with metadata (testing dict serialization)
    original_event = PybEvents.StateEnterEvent(
        chamber=1, 
        name="TEST_STATE", 
        value=5, 
        metadata={"info": "extra_data"}
    )
    raw_bytes = encoder.encode(original_event)
    assert isinstance(raw_bytes, bytes)
    decoded_event = decoder.decode(raw_bytes)
    assert isinstance(decoded_event, PybEvents.StateEnterEvent)
    assert decoded_event.name == "TEST_STATE"
    assert decoded_event.metadata["info"] == "extra_data"
    assert decoded_event.chamber == 1

def test_pygame_event():
    #  sample data (mimicking a Pygame mouse click)
    etype = 1025  # pygame.MOUSEBUTTONDOWN
    edict = {"pos": (10, 20), "button": 1}
    meta = {"source": "gui_layer"}
    event = PybEvents.PygameEvent(
        event_type=etype, 
        event_dict=edict, 
        metadata=meta
    )
    assert event.event_type == etype
    assert event.event_dict == edict
    assert event.metadata["source"] == "gui_layer"
 
    # This ensures the pygame event can be sent over IPC pipes
    encoder = msgspec.msgpack.Encoder(enc_hook=PybEvents.enc_hook)
    decoder = msgspec.msgpack.Decoder(
        type=PybEvents.subclass_union(PybEvents.PybEvent), 
        dec_hook=PybEvents.dec_hook
    )
    # Round-trip: Object -> Bytes -> Object
    encoded = encoder.encode(event)
    decoded = decoder.decode(encoded)
    assert isinstance(decoded, PybEvents.PygameEvent)
    assert decoded.event_type == etype
    assert decoded.event_dict["pos"] == [10, 20] # msgspec converts tuples to lists by default