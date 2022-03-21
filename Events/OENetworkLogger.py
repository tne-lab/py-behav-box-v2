import zmq

from Events.EventLogger import EventLogger
from Events.InputEvent import InputEvent
from Events.StateChangeEvent import StateChangeEvent
from Events.InitialStateEvent import InitialStateEvent


class OENetworkLogger(EventLogger):

    def __init__(self, address, port, nbits=8):
        super().__init__()
        context = zmq.Context()
        self.event_count = 0
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://" + address + ":" + str(port))
        self.nbits = nbits

    def send_ttl_event_code(self, ec):
        # Convert the code to binary
        bc = [int(x) for x in bin(ec)[2:]]
        bc.reverse()
        # Activate the TTL channels according to the bit sequence
        for i in range(len(bc)):
            self.socket.send(
                b"".join([b'TTL Channel=', str(i + 1).encode('ascii'), b' on=', str(bc[i]).encode('ascii')]))
            self.socket.recv()
        # Deactivate remaining TTL channels
        for i in range(self.nbits - len(bc)):
            self.socket.send(b"".join([b'TTL Channel=', str(i + len(binA) + 1).encode('ascii'), b' on=0']))
            self.socket.recv()
        # Wait and send TTL OFF on all channels
        time.sleep(0.005)
        for i in range(self.nbits):
            self.socket.send(b"".join([b'TTL Channel=', str(i + 1).encode('ascii'), b' on=0']))
            self.socket.recv()

    def send_string(self, msg):
        print(msg.encode("utf-8"))
        self.socket.send(msg.encode("utf-8"))
        self.socket.recv()

    def log_events(self, events):
        for e in events:
            self.event_count += 1
            if isinstance(e, InitialStateEvent):
                self.send_string("{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                               e.initial_state.value, e.initial_state.name,
                                                               str(e.metadata)))
            elif isinstance(e, StateChangeEvent):
                self.send_string("{},{},Exit,{},{},{}\n".format(self.event_count, e.entry_time,
                                                                e.initial_state.value, e.initial_state.name,
                                                                str(e.metadata)))
                self.event_count += 1
                self.send_string("{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                               e.new_state.value, e.new_state.name, str(None)))
            elif isinstance(e, InputEvent):
                self.send_string("{},{},Input,{},{},{}".format(self.event_count, e.entry_time,
                                                               e.input_event.value, e.input_event.name,
                                                               str(e.metadata)))

    def close(self):
        pass
