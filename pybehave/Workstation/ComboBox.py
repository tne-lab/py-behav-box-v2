from PyQt5 import QtCore
from PyQt5.QtWidgets import QComboBox


class ComboBox(QComboBox):
    new_signal = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(ComboBox, self).__init__(parent)
        self.lastSelected = None
        self.activated[str].connect(self.onActivated)

    def onActivated(self, text):
        self.new_signal.emit(self.lastSelected, text)
        self.lastSelected = text
