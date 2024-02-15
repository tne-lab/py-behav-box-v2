from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtGui import *


class IconButton(QPushButton):

    def __init__(self, icon, hover_icon=None, disabled_icon=None, parent=None):
        super(IconButton, self).__init__(parent)
        self.icon = icon
        self.hover_icon = hover_icon
        self.disabled_icon = disabled_icon
        self.disabled = False
        self.setIcon(QIcon(icon))
        self.setStyleSheet("background-color: white; border: none;")
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

    def enterEvent(self, _):
        if self.hover_icon is not None and not self.disabled:
            self.setIcon(QIcon(self.hover_icon))

    def leaveEvent(self, _):
        if not self.disabled:
            self.setIcon(QIcon(self.icon))

    def setEnabled(self, enabled):
        self.disabled = not enabled
        if self.disabled:
            self.setIcon(QIcon(self.disabled_icon))
            self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        else:
            self.setIcon(QIcon(self.icon))
            self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
