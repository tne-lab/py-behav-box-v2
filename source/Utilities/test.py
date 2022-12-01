import os
import time

import psutil
import ctypes
import serial

c_uint8 = ctypes.c_uint8


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


p = psutil.Process(os.getpid())
p.nice(psutil.REALTIME_PRIORITY_CLASS)
sp = serial.Serial(port='COM6', baudrate=500000, write_timeout=None, timeout=None, dsrdtr=True)
sp.dtr = True
sp.reset_input_buffer()
sp.reset_output_buffer()
time.sleep(3)
command = RegisterGPIO()
command.b.command = 3
command.b.address = 0
command.b.type = 3
sp.write(command.data.to_bytes(1, 'little'))
command.b.address = 1
sp.write(command.data.to_bytes(1, 'little'))

t = time.perf_counter()
skip = False

t1 = time.perf_counter()
count = 0
count2 = 0
btotal = 0
while time.perf_counter() - t < 6*60:
    nb = sp.in_waiting
    if nb > 0:
        msg = sp.read(1)
        data = int.from_bytes(msg, 'little')
        cid = data & 0x7
        if cid == 0 and not skip:
            count += 1
            command = 0
            sp.write(command.to_bytes(1, 'little'))
            skip = False
        elif cid == 1:
            count2 += 1
            skip = True
        else:
            skip = False
        btotal += 1
    if time.perf_counter() - t1 > 1:
        # print(count)
        # print(count2)
        # print(btotal)
        count = 0
        count2 = 0
        btotal = 0
        t1 = time.perf_counter()

reset = Reset()
reset.b.command = 4
sp.write(reset.data.to_bytes(1, 'little'))
