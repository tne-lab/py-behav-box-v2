from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableWidget


class FileCreationTable(QTableWidget):
    deselected_signal = QtCore.pyqtSignal()

    def mousePressEvent(self, event):
        if self.itemAt(event.pos()) is None:
            self.clearSelection()
        self.deselected_signal.emit()
        QTableWidget.mousePressEvent(self, event)
