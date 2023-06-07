from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from Utilities.dictionary_to_save_string import dictionary_to_save_string

if TYPE_CHECKING:
    from Events.Event import Event

import zmq
from datetime import datetime
import os
import time

from Events.GUIEventLogger import GUIEventLogger
from Events.InputEvent import InputEvent
from Events.StateChangeEvent import StateChangeEvent
from Events.InitialStateEvent import InitialStateEvent
from Events.FinalStateEvent import FinalStateEvent
from Events.OEEvent import OEEvent
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from Workstation.ChamberWidget import ChamberWidget
from Workstation.IconButton import IconButton


class OENetworkLogger(GUIEventLogger):

    def __init__(self, address: str, port: str):
        super().__init__()
        context = zmq.Context()
        self.fd = None
        self.event_count = 0
        self.socket = context.socket(zmq.REQ)
        self.socket.set(zmq.REQ_RELAXED, True)
        self.socket.connect("tcp://" + address + ":" + str(port))

        self.oe_group = QGroupBox('Open Ephys')
        oe_group_layout = QHBoxLayout(self.oe_group)
        self.oe_group.setLayout(oe_group_layout)
        oe_rec_layout = QVBoxLayout(self.oe_group)
        oe_text_layout = QHBoxLayout(self.oe_group)
        oe_control_layout = QVBoxLayout(self.oe_group)

        # Widget corresponding to the path for the output folder for OpenEphys
        rec_dir_box = QGroupBox('RecDir')
        rec_dir_layout = QHBoxLayout(self.oe_group)
        rec_dir_box.setLayout(rec_dir_layout)
        self.rec_dir = QLineEdit("")
        self.rec_dir.setReadOnly(True)
        rec_dir_layout.addWidget(self.rec_dir)
        self.rec_dir_browse = QPushButton()
        self.rec_dir_browse.setIcon(QIcon('Workstation/icons/folder.svg'))
        self.rec_dir_browse.setFixedWidth(30)
        self.rec_dir_browse.clicked.connect(lambda: self.get_file_path())
        rec_dir_layout.addWidget(self.rec_dir_browse)
        oe_rec_layout.addWidget(rec_dir_box)

        pre_box = QGroupBox('prependText')
        pre_layout = QHBoxLayout(self.oe_group)
        pre_box.setLayout(pre_layout)
        self.pre = QLineEdit("")
        pre_layout.addWidget(self.pre)
        oe_text_layout.addWidget(pre_box)

        app_box = QGroupBox('appendText')
        app_layout = QHBoxLayout(self.oe_group)
        app_box.setLayout(app_layout)
        self.app = QLineEdit("")
        app_layout.addWidget(self.app)
        oe_text_layout.addWidget(app_box)
        oe_rec_layout.addLayout(oe_text_layout)
        oe_group_layout.addLayout(oe_rec_layout)

        self.acq_button = IconButton('Workstation/icons/play.svg', 'Workstation/icons/play_hover.svg')
        self.acq_button.setFixedWidth(30)
        self.acq_button.clicked.connect(self.acquisition)
        oe_control_layout.addWidget(self.acq_button)
        self.rec_button = IconButton('Workstation/icons/record.svg', 'Workstation/icons/record_hover.svg')
        self.rec_button.setFixedWidth(30)
        self.rec_button.clicked.connect(self.record)
        oe_control_layout.addWidget(self.rec_button)
        oe_group_layout.addLayout(oe_control_layout)

        self.acq = False
        self.rec = False

    def set_chamber(self, cw: ChamberWidget) -> None:
        super(OENetworkLogger, self).set_chamber(cw)
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.rec_dir.setText("{}/py-behav/{}/Data/{}/{}/".format(desktop,
                                                                 self.cw.task_name.currentText(),
                                                                 self.cw.subject.text(),
                                                                 datetime.now().strftime(
                                                                     "%m-%d-%Y")))

    def acquisition(self) -> None:
        if not self.acq:
            self.acq_button.icon = 'Workstation/icons/stop_play.svg'
            self.acq_button.hover_icon = 'Workstation/icons/stop_play_hover.svg'
            self.acq_button.setIcon(QIcon(self.acq_button.icon))
            self.log_events([OEEvent(self.cw.task, "startAcquisition")])
            self.acq = True
        elif self.acq:
            self.acq_button.icon = 'Workstation/icons/play.svg'
            self.acq_button.hover_icon = 'Workstation/icons/play_hover.svg'
            self.acq_button.setIcon(QIcon(self.acq_button.icon))
            if self.rec:
                self.rec_button.icon = 'Workstation/icons/record.svg'
                self.rec_button.hover_icon = 'Workstation/icons/record_hover.svg'
                self.rec_button.setIcon(QIcon(self.rec_button.icon))
                self.rec = False
            self.log_events([OEEvent(self.cw.task, "stopAcquisition")])
            self.acq = False

    def record(self) -> None:
        if not self.rec:
            self.acq_button.icon = 'Workstation/icons/stop_play.svg'
            self.acq_button.hover_icon = 'Workstation/icons/stop_play_hover.svg'
            self.acq_button.setIcon(QIcon(self.acq_button.icon))
            self.rec_button.icon = 'Workstation/icons/stop_record.svg'
            self.rec_button.hover_icon = 'Workstation/icons/stop_record_hover.svg'
            self.rec_button.setIcon(QIcon(self.rec_button.icon))
            self.log_events([OEEvent(self.cw.task, "startRecord")])
            self.acq = True
            self.rec = True
        elif self.rec:
            self.rec_button.icon = 'Workstation/icons/record.svg'
            self.rec_button.hover_icon = 'Workstation/icons/record_hover.svg'
            self.rec_button.setIcon(QIcon(self.rec_button.icon))
            self.log_events([OEEvent(self.cw.task, "stopRecord")])
            self.rec = False

    def get_file_path(self) -> None:
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.fd = QFileDialog(self.oe_group)
        self.fd.setFileMode(QFileDialog.Directory)
        self.fd.setViewMode(QFileDialog.List)
        self.fd.setDirectory("{}/py-behav/{}/".format(desktop, self.cw.task_name.currentText()))
        self.fd.setWindowTitle('Select Folder')
        self.fd.accept = self.open_folder
        self.fd.show()

    def open_folder(self):
        if len(self.fd.selectedFiles()[0]) > 1:
            self.rec_dir.setText(self.fd.selectedFiles()[0])
        super(QFileDialog, self.fd).accept()

    def send_ttl_event(self, ec: int, ttl_type: str | float) -> None:
        if ttl_type == 'on':
            self.socket.send(
                b"".join([b'TTL Channel=', str(ec).encode('ascii'), b' on=1']))
            self.receive()
        elif ttl_type == 'off':
            self.socket.send(
                b"".join([b'TTL Channel=', str(ec).encode('ascii'), b' on=0']))
            self.receive()
        else:
            t = threading.Thread(target=self.send_ttl_event_, args=[ec, ttl_type])
            t.start()

    def send_ttl_event_(self, ec: int, dur: float) -> None:
        # Activate the TTL channels according to the bit sequence
        self.socket.send(
            b"".join([b'TTL Channel=', str(ec).encode('ascii'), b' on=1']))
        self.receive()
        time.sleep(dur)
        self.socket.send(
            b"".join([b'TTL Channel=', str(ec).encode('ascii'), b' on=0']))
        self.receive()

    def send_string(self, msg: str) -> None:
        self.socket.send(msg.encode("utf-8"))
        self.receive()

    def receive(self) -> None:
        try:
            self.socket.recv(flags=zmq.NOBLOCK)
        except zmq.ZMQError:
            pass

    def log_events(self, events: list[Event]) -> None:
        for e in events:
            if isinstance(e, OEEvent):
                if e.event_type == 'startAcquisition':
                    self.send_string("startAcquisition")
                elif e.event_type == 'stopAcquisition':
                    self.send_string("stopAcquisition")
                elif e.event_type == 'startRecord':
                    self.send_string("startRecord RecDir={} prependText={} appendText={}".format(self.rec_dir.text(),
                                                                                                 self.pre.text() + e.metadata.pre if e.metadata is not None and "pre" in e.metadata else self.pre.text(),
                                                                                                 self.app.text()))
                elif e.event_type == 'stopRecord':
                    self.send_string("stopRecord")
            elif isinstance(e, InitialStateEvent):
                self.event_count += 1
                if e.metadata is not None and 'ttl' in e.metadata and e.metadata['ttl']:
                    self.send_ttl_event(e.initial_state.value, 'on')
                else:
                    self.send_string("{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                                   e.initial_state.value, e.initial_state.name,
                                                                   dictionary_to_save_string(e.metadata)))
            elif isinstance(e, FinalStateEvent):
                self.event_count += 1
                if e.metadata is not None and 'ttl' in e.metadata and e.metadata['ttl']:
                    self.send_ttl_event(e.final_state.value, 'off')
                else:
                    self.send_string("{},{},Exit,{},{},{}".format(self.event_count, e.entry_time,
                                                                  e.final_state.value, e.final_state.name,
                                                                  dictionary_to_save_string(e.metadata)))
            elif isinstance(e, StateChangeEvent):
                self.event_count += 1
                if e.metadata is not None and 'ttl' in e.metadata and e.metadata['ttl']:
                    self.send_ttl_event(e.initial_state.value, 'off')
                    self.event_count += 1
                    self.send_ttl_event(e.new_state.value, 'on')
                else:
                    self.send_string("{},{},Exit,{},{},{}".format(self.event_count, e.entry_time,
                                                                  e.initial_state.value, e.initial_state.name,
                                                                  dictionary_to_save_string(e.metadata)))
                    self.event_count += 1
                    self.send_string("{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                                   e.new_state.value, e.new_state.name, str(None)))
            elif isinstance(e, InputEvent):
                self.event_count += 1
                if e.metadata is not None and 'ttl' in e.metadata and e.metadata['ttl']:
                    self.send_ttl_event(e.input_event.value, e.metadata['ttl'])
                else:
                    self.send_string("{},{},Input,{},{},{}".format(self.event_count, e.entry_time,
                                                                   e.input_event.value, e.input_event.name,
                                                                   dictionary_to_save_string(e.metadata)))

    def close(self) -> None:
        self.socket.close()

    def get_widget(self) -> QWidget:
        return self.oe_group
