import zmq
from datetime import datetime
import os
from source.Events.GUIEventLogger import GUIEventLogger
from source.Events.InputEvent import InputEvent
from source.Events.StateChangeEvent import StateChangeEvent
from source.Events.InitialStateEvent import InitialStateEvent
from source.Events.FinalStateEvent import FinalStateEvent
from source.Events.OEEvent import OEEvent
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from Workstation.IconButton import IconButton


class OENetworkLogger(GUIEventLogger):

    def __init__(self, address, port, nbits=8):
        super().__init__()
        context = zmq.Context()
        self.event_count = 0
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://" + address + ":" + str(port))
        self.nbits = nbits

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

    def set_chamber(self, cw):
        super(OENetworkLogger, self).set_chamber(cw)
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.rec_dir.setText("{}/py-behav/{}/Data/{}/{}/".format(desktop,
                                                                 self.cw.task_name.currentText(),
                                                                 self.cw.subject.text(),
                                                                 datetime.now().strftime(
                                                                     "%m-%d-%Y")))

    def acquisition(self):
        if not self.acq:
            self.acq_button.icon = 'Workstation/icons/stop_play.svg'
            self.acq_button.hover_icon = 'Workstation/icons/stop_play_hover.svg'
            self.acq_button.setIcon(QIcon(self.acq_button.icon))
            self.log_events([OEEvent("startAcquisition", 0)])
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
            self.log_events([OEEvent("stopAcquisition", 0)])
            self.acq = False

    def record(self):
        if not self.rec:
            self.acq_button.icon = 'Workstation/icons/stop_play.svg'
            self.acq_button.hover_icon = 'Workstation/icons/stop_play_hover.svg'
            self.acq_button.setIcon(QIcon(self.acq_button.icon))
            self.rec_button.icon = 'Workstation/icons/stop_record.svg'
            self.rec_button.hover_icon = 'Workstation/icons/stop_record_hover.svg'
            self.rec_button.setIcon(QIcon(self.rec_button.icon))
            self.log_events([OEEvent("startRecord", 0)])
            self.acq = True
            self.rec = True
        elif self.rec:
            self.rec_button.icon = 'Workstation/icons/record.svg'
            self.rec_button.hover_icon = 'Workstation/icons/record_hover.svg'
            self.rec_button.setIcon(QIcon(self.rec_button.icon))
            self.log_events([OEEvent("stopRecord", 0)])
            self.rec = False

    def get_file_path(self):
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        file_name = QFileDialog.getExistingDirectory(self.oe_group, 'Select Folder', "{}/py-behav/{}/".format(desktop,
                                                                                                              self.cw.task_name.currentText()))
        if len(file_name) > 0:
            self.rec_dir.setText(file_name)

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
        self.socket.send(msg.encode("utf-8"))
        self.socket.recv()

    def log_events(self, events):
        for e in events:
            if isinstance(e, OEEvent):
                if e.event_type == 'startAcquisition':
                    self.send_string("startAcquisition")
                elif e.event_type == 'stopAcquisition':
                    self.send_string("stopAcquisition")
                elif e.event_type == 'startRecord':
                    self.send_string("startRecord RecDir={} prependText={} appendText={}".format(self.rec_dir.text(),
                                                                                                 self.pre.text(),
                                                                                                 self.app.text()))
                elif e.event_type == 'stopRecord':
                    self.send_string("stopRecord")
            elif isinstance(e, InitialStateEvent):
                self.event_count += 1
                self.send_string("{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                               e.initial_state.value, e.initial_state.name,
                                                               str(e.metadata)))
            elif isinstance(e, FinalStateEvent):
                self.event_count += 1
                self.send_string("{},{},Exit,{},{},{}".format(self.event_count, e.entry_time,
                                                              e.final_state.value, e.final_state.name,
                                                              str(e.metadata)))
            elif isinstance(e, StateChangeEvent):
                self.event_count += 1
                self.send_string("{},{},Exit,{},{},{}".format(self.event_count, e.entry_time,
                                                              e.initial_state.value, e.initial_state.name,
                                                              str(e.metadata)))
                self.event_count += 1
                self.send_string("{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                               e.new_state.value, e.new_state.name, str(None)))
            elif isinstance(e, InputEvent):
                self.event_count += 1
                self.send_string("{},{},Input,{},{},{}".format(self.event_count, e.entry_time,
                                                               e.input_event.value, e.input_event.name,
                                                               str(e.metadata)))

    def close(self):
        pass

    def get_widget(self):
        return self.oe_group
