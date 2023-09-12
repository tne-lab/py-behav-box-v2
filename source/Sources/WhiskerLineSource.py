import os
import socket
import threading
import time
import traceback

import win32gui

from Components.Component import Component
from Sources.ThreadSource import ThreadSource

IsWhiskerRunning = False


def look_for_program(hwnd, program_name):
    global IsWhiskerRunning
    if program_name in win32gui.GetWindowText(hwnd):
        win32gui.CloseWindow(hwnd)  # Minimize Window
        IsWhiskerRunning = True


class WhiskerLineSource(ThreadSource):

    def __init__(self, address='localhost', port=3233,
                 whisker_path=r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe"):
        super(WhiskerLineSource, self).__init__()
        self.vals = {}
        self.available = True
        self.address = address
        self.port = int(port)
        self.whisker_path = whisker_path
        self.msg = ""
        self.client = None
        self.closing = False

    def initialize(self):
        try:
            win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if not IsWhiskerRunning:
                ws = self.whisker_path
                os.startfile(ws)
                time.sleep(2)
                print("WHISKER server started")
                win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if IsWhiskerRunning:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.client.connect((self.address, self.port))
                self.client.settimeout(1)
                while not self.closing:
                    try:
                        new_data = self.client.recv(4096)
                        self.msg += new_data.decode('UTF-8')
                        if '\n' in self.msg:
                            msgs = self.msg.split('\n')
                            self.msg = msgs[-1]
                        else:
                            msgs = []
                        for msg in msgs[:-1]:
                            if msg.startswith('Event:'):
                                div = msg.split(' ')[1].rindex("_")
                                cid, direction = msg.split(' ')[1][:div], msg.split(' ')[1][div + 1:]
                                self.update_component(cid, direction == "on")
                    except socket.timeout:
                        pass
            else:
                self.unavailable()
        except:
            traceback.print_exc()
            self.unavailable()

    def register_component(self, component, metadata):
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
        self.closing = True
        self.client.send(b'LineRelinquishAll\n')
        self.client.close()

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
