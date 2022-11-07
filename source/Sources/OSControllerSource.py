import threading
import time

import serial_asyncio
import asyncio

from Sources.Source import Source

from Components.Component import Component
import ctypes
c_uint8 = ctypes.c_uint8


class DigitalOutBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", c_uint8, 3),
        ("address", c_uint8, 5)
    ]


class DigitalOut(ctypes.Union):
    _fields_ = [("b", DigitalOutBits),
                ("data", c_uint8)]


class AnalogInBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ("command", c_uint8, 3),
        ("address", c_uint8, 2),
        ("value", ctypes.c_uint16, 10)
    ]


class AnalogIn(ctypes.Union):
    _fields_ = [("b", AnalogInBits),
                ("data", c_uint8 * 2)]


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


two_byte = c_uint8 * 2


class OSControllerSource(Source):

    class OSCSProtocol(asyncio.Protocol):

        def __init__(self, oscs):
            super().__init__()
            self.oscs = oscs
            self.transport = None
            self.buf = bytes()
            self.st = time.perf_counter()
            self.count = 0

        def connection_made(self, transport):
            self.transport = transport
            # self.transport.serial.rts = False  # You can manipulate Serial object via transport
            self.transport.serial.dtr = True

        def data_received(self, bdata):
            self.buf += bdata
            self.count += 1
            # print(len(self.buf))
            while len(self.buf) > 0:
                data = int.from_bytes(self.buf[0:1], 'little')
                # print(bin(data))
                cid = data & 0x7
                if cid == 0:
                    address = data << 3 & 0x7
                    input_id = str(address)
                    if input_id in self.oscs.input_ids:
                        self.oscs.values[self.oscs.input_ids[input_id]] = not self.oscs.values[self.oscs.input_ids[input_id]]
                    self.buf = self.buf[1:]
                elif cid == 1:
                    if len(self.buf) >= 2:
                        data2 = int.from_bytes(self.buf[1:2] + self.buf[0:1], 'little')
                        command = AnalogIn()
                        command.data = two_byte(data, data2)
                        # print(bin(command.data[1]) + bin(command.data[0]))
                        # print(command.b.address)
                        # print(command.b.value)
                        input_id = "A" + str(command.b.address)
                        if input_id in self.oscs.input_ids:
                            self.oscs.values[self.oscs.input_ids[input_id]] = command.b.value
                        self.buf = self.buf[2:]
                    else:
                        break
                elif cid == 2:
                    address = data << 3 & 0x3
                    input_id = "A" + str(address)
                    if input_id in self.oscs.input_ids:
                        self.oscs.values[self.oscs.input_ids[input_id]] = not self.oscs.values[self.oscs.input_ids[input_id]]
                    self.buf = self.buf[1:]
            if time.perf_counter() - self.st > 1:
                self.st = time.perf_counter()
                print(self.count)
                self.count = 0

    def __init__(self, com):
        super(OSControllerSource, self).__init__()
        try:
            # self.com = serial.Serial(port=com, baudrate=115200, write_timeout=0, timeout=0.000001, dsrdtr=True)
            self.loop = asyncio.get_event_loop()
            coro = serial_asyncio.create_serial_connection(self.loop, lambda: self.OSCSProtocol(self), com, baudrate=115200, write_timeout=0, timeout=0, dsrdtr=True)
            self.com, _ = self.loop.run_until_complete(coro)
            # self.com.dtr = True
            # self.com.reset_input_buffer()
            # self.com.reset_output_buffer()
            self.available = True
            # self.event = threading.Event()
            self.closing = False
            t = threading.Thread(target=lambda: self.loop.run_forever())
            t.start()
        except:
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
            self.com.serial.write(command.data.to_bytes(1, 'little'))
            # self.com.write(command.data.to_bytes(1, 'little'))
            print(bin(command.data))
        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.DIGITAL_OUTPUT:
            self.values[component.id] = False
        else:
            self.values[component.id] = 0

        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.ANALOG_INPUT:
            self.input_ids[component.address] = component.id

    def close_source(self):
        self.closing = True
        # self.event.wait()
        # self.com.__exit__()
        self.loop.close()

    def read(self):
        while not self.closing:
            st = time.perf_counter()
            if self.com.in_waiting > 0:
                bdata = self.com.read(1)
                data = int.from_bytes(bdata, 'little')
                print(bin(data))
                cid = data & 0x7
                if cid == 0:
                    address = data << 3 & 0x7
                    input_id = str(address)
                    if input_id in self.input_ids:
                        self.values[self.input_ids[input_id]] = not self.values[self.input_ids[input_id]]
                elif cid == 1:
                    data2 = int.from_bytes(self.com.read(1)+bdata, 'little')
                    command = AnalogIn()
                    command.data = two_byte(data, data2)
                    print(bin(command.data[1])+bin(command.data[0]))
                    print(command.b.address)
                    print(command.b.value)
                    input_id = "A" + str(command.b.address)
                    if input_id in self.input_ids:
                        self.values[self.input_ids[input_id]] = command.b.value
                elif cid == 2:
                    address = data << 3 & 0x3
                    input_id = "A" + str(address)
                    if input_id in self.input_ids:
                        self.values[self.input_ids[input_id]] = not self.values[self.input_ids[input_id]]
            print(time.perf_counter() - st)
        self.event.set()

    def read_component(self, component_id):
        return self.values[component_id]

    def write_component(self, component_id, msg):
        # If the intended value for the component differs from the current value, change it
        if not msg == self.values[component_id]:
            if self.components[component_id].address.startswith("A"):
                command = GPIOOut()
                command.b.command = 2
                command.b.address = int(self.components[component_id].address[1])
                # self.com.write(command.data.to_bytes(1, 'little'))
                self.com.serial.write(command.data.to_bytes(1, 'little'))
            else:
                command = DigitalOut()
                command.b.command = 0
                command.b.address = int(self.components[component_id].address)
                # self.com.write(command.data.to_bytes(1, 'little'))
                self.com.serial.write(command.data.to_bytes(1, 'little'))
            print(bin(command.data))
        self.values[component_id] = msg

    def close_component(self, component_id: str) -> None:
        if self.components[component_id].address.startswith("A"):
            command = RegisterGPIO()
            command.b.command = 3
            command.b.address = int(self.components[component_id].address[1])
            command.b.type = 0
            # self.com.write(command.data.to_bytes(1, 'little'))
            self.com.serial.write(command.data.to_bytes(1, 'little'))

    def is_available(self):
        return self.available
