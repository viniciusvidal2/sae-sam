from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QTextEdit, QLabel
)
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt, QThread
import os
import open3d as o3d
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from modules.hypack_file_manipulator import HypackFileManipulator
from modules.ardupilot_log_reader import ArdupilotLogReader
from workers.mb2_opt_worker import Mb2OptWorker


class Mb2OptWindow(QMainWindow):
    ##############################################################################################
    # region window setup
    def __init__(self) -> None:
        """Initialize the main window for the Mb2 raw data optimization application.
        """
        super().__init__()
        self.setWindowTitle("MB2 Raw data optimization")
        self.setMinimumSize(1700, 600)
        # Setup background with proper image and style
        self.setup_background()

        # Main layout split into left and right panels
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel layout - data input btns, process btns and text panel
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.setup_input_data_section(left_layout)
        self.setup_processing_section(left_layout)

        # Right panel - Plot visualizer placeholder plus btns
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_right_panel(right_layout)

        # Fill the main layout with both panels
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        # Help the printing in the text panel
        self.skip_print = "------------------------------------------------"
        # Object to manipulate and process HSX files
        self.hypack_file_manipulator = HypackFileManipulator()
        self.hypack_file_manipulator.set_timezone_offset(-3)
        # Object to manipulate and process BIN files
        self.pixhawk_log_manipulator = ArdupilotLogReader()
        # Specific paths to the several files we must control
        self.hsx_path = None
        self.hsx_log_path = None
        self.raw_path = None
        self.raw_log_path = None
        self.bin_path = None
        self.project_root_path = None
        # Optimized data we get after calling the GPS process from pixhawk log
        self.optimized_hypack_points_data = None

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
        hsx_label = QLabel("Hypack HSX file:")
        self.hsx_text_edit = QLineEdit()
        self.hsx_text_edit.setPlaceholderText(
            "Path to the HSX file. Make sure RAW and LOG files are in the same project folder.")
        hsx_browse_btn = QPushButton("Browse")
        hsx_browse_btn.clicked.connect(self.hsx_browse_btn_callback)
        hsx_view_data_btn = QPushButton("View Data")
        hsx_btn_layout.addWidget(hsx_label)
        hsx_btn_layout.addWidget(self.hsx_text_edit)
        hsx_btn_layout.addWidget(hsx_browse_btn)
        hsx_btn_layout.addWidget(hsx_view_data_btn)
        # Pixhawk data from bin file
        bin_btn_layout = QHBoxLayout()
        bin_label = QLabel("Pixhawk log file in BIN format")
        self.bin_text_edit = QLineEdit()
        self.bin_text_edit.setPlaceholderText(
            "Path to the BIN file, where the Pixhawk data is stored.")
        bin_browse_btn = QPushButton("Browse")
        bin_browse_btn.clicked.connect(self.bin_browse_btn_callback)
        bin_view_data_btn = QPushButton("View Data")
        bin_btn_layout.addWidget(bin_label)
        bin_btn_layout.addWidget(self.bin_text_edit)
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
        self.optimize_gps_btn = QPushButton("Optimize GPS")
        self.optimize_gps_btn.setEnabled(True)
        self.optimize_gps_btn.clicked.connect(self.optimize_gps_btn_callback)
        self.split_line_mission_btn = QPushButton("Split Line with Mission")
        self.split_line_mission_btn.setEnabled(True)
        self.split_line_mission_btn.clicked.connect(
            self.split_line_mission_btn_callback)
        self.split_line_manual_btn = QPushButton("Split Line Manually")
        self.split_line_manual_btn.setEnabled(True)
        self.split_line_manual_btn.clicked.connect(
            self.split_line_manual_btn_callback)
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
        # left_layout.addStretch(1)
        left_layout.addLayout(self.process_btn_layout)
        left_layout.addWidget(self.text_panel, stretch=1)

    def setup_right_panel(self, right_layout: QVBoxLayout) -> None:
        """Set up the right panel with its elements.
        Args:
            right_layout (QVBoxLayout): The layout to add the elements to.
        """
        # Reset button
        self.reset_data_btn = QPushButton("Reset Data")
        self.reset_data_btn.setEnabled(True)
        self.reset_data_btn.clicked.connect(self.reset_btn_callback)
        # Canvas for plots with toolbar
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet(""" 
            QToolBar {
                background: white;
                spacing: 6px;
                padding: 4px;
            }
            QToolButton {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QToolButton:hover {
                background: #e0e0e0;
            }
        """)
        # Download button
        self.download_btn = QPushButton("Download optimized project files")
        self.download_btn.setEnabled(True)
        self.download_btn.clicked.connect(self.download_btn_callback)
        # Add it all to the right layout
        right_layout.addWidget(self.reset_data_btn)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        right_layout.addWidget(self.download_btn)

    def resizeEvent(self, event: None) -> None:
        """Resize the contents when the window is resized.
        """
        # Rescale background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)

