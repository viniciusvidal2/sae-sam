import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt
from pyvistaqt import QtInteractor
import pyvista as pv


class ApexWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apex image processing")
        self.setGeometry(100, 100, 800, 600)

        self.setup_background()

    def setup_background(self):
        background = QPixmap("resources/saesc1.png")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)
