import ctypes
import threading
from contextlib import ExitStack

import serial

from Components.Component import Component

from Utilities.Exceptions import ComponentRegisterError

from Sources.ThreadSource import ThreadSource


class OSControllerSource(ThreadSource):

    def __init__(self, coms: str):
        super(OSControllerSource, self).__init__()
        self.coms = eval(coms)
        self.sps = None
        self.values = {}
        self.input_ids = {}
        self.close_event = None

    def initialize(self):
        self.close_event = threading.Event()
        self.sps = []
        threads = []
        with OSCARContextManager(self.sps) as stack:
            for i, com in enumerate(self.coms):
                self.sps.append(serial.Serial(port=com, baudrate=1000000, write_timeout=None, timeout=None, dsrdtr=True))
                stack.enter_context(self.sps[i].__enter__())
                self.sps[i].dtr = True
                self.sps[i].reset_input_buffer()
                self.sps[i].reset_output_buffer()
                threads.append(threading.Thread(target=self.serial_thread, args=[i]))
                threads[i].start()
            self.close_event.wait()
            for sp in self.sps:
                reset = Reset()
                reset.b.command = 4
                sp.write(reset.data.to_bytes(1, 'little'))

    def register_component(self, component, metadata):
        if "A" in component.address:
            parts = component.address.split('_')
            if component.get_type() == Component.Type.DIGITAL_OUTPUT:
                tp = 1
            elif component.get_type() == Component.Type.DIGITAL_INPUT:
                tp = 2
            elif component.get_type() == Component.Type.ANALOG_INPUT:
                tp = 3
            else:
                raise ComponentRegisterError
            command = RegisterGPIO()
            command.b.command = 3
            command.b.address = int(parts[1][1])
            command.b.type = tp
            self.sps[int(parts[0])].write(command.data.to_bytes(1, 'little'))
        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.DIGITAL_OUTPUT:
            if component.id not in self.values:
                self.values[component.id] = False
        else:
            self.values[component.id] = 0

        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.ANALOG_INPUT:
            self.input_ids[component.address] = component.id

    def close_source(self):
        self.close_event.set()

    def write_component(self, component_id, msg):
        # If the intended response for the component differs from the current response, change it
        if not msg == self.values[component_id]:
            if isinstance(self.components[component_id].address, list):
                comps = self.components[component_id].address
            else:
                comps = [self.components[component_id].address]
            for comp in comps:
                parts = comp.split('_')
                if 'A' in self.components[component_id].address:
                    command = GPIOOut()
                    command.b.command = 2
                    command.b.address = int(parts[1][1])
                    self.sps[int(parts[0])].write(command.data.to_bytes(1, 'little'))
                elif 'O' in self.components[component_id].address:
                    scaled = msg
                    if scaled < 0:
                        scaled = 0
                    elif scaled > 2.5:
                        scaled = 2.5
                    scaled = round(scaled * 65535 / 2.5)
                    command = AnalogOut()
                    command.b.command = 1
                    command.b.address = int(parts[1][1])
                    scaled = scaled
                    command.b.value = scaled
                    self.sps[int(parts[0])].write(command.data.to_bytes(3, 'little'))
                else:
                    command = DigitalOut()
                    command.b.command = 0
                    command.b.address = int(parts[1])
                    self.sps[int(parts[0])].write(command.data.to_bytes(1, 'little'))
        self.values[component_id] = msg

    def close_component(self, component_id: str) -> None:
        if component_id in self.components:
            if 'A' in self.components[component_id].address:
                parts = self.components[component_id].address.split('_')
                command = RegisterGPIO()
                command.b.command = 3
                command.b.address = int(parts[1][1])
                command.b.type = 0
                self.sps[int(parts[0])].write(command.data.to_bytes(1, 'little'))
            del self.components[component_id]

    def is_available(self):
        return self.available

    def serial_thread(self, serial_index):
        serial_port = self.sps[serial_index]
        nb = serial_port.in_waiting
        serial_command = bytearray()
        while True:
            if nb > 0:
                msg = serial_port.read(nb)
            else:
                msg = serial_port.read(1)
            for b in msg:
                serial_command.extend(b.to_bytes(1, 'little'))
                data = int.from_bytes(serial_command, 'little')
                cid = data & 0x7
                if cid == 0:
                    address = data >> 3 & 0x7
                    input_id = "{}_{}".format(serial_index, str(address))
                    if input_id in self.input_ids:
                        self.values[self.input_ids[input_id]] = not self.values[self.input_ids[input_id]]
                        self.update_component(self.input_ids[input_id], self.values[self.input_ids[input_id]])
                    serial_command = bytearray()
                elif cid == 1:
                    if len(serial_command) == 2:
                        data2 = int.from_bytes(serial_command, 'little')
                        command = AnalogIn()
                        command.data = data2
                        input_id = "{}_{}".format(serial_index, "A" + str(command.b.address))
                        if input_id in self.input_ids:
                            self.values[self.input_ids[input_id]] = command.b.value
                            self.update_component(self.input_ids[input_id], self.values[self.input_ids[input_id]])
                        serial_command = bytearray()
                elif cid == 2:
                    address = data >> 3 & 0x3
                    input_id = "{}_{}".format(serial_index, "A" + str(address))
                    if input_id in self.input_ids:
                        self.values[self.input_ids[input_id]] = not self.values[self.input_ids[input_id]]
                        self.update_component(self.input_ids[input_id], self.values[self.input_ids[input_id]])
                    serial_command = bytearray()


class OSCARContextManager(ExitStack):

    def __init__(self, ports):
        super(OSCARContextManager, self).__init__()
        self.ports = ports

    def __exit__(self, exc_type, exc_value, exc_tb):
        for spi in self.ports:
            r = Reset()
            r.b.command = 4
            spi.write(r.data.to_bytes(1, 'little'))
        super(OSCARContextManager, self).__exit__(exc_type, exc_value, exc_tb)


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


class DigitalOutBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", ctypes.c_uint8, 3),
        ("address", ctypes.c_uint8, 5)
    ]


class DigitalOut(ctypes.Union):
    _fields_ = [("b", DigitalOutBits),
                ("data", ctypes.c_uint8)]


class GPIOOutBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", ctypes.c_uint8, 3),
        ("address", ctypes.c_uint8, 2)
    ]


class GPIOOut(ctypes.Union):
    _fields_ = [("b", GPIOOutBits),
                ("data", ctypes.c_uint8)]


class RegisterGPIOBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", ctypes.c_uint8, 3),
        ("address", ctypes.c_uint8, 2),
        ("type", ctypes.c_uint8, 2)
    ]


class RegisterGPIO(ctypes.Union):
    _fields_ = [("b", RegisterGPIOBits),
                ("data", ctypes.c_uint8)]


class ResetBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", ctypes.c_uint8, 3)
    ]


class Reset(ctypes.Union):
    _fields_ = [("b", RegisterGPIOBits),
                ("data", ctypes.c_uint8)]


class AInParamsBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", ctypes.c_uint8, 3),
        ("fs", ctypes.c_uint8, 2),
        ("ref", ctypes.c_uint8, 1)
    ]


class AInParams(ctypes.Union):
    _fields_ = [("b", AInParamsBits),
                ("data", ctypes.c_uint8)]