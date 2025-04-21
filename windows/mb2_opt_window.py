from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QRadioButton, QFileDialog, QScrollArea,
    QButtonGroup, QTextEdit, QLabel
)
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt, QThread
from pyvistaqt import QtInteractor
import os
import open3d as o3d


##############################################################################################
# region Main Window
class Mb2OptWindow(QMainWindow):
    def __init__(self) -> None:
        """Initialize the main window for the Mb2 raw data optimization application.
        """
        super().__init__()
        self.setWindowTitle("MB2 Raw data optimization")
        self.setMinimumSize(1700, 600)
        # Setup background with proper image and style
        self.setup_background()

        # Main layout split: left (fixed width) and right (visualizer)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel layout - data input btns, process btns and text panel
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        # Input data
        self.setup_input_data_section(left_layout)
        # Processing and pannel
        self.setup_processing_section(left_layout)

        # Right panel - PyVista Visualizer placeholder plus btns
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.reset_data_btn = QPushButton("Reset Data")
        self.reset_data_btn.setEnabled(True)
        self.reset_data_btn.clicked.connect(self.reset_btn_callback)
        self.download_btn = QPushButton("Download optimized project files")
        self.download_btn.setEnabled(True)
        self.download_btn.clicked.connect(self.download_btn_callback)
        right_layout.addWidget(self.reset_data_btn)
        right_layout.addWidget(self.download_btn)

        # Fill the main layout with both panels
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        # Help the printing in the text panel
        self.skip_print = "------------------------------------------------"

    def setup_background(self) -> None:
        """Set up the background image for the main window.
        """
        self.background = QPixmap("resources/background.png")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def setup_input_data_section(self, left_layout: QVBoxLayout) -> None:
        """Set up the btns for HSX, RAW and BIN files.
        Args:
            left_layout (QVBoxLayout): The layout to add the btns to.
        """
        # Hypack project data from HSX and RAW files in the project folder
        hsx_btn_layout = QHBoxLayout()
        hsx_label = QLabel("Hypack project folder")
        hsx_text_edit = QLineEdit()
        hsx_text_edit.setPlaceholderText(
            "Path to the project folder, where HSX and RAW files are file.")
        hsx_browse_btn = QPushButton("Browse")
        hsx_browse_btn.clicked.connect(
            lambda: hsx_text_edit.setText(QFileDialog.getExistingDirectory(self, "Select Project Folder")))
        hsx_view_data_btn = QPushButton("View Data")
        hsx_btn_layout.addWidget(hsx_label)
        hsx_btn_layout.addWidget(hsx_text_edit)
        hsx_btn_layout.addWidget(hsx_browse_btn)
        hsx_btn_layout.addWidget(hsx_view_data_btn)
        # Pixhawk data from bin file
        bin_btn_layout = QHBoxLayout()
        bin_label = QLabel("Pixhawk log file in BIN format")
        bin_text_edit = QLineEdit()
        bin_text_edit.setPlaceholderText(
            "Path to the BIN file, where the Pixhawk data is stored.")
        bin_browse_btn = QPushButton("Browse")
        bin_browse_btn.clicked.connect(
            lambda: bin_text_edit.setText(QFileDialog.getOpenFileName(self, "Select BIN File")[0]))
        bin_view_data_btn = QPushButton("View Data")
        bin_btn_layout.addWidget(bin_label)
        bin_btn_layout.addWidget(bin_text_edit)
        bin_btn_layout.addWidget(bin_browse_btn)
        bin_btn_layout.addWidget(bin_view_data_btn)
        # Add the btns to the main layout
        left_layout.addLayout(hsx_btn_layout)
        left_layout.addLayout(bin_btn_layout)

    def setup_processing_section(self, left_layout: QVBoxLayout) -> None:
        """Set up the processing section with radio btns and a text panel.
        Args:
            left_layout (QVBoxLayout): The layout to add the btns to.
        """
        # Buttons with processing calls
        self.process_btn_layout = QHBoxLayout()
        self.process_btn_layout.setAlignment(Qt.AlignTop)
        self.process_btn_layout.setSpacing(10)
        self.process_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.process_btn_layout.addStretch(1)
        self.optimize_gps_btn = QPushButton("Optimize GPS")
        self.optimize_gps_btn.setEnabled(True)
        self.split_line_mission_btn = QPushButton("Split Line with Mission")
        self.split_line_mission_btn.setEnabled(True)
        self.split_line_manual_btn = QPushButton("Split Line Manually")
        self.split_line_manual_btn.setEnabled(True)
        self.split_line_pct_lide_edit = QLineEdit()
        self.split_line_pct_lide_edit.setPlaceholderText(
            "Percentage of the line to split (0 - 100)")
        # Add the btns to the layout
        self.process_btn_layout.addWidget(self.optimize_gps_btn)
        self.process_btn_layout.addWidget(self.split_line_mission_btn)
        self.process_btn_layout.addWidget(self.split_line_manual_btn)
        self.process_btn_layout.addWidget(self.split_line_pct_lide_edit)
        # Text panel for logs and status
        self.text_panel = QTextEdit()
        self.text_panel.setPlaceholderText(
            "Logs, status, or descriptions here...")
        self.text_panel.setReadOnly(True)
        # Add everything to the left layout
        left_layout.addStretch(1)
        left_layout.addLayout(self.process_btn_layout)
        left_layout.addWidget(self.text_panel, stretch=1)

    def resizeEvent(self, event: None) -> None:
        """Resize the contents when the window is resized.
        """
        # Rescale background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)

    def reset_btn_callback(self) -> None:
        """Reset the data and clear the visualizer.
        """
        self.log_output("Resetting data...")
        self.log_output("Merged point cloud data cleared.")

    def download_btn_callback(self) -> None:
        """Download the merged point cloud.
        """
        if self.merged_ptc_ply is None:
            self.log_output("No merged point cloud to download.")
            return
        # Open file dialog to save the merged point cloud
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged Point Cloud", "merged_point_cloud.ply", "Point Cloud Files (*.ply)")
        if file_path:
            o3d.io.write_point_cloud(file_path, self.merged_ptc_ply)
            self.log_output(f"Merged point cloud saved to: {file_path}")
        else:
            self.log_output("Download cancelled.")

    def log_output(self, msg: str) -> None:
        """Log output to the text panel.
        Args:
            msg (str): The message to log.
        """
        self.text_panel.append(msg)

# endregion


if __name__ == "__main__":
    app = QApplication([])
    window = Mb2OptWindow()
    window.show()
    app.exec()
