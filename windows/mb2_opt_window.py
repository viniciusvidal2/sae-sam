from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QTextEdit, QLabel, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt, QThread
import os
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
        # Optimized data we get after calling the GPS process from pixhawk log
        self.optimized_hypack_points_data = None
        # Split content for HSX and RAW files once we have the mission from the pixhawk logs
        self.data_split_content_with_mission = None
        # Canvas toolbar stylesheet
        self.toolbar_style = """
            QToolBar {
                    background: rgba(0,0,0,150);
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
        """
        
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
        # Layouts to split the input and view sections
        input_view_layout = QHBoxLayout()
        input_layout = QVBoxLayout()
        # Hypack project data from HSX and RAW files in the project folder
        hsx_btn_layout = QHBoxLayout()
        label_style = "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;"
        hsx_label = QLabel("Hypack file (HSX):")
        hsx_label.setStyleSheet(label_style)
        self.hsx_text_edit = QLineEdit()
        self.hsx_text_edit.setPlaceholderText(
            "Path to the HSX file. Make sure RAW and LOG files are in the same project folder.")
        hsx_browse_btn = QPushButton("Browse")
        hsx_browse_btn.clicked.connect(self.hsx_browse_btn_callback)
        hsx_btn_layout.addWidget(hsx_label)
        hsx_btn_layout.addWidget(self.hsx_text_edit)
        hsx_btn_layout.addWidget(hsx_browse_btn)
        # Pixhawk data from bin file
        bin_btn_layout = QHBoxLayout()
        bin_label = QLabel("Pixhawk log file (.bin):")
        bin_label.setStyleSheet(label_style)
        self.bin_text_edit = QLineEdit()
        self.bin_text_edit.setPlaceholderText(
            "Path to the BIN file, where the Pixhawk data is stored.")
        bin_browse_btn = QPushButton("Browse")
        bin_browse_btn.clicked.connect(self.bin_browse_btn_callback)
        bin_btn_layout.addWidget(bin_label)
        bin_btn_layout.addWidget(self.bin_text_edit)
        bin_btn_layout.addWidget(bin_browse_btn)
        # Add the input layouts to the horizontal layout
        input_layout.addLayout(hsx_btn_layout)
        input_layout.addLayout(bin_btn_layout)
        # Add the input plus the view button to the top layout
        view_data_btn = QPushButton("View Data")
        view_data_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        view_data_btn.clicked.connect(self.draw_data_callback)
        input_view_layout.addLayout(input_layout)
        input_view_layout.addWidget(view_data_btn)
        # Add it all to the main layout
        left_layout.addLayout(input_view_layout)

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
        self.toolbar.setStyleSheet(self.toolbar_style)
        # Optimized data download button
        self.download_opt_data_btn = QPushButton(
            "Download optimized project files")
        self.download_opt_data_btn.setEnabled(True)
        self.download_opt_data_btn.clicked.connect(
            self.download_optimized_data_callback)
        # Mission split data data download button
        self.download_mission_split_data_btn = QPushButton(
            "Download HSX and RAW files split from mission")
        self.download_mission_split_data_btn.setEnabled(True)
        self.download_mission_split_data_btn.clicked.connect(
            self.download_split_data_callback)
        # Add it all to the right layout
        right_layout.addWidget(self.reset_data_btn)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        right_layout.addWidget(self.download_opt_data_btn)
        right_layout.addWidget(self.download_mission_split_data_btn)

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
        self.log_output(self.skip_print)
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
        self.log_output(self.skip_print)
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
        self.log_output(self.skip_print)
        if not self.hsx_path or not self.bin_path:
            self.log_output("No HSX or BIN file selected to de drawn.")
            return
        # Dict with the paths to the files
        input_paths = {
            "hsx_path": self.hsx_path,
            "hsx_log_path": self.hsx_log_path,
            "raw_path": self.raw_path,
            "raw_log_path": self.raw_log_path,
            "bin_path": self.bin_path
        }
        # Start the parallel process
        self.thread = QThread()
        self.worker = Mb2OptWorker(pixhawk_reader=self.pixhawk_log_manipulator,
                                   hypack_reader=self.hypack_file_manipulator, input_paths=input_paths)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_gps_opt)
        self.worker.log.connect(self.log_output)
        self.worker.optimized_hypack_data_signal.connect(
            self._set_optimized_hsx_points_data)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _set_optimized_hsx_points_data(self, optimized_hypack_points_data: list) -> None:
        """Set the optimized HSX points data.
        Args:
            optimized_hypack_points_data (list): The optimized HSX points data.
        """
        self.optimized_hypack_points_data = optimized_hypack_points_data

    def split_line_mission_btn_callback(self) -> None:
        """Split the original HSX and RAW content according to the log waypoints
        """
        self.log_output(self.skip_print)
        if not self.hsx_path or not self.bin_path:
            self.log_output("No HSX or BIN file selected to de drawn.")
            return
        # Dict with the paths to the files
        input_paths = {
            "hsx_path": self.hsx_path,
            "hsx_log_path": self.hsx_log_path,
            "raw_path": self.raw_path,
            "raw_log_path": self.raw_log_path,
            "bin_path": self.bin_path
        }
        # Start the parallel process
        self.thread = QThread()
        self.worker = Mb2OptWorker(pixhawk_reader=self.pixhawk_log_manipulator,
                                   hypack_reader=self.hypack_file_manipulator, input_paths=input_paths)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_hsx_mission_split)
        self.worker.log.connect(self.log_output)
        self.worker.data_split_content_signal.connect(
            self._set_data_split_content)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _set_data_split_content(self, data_list: list) -> None:
        """Sets the mission split content once we use the mission from the ardupilot log

        Args:
            data_list (list): the split data list
        """
        self.data_split_content_with_mission = data_list

    def split_line_manual_btn_callback(self) -> None:
        pass

    def draw_data_callback(self) -> None:
        """Draw the HSX data in the visualizer.
        """
        self.log_output(self.skip_print)
        if not self.hsx_path or not self.bin_path:
            self.log_output("No HSX or BIN file selected to de drawn.")
            return
        # Dict with the paths to the files
        input_paths = {
            "hsx_path": self.hsx_path,
            "hsx_log_path": self.hsx_log_path,
            "raw_path": self.raw_path,
            "raw_log_path": self.raw_log_path,
            "bin_path": self.bin_path
        }
        # Start the parallel process
        self.thread = QThread()
        self.worker = Mb2OptWorker(pixhawk_reader=self.pixhawk_log_manipulator,
                                   hypack_reader=self.hypack_file_manipulator, input_paths=input_paths)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.create_map_data_figure)
        self.worker.log.connect(self.log_output)
        self.worker.map_canvas_signal.connect(
            self.draw_map_to_canvas)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def draw_map_to_canvas(self, fig: Figure) -> None:
        """Draw the content to the canvas in the GUI

        Args:
            fig (Figure): Figure with the map data from the mission in the log and the HSX file
        """
        # Create a new canvas
        new_canvas = FigureCanvas(fig)
        # Find the old canvas in the layout and replace it. Update the toolbar as well
        layout = self.right_panel.layout()
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, FigureCanvas):
                layout.removeWidget(widget)
                widget.setParent(None)
                layout.insertWidget(i, new_canvas)
                break
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, NavigationToolbar):
                layout.removeWidget(widget)
                widget.setParent(None)
                new_toolbar = NavigationToolbar(new_canvas, self)
                new_toolbar.setStyleSheet(self.toolbar_style)
                layout.insertWidget(i, new_toolbar)
                self.toolbar = new_toolbar
                break
        # Draw the new canvas
        self.canvas = new_canvas
        self.canvas.draw()

    def reset_btn_callback(self) -> None:
        """Reset the data and clear the visualizer.
        """
        self.log_output(self.skip_print)
        self.log_output("Resetting data...")
        self.log_output("Merged point cloud data cleared.")

    def download_optimized_data_callback(self) -> None:
        """Download the GPS optimized files.
        """
        self.log_output(self.skip_print)
        if self.optimized_hypack_points_data is None:
            self.log_output("No optimized HSX data to be saved.")
            return
        # Open file dialog to save the optimized files
        optimized_files_dir = QFileDialog.getExistingDirectory(
            self, "Select folder to save the optimized files", "", QFileDialog.ShowDirsOnly)
        if optimized_files_dir:
            optimized_file_name = os.path.basename(
                self.hsx_path).split(".")[0] + "_optimized"
            output_path = os.path.join(
                optimized_files_dir, optimized_file_name)
            self.hypack_file_manipulator.write_optimized_files(optimized_gps_data=self.optimized_hypack_points_data,
                                                               output_files_base_path=output_path)
            self.log_output(f"Optimized files saved to: {optimized_files_dir}")
        else:
            self.log_output("Optimized files download cancelled.")

    def download_split_data_callback(self):
        """Download the split HSX and RAW files.
        """
        self.log_output(self.skip_print)
        if self.data_split_content_with_mission is None:
            self.log_output("No split data to be saved.")
            return
        # Open file dialog to get the dir to save the split files
        split_files_dir = QFileDialog.getExistingDirectory(
            self, "Select folder to save the split files", "", QFileDialog.ShowDirsOnly)
        if split_files_dir:
            # Save every file content based on the split data content we got
            for data_section in self.data_split_content_with_mission:
                hsx_save_path = os.path.join(
                    split_files_dir, data_section["hsx_name"])
                raw_save_path = os.path.join(
                    split_files_dir, data_section["raw_name"])
                self.hypack_file_manipulator.write_file_and_log(
                    content=data_section["hsx_content"], file_path=hsx_save_path)
                self.hypack_file_manipulator.write_file_and_log(
                    content=data_section["raw_content"], file_path=raw_save_path)
                self.log_output(
                    f"Split HSX file saved to: {hsx_save_path}")
                self.log_output(
                    f"Split RAW file saved to: {raw_save_path}")
        else:
            self.log_output("Split files download cancelled.")
        self.log_output("Split HSX and RAW files saved.")

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
