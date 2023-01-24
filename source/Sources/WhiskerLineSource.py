import socket
import subprocess
import threading
import time
import traceback

import win32gui

from Components.Component import Component
from Sources.Source import Source


IsWhiskerRunning = False


def look_for_program(hwnd, program_name):
    global IsWhiskerRunning
    if program_name in win32gui.GetWindowText(hwnd):
        win32gui.CloseWindow(hwnd)  # Minimize Window
        IsWhiskerRunning = True


class WhiskerLineSource(Source):

    def __init__(self, address='localhost', port=3233, whisker_path=r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe"):
        super(WhiskerLineSource, self).__init__()
        self.msg = ""
        try:
            win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if not IsWhiskerRunning:
                ws = whisker_path
                window = subprocess.Popen(ws)
                time.sleep(2)
                print("WHISKER server started", window)
                win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if IsWhiskerRunning:
                self.available = True
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.client.connect((address, int(port)))
                self.running = threading.Event()
                rt = threading.Thread(target=lambda: self.read())
                rt.start()
                self.vals = {}
            else:
                self.available = False
        except:
            traceback.print_exc()
            self.available = False

    def read(self):
        while not self.running.is_set():
            self.msg += self.client.recv(4096).decode()
            print(self.msg)
            if self.msg.startswith('Event:'):
                if '\n' in self.msg:
                    msgs = self.msg.split('\n')
                    for msg in msgs[:-1]:
                        self.vals[msg.split(' ')[1]] = not self.vals[msg.split(' ')[1]]
                    self.msg = msgs[-1]

        self.client.send(b'LineRelinquishAll\n')
        self.client.close()

    def register_component(self, _, component):
        self.components[component.id] = component
        if component.get_type() == Component.Type.DIGITAL_INPUT:
            self.client.send(
                'LineClaim {} -ResetOff;LineSetEvent {} both {}\n'.format(component.address, component.address,
                                                                          component.id).encode('utf-8'))
            self.vals[component.id] = False
        else:
            self.client.send('LineClaim {} -ResetOff\n'.format(component.address).encode('utf-8'))

    def close_source(self):
        self.running.set()

    def read_component(self, component_id):
        return self.vals[component_id]

    def write_component(self, component_id, msg):
        if msg:
            self.client.send('LineSetState {} on\n'.format(self.components[component_id].address).encode('utf-8'))
        else:
            self.client.send('LineSetState {} off\n'.format(self.components[component_id].address).encode('utf-8'))

    def is_available(self):
        return self.available
