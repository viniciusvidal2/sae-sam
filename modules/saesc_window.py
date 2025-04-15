from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QRadioButton, QFileDialog, QScrollArea,
    QButtonGroup, QTextEdit, QFrame
)
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt
from pyvistaqt import QtInteractor
import os

# region Point Cloud Entries


class PointCloudEntry(QWidget):
    def __init__(self):
        super().__init__()
        self.full_path = None
        layout = QHBoxLayout()

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        layout.addWidget(self.line_edit)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_btn)

        self.radio_drone = QRadioButton("Drone")
        self.radio_sonar = QRadioButton("Sonar")
        self.radio_drone.setChecked(True)
        radio_style = "color: black; background-color: rgba(100,100,100,150); padding: 4px; border-radius: 4px;"
        self.radio_drone.setStyleSheet(radio_style)
        self.radio_sonar.setStyleSheet(radio_style)

        group = QButtonGroup(self)
        group.addButton(self.radio_drone)
        group.addButton(self.radio_sonar)

        layout.addWidget(self.radio_drone)
        layout.addWidget(self.radio_sonar)

        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_entry)
        layout.addWidget(self.remove_btn)

        self.setLayout(layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Point Cloud", "", "Point Cloud Files (*.pcd *.ply *.xyz)")
        if file_path:
            self.full_path = file_path
            self.line_edit.setText(os.path.basename(file_path))

    def remove_entry(self):
        self.line_edit.clear()
        self.full_path = None
# endregion

# region Main Window


class SaescWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAESC - SAE Scene Creator")
        self.setMinimumSize(1000, 600)
        # Setup background with proper image and style
        self.setup_background()

        # Main layout split: left (fixed width) and right (visualizer)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel layout (vertical)
        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(450)
        left_layout = QVBoxLayout(self.left_panel)
        # Scroll area for entries
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_widget)
        left_layout.addWidget(self.scroll_area, stretch=3)

        # Add/Process buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Point Cloud")
        self.add_btn.clicked.connect(self.add_entry)
        btn_layout.addWidget(self.add_btn)
        self.process_btn = QPushButton("Start Processing")
        btn_layout.addWidget(self.process_btn)
        left_layout.addLayout(btn_layout)

        # Text panel (bottom of left column)
        self.text_panel = QTextEdit()
        self.text_panel.setPlaceholderText(
            "Logs, status, or descriptions here...")
        self.text_panel.setReadOnly(True)
        self.text_panel.setFixedHeight(120)
        left_layout.addWidget(self.text_panel, stretch=1)

        # Finish the left layout in the main layout
        main_layout.addWidget(self.left_panel)

        # Right panel (PyVista Visualizer placeholder)
        self.visualizer = QtInteractor(self)
        self.visualizer.set_background(color="gray")
        main_layout.addWidget(self.visualizer, stretch=1)
        self.visualizer.add_axes()
        self.visualizer.show_bounds(grid='front')

        # We will have a list of entries to manage point clouds that will be processed
        self.entries = []

        self.skip_print = "------------------------------------------------"

    def setup_background(self):
        self.background = QPixmap("resources/background.png")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def resizeEvent(self, event):
        # Rescale background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)

    def add_entry(self):
        entry = PointCloudEntry()
        self.scroll_layout.addWidget(entry)
        self.entries.append(entry)
# endregion


if __name__ == "__main__":
    app = QApplication([])
    window = SaescWindow()
    window.show()
    app.exec()