# endregion
##############################################################################################
# region processing callbacks
    def hsx_browse_btn_callback(self) -> None:
        """Open a file dialog to select the HSX file.
        """
        hsx_file_path, _ = QFileDialog.getOpenFileName(
            self, "Select HSX file. Make sure RAW and LOG files are in the same project folder.", "", "HSX files (*.HSX)")
        if hsx_file_path:
            # Find the project root folder and proper raw file
            project_folder = os.path.dirname(hsx_file_path)
            self.log_output(f"Selected HSX file: {hsx_file_path}")
            self.log_output(f"Selected project folder: {project_folder}")
            self.hsx_text_edit.setText(hsx_file_path.split("/")[-1])
            raw_file_path = os.path.join(
                project_folder, hsx_file_path.split("/")[-1].replace(".HSX", ".RAW"))
            if os.path.exists(raw_file_path):
                self.log_output(f"Selected RAW file: {raw_file_path}")
            else:
                self.log_output(
                    "No valid RAW file found in the project folder.")
                return
            # Check for HSX and RAW log files
            files_in_folder = os.listdir(project_folder)
            hsx_log = ""
            raw_log = ""
            for f in files_in_folder:
                if f.endswith(".LOG") and f.startswith("HSX"):
                    hsx_log = os.path.join(project_folder, f)
                if f.endswith(".LOG") and f.startswith("RAW"):
                    raw_log = os.path.join(project_folder, f)
            if os.path.exists(raw_log) and os.path.exists(hsx_log):
                self.log_output(f"HSX log file: {hsx_log}")
                self.log_output(f"RAW log file: {raw_log}")
            else:
                self.log_output(
                    "No valid HSX or RAW log files found in the project folder.")
                return
            # Set the files to be processed
            self.project_root_path = project_folder
            self.hsx_path = hsx_file_path
            self.hsx_log_path = hsx_log
            self.raw_path = raw_file_path
            self.raw_log_path = raw_log
            self.log_output("HSX and RAW files set for processing.")
        else:
            self.log_output("No valid HSX file selected.")

    def bin_browse_btn_callback(self) -> None:
        """Open a file dialog to select the BIN file.
        """
        bin_file_path, _ = QFileDialog.getOpenFileName(
            self, "Select BIN file", "", "BIN files (*.bin)")
        if bin_file_path:
            self.log_output(f"Selected BIN file: {bin_file_path}")
            self.bin_path = bin_file_path
            self.bin_text_edit.setText(bin_file_path.split("/")[-1])
        else:
            self.log_output("No valid BIN file selected.")

    def optimize_gps_btn_callback(self) -> None:
        """Optimize the Hypack gps points with the ardupilot (pixhawk) ones
        """
        # Dict with the paths to the files
        input_paths = {
            "hsx_path": self.hsx_path,
            "hsx_log_path": self.hsx_log_path,
            "raw_path": self.raw_path,
            "raw_log_path": self.raw_log_path,
            "bin_path": self.bin_path,
            "project_path": self.project_root_path
        }
        # Start the parallel process
        self.log_output(self.skip_print)
        self.thread = QThread()
        self.worker = Mb2OptWorker(pixhawk_reader=self.pixhawk_log_manipulator,
                                   hypack_reader=self.hypack_file_manipulator, input_paths=input_paths)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_gps_opt)
        self.worker.log.connect(self.log_output)
        self.worker.optimized_hypack_data_signal.connect(
            self.optimized_hypack_points_data)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def split_line_mission_btn_callback(self) -> None:
        pass

    def split_line_manual_btn_callback(self) -> None:
        pass

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
