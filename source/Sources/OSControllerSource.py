import multiprocessing
import threading
import traceback

from Sources.Source import Source

from Components.Component import Component
import ctypes
import serial

c_uint8 = ctypes.c_uint8


class DigitalOutBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", c_uint8, 3),
        ("address", c_uint8, 5)
    ]


class DigitalOut(ctypes.Union):
    _fields_ = [("b", DigitalOutBits),
                ("data", c_uint8)]


class AnalogOutBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", ctypes.c_uint32, 3),
        ("address", ctypes.c_uint32, 2),
        ("value", ctypes.c_uint32, 16)
    ]


class AnalogOut(ctypes.Union):
    _fields_ = [("b", AnalogOutBits),
                ("data", ctypes.c_uint32)]


class AnalogInBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", ctypes.c_uint16, 3),
        ("address", ctypes.c_uint16, 2),
        ("value", ctypes.c_uint16, 10)
    ]


class AnalogIn(ctypes.Union):
    _fields_ = [("b", AnalogInBits),
                ("data", ctypes.c_uint16)]


class GPIOOutBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", c_uint8, 3),
        ("address", c_uint8, 2)
    ]


class GPIOOut(ctypes.Union):
    _fields_ = [("b", GPIOOutBits),
                ("data", c_uint8)]


class RegisterGPIOBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", c_uint8, 3),
        ("address", c_uint8, 2),
        ("type", c_uint8, 2)
    ]


class RegisterGPIO(ctypes.Union):
    _fields_ = [("b", RegisterGPIOBits),
                ("data", c_uint8)]


class ResetBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", c_uint8, 3)
    ]


class Reset(ctypes.Union):
    _fields_ = [("b", RegisterGPIOBits),
                ("data", c_uint8)]


class ArduinoProcess(multiprocessing.Process):

    def __init__(self, com, pipe, event):
        super(ArduinoProcess, self).__init__()
        self.pipe = pipe
        self.com = com
        self.event = event

    def run(self):
        sp = serial.Serial(port=self.com, baudrate=500000, write_timeout=None, timeout=None, dsrdtr=True)
        sp.dtr = True
        sp.reset_input_buffer()
        sp.reset_output_buffer()
        while not self.event.is_set():
            if self.pipe.poll():
                msg = self.pipe.recv_bytes()
                sp.write(msg)
            nb = sp.in_waiting
            if nb > 0:
                msg = sp.read(nb)
                self.pipe.send_bytes(msg)
        sp.close()


class OSControllerSource(Source):

    def __init__(self, com):
        super(OSControllerSource, self).__init__()
        try:
            conn1, conn2 = multiprocessing.Pipe(duplex=True)
            self.pipe = conn1
            self.event = multiprocessing.Event()
            self.sp = ArduinoProcess(com, conn2, self.event)
            self.sp.start()
            self.available = True
            self.closing = False
            t = threading.Thread(target=lambda: self.handle())
            t.start()
        except:
            traceback.print_exc()
            self.available = False
        self.components = {}
        self.input_ids = {}
        self.values = {}
        self.buffer = ""

    def register_component(self, _, component):
        self.components[component.id] = component
        if component.address.startswith("A"):
            command = RegisterGPIO()
            command.b.command = 3
            command.b.address = int(component.address[1])
            if component.get_type() == Component.Type.DIGITAL_OUTPUT:
                command.b.type = 1
            elif component.get_type() == Component.Type.DIGITAL_INPUT:
                command.b.type = 2
            elif component.get_type() == Component.Type.ANALOG_INPUT:
                command.b.type = 3
            self.pipe.send_bytes(command.data.to_bytes(1, 'little'))
        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.DIGITAL_OUTPUT:
            self.values[component.id] = False
        else:
            self.values[component.id] = 0

        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.ANALOG_INPUT:
            self.input_ids[component.address] = component.id

    def close_source(self):
        reset = Reset()
        reset.b.command = 4
        self.pipe.send_bytes(reset.data.to_bytes(1, 'little'))
        self.closing = True
        if self.available:
            self.event.set()

    def handle(self):
        cur_command = bytes()
        while not self.closing:
            if self.pipe.poll():
                req = self.pipe.recv_bytes()
                for b in req:
                    cur_command = cur_command + b.to_bytes(1, 'little')
                    data = int.from_bytes(cur_command, 'little')
                    cid = data & 0x7
                    if cid == 0:
                        address = data << 3 & 0x7
                        input_id = str(address)
                        if input_id in self.input_ids:
                            self.values[self.input_ids[input_id]] = not self.values[self.input_ids[input_id]]
                        cur_command = bytes()
                    elif cid == 1:
                        if len(cur_command) == 2:
                            data2 = int.from_bytes(cur_command, 'little')
                            command = AnalogIn()
                            command.data = data2
                            input_id = "A" + str(command.b.address)
                            if input_id in self.input_ids:
                                self.values[self.input_ids[input_id]] = command.b.value
                            cur_command = bytes()
                    elif cid == 2:
                        address = data << 3 & 0x3
                        input_id = "A" + str(address)
                        if input_id in self.input_ids:
                            self.values[self.input_ids[input_id]] = not self.values[self.input_ids[input_id]]
                        cur_command = bytes()

    def read_component(self, component_id):
        return self.values[component_id]

    def write_component(self, component_id, msg):
        # If the intended value for the component differs from the current value, change it
        if not msg == self.values[component_id]:
            if self.components[component_id].address.startswith("A"):
                command = GPIOOut()
                command.b.command = 2
                command.b.address = int(self.components[component_id].address[1])
                self.pipe.send_bytes(command.data.to_bytes(1, 'little'))
            elif self.components[component_id].address.startswith("O"):
                command = AnalogOut()
                command.b.command = 1
                command.b.address = int(self.components[component_id].address[1])
                scaled = msg
                if scaled < 0:
                    scaled = 0
                elif scaled > 2.5:
                    scaled = 2.5
                scaled = round(scaled * 65535 / 2.5)
                command.b.value = scaled
                self.pipe.send_bytes(command.data.to_bytes(3, 'little'))
            else:
                command = DigitalOut()
                command.b.command = 0
                command.b.address = int(self.components[component_id].address)
                self.pipe.send_bytes(command.data.to_bytes(1, 'little'))
        self.values[component_id] = msg

    def close_component(self, component_id: str) -> None:
        if self.components[component_id].address.startswith("A"):
            command = RegisterGPIO()
            command.b.command = 3
            command.b.address = int(self.components[component_id].address[1])
            command.b.type = 0
            self.pipe.send_bytes(command.data.to_bytes(1, 'little'))

    def is_available(self):
        return self.available
