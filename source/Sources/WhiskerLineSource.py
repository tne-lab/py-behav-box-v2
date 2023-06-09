import socket
import os
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

    def __init__(self, address='localhost', port=3233,
                 whisker_path=r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe"):
        super(WhiskerLineSource, self).__init__()
        self.msg = ""
        try:
            win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if not IsWhiskerRunning:
                ws = whisker_path
                os.startfile(ws)
                time.sleep(2)
                print("WHISKER server started")
                win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if IsWhiskerRunning:
                self.available = True
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.client.settimeout(0.5)
                self.client.connect((address, int(port)))
                self.running = threading.Event()
                rt = threading.Thread(target=self.read)
                rt.start()
                self.vals = {}
            else:
                self.available = False
        except:
            traceback.print_exc()
            self.available = False

    def read(self):
        while not self.running.is_set():
            try:
                self.msg += self.client.recv(4096).decode()
                if '\n' in self.msg:
                    msgs = self.msg.split('\n')
                    self.msg = msgs[-1]
                else:
                    msgs = []
                for msg in msgs[:-1]:
                    if msg.startswith('Event:'):
                        div = msg.split(' ')[1].rindex("_")
                        cid, direction = msg.split(' ')[1][:div], msg.split(' ')[1][div+1:]
                        self.update_component(cid, direction == "on")
            except TimeoutError:
                pass

        self.client.send(b'LineRelinquishAll\n')
        self.client.close()

    def register_component(self, task, component):
        super().register_component(task, component)
        if component.get_type() == Component.Type.DIGITAL_INPUT:
            self.client.send(
                'LineClaim {} -ResetOff;LineSetEvent {} on {};LineSetEvent {} off {}\n'.format(component.address,
                                                                                               component.address,
                                                                                               component.id + "_on",
                                                                                               component.address,
                                                                                               component.id + "_off").encode('utf-8'))
            self.vals[component.id] = False
        else:
            if isinstance(component.address, list):
                addr = component.address
            else:
                addr = [component.address]
            msg = ""
            for a in addr:
                msg += 'LineClaim {} -ResetOff\n'.format(a)
            self.client.send(msg.encode('utf-8'))

    def close_source(self):
        self.running.set()

    def write_component(self, component_id, msg):
        if isinstance(self.components[component_id].address, list):
            addr = self.components[component_id].address
        else:
            addr = [self.components[component_id].address]
        out = ""
        for a in addr:
            if msg:
                out += 'LineSetState {} on\n'.format(a)
            else:
                out += 'LineSetState {} off\n'.format(a)
        self.client.send(out.encode('utf-8'))

    def is_available(self):
        return self.available
