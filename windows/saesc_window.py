from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QRadioButton, QFileDialog, QScrollArea,
    QButtonGroup, QTextEdit
)
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt, QThread
from pyvistaqt import QtInteractor
import os
import open3d as o3d
from modules.saesc_pipeline import SaescPipeline
from modules.saesc_worker import SaescWorker


##############################################################################################
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
            self, "Select Point Cloud", "", "Point Cloud Files (*.ply *.xyz)")
        if file_path:
            self.full_path = file_path
            self.line_edit.setText(os.path.basename(file_path))
            # If the extension is xyz we should mark the sonar radio button, ply for drone instead
            if file_path.endswith(".xyz"):
                self.radio_sonar.setChecked(True)
                self.radio_drone.setChecked(False)
            elif file_path.endswith(".ply"):
                self.radio_drone.setChecked(True)
                self.radio_sonar.setChecked(False)

    def remove_entry(self):
        self.line_edit.clear()
        self.full_path = None

 # endregion


##############################################################################################
# region Main Window
class SaescWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAESC - SAE Scene Creator")
        self.setMinimumSize(1500, 600)
        # Setup background with proper image and style
        self.setup_background()

        # Main layout split: left (fixed width) and right (visualizer)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel layout - scroll area, buttons and text panel
        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(550)
        left_layout = QVBoxLayout(self.left_panel)
        # Scroll area for entries
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_widget)
        # Add/Process buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Point Cloud")
        self.add_btn.clicked.connect(self.add_entry)
        btn_layout.addWidget(self.add_btn)
        self.process_btn = QPushButton("Start Processing")
        self.process_btn.clicked.connect(self.process_button_callback)
        btn_layout.addWidget(self.process_btn)
        # Text panel (bottom of left column)
        self.text_panel = QTextEdit()
        self.text_panel.setPlaceholderText(
            "Logs, status, or descriptions here...")
        self.text_panel.setReadOnly(True)
        self.text_panel.setFixedHeight(120)
        # Filling left panel
        left_layout.addWidget(self.scroll_area, stretch=3)
        left_layout.addLayout(btn_layout)
        left_layout.addWidget(self.text_panel, stretch=1)

        # Right panel - PyVista Visualizer placeholder plus buttons
        self.right_panel = QWidget()
        self.right_panel.setFixedWidth(900)
        right_layout = QVBoxLayout(self.right_panel)
        self.reset_data_button = QPushButton("Reset Data")
        self.reset_data_button.setEnabled(True)
        self.reset_data_button.clicked.connect(self.reset_button_callback)
        self.visualizer = QtInteractor(self)
        self.visualizer.set_background(color="gray")
        self.visualizer.add_axes()
        self.download_button = QPushButton("Download Merged Point Cloud")
        self.download_button.setEnabled(True)
        self.download_button.clicked.connect(self.download_button_callback)
        right_layout.addWidget(self.reset_data_button)
        right_layout.addWidget(self.visualizer.interactor, stretch=1)
        right_layout.addWidget(self.download_button)
        
        # Fill the main layout with both panels
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        # We will have a list of entries to manage point clouds that will be processed
        self.entries = []
        # Help the printing in the text panel
        self.skip_print = "------------------------------------------------"
        # The pipeline object to call the processing functions
        self.pipeline = SaescPipeline()
        # The generated merged point cloud to be downloaded
        self.merged_ptc_pyvista = None
        self.merged_ptc_ply = None

    def setup_background(self):
        self.background = QPixmap("resources/background.png")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def resizeEvent(self, event: None) -> None:
        """Resize the contents when the window is resized.
        """
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

    def process_button_callback(self):
        # Obtaining the input data from the entires and organizing to the worker thread
        input_paths = []
        input_types = []
        self.log_output(self.skip_print)
        self.log_output("Reading the input point clouds and its types...")
        for entry in self.entries:
            if entry.full_path:
                input_paths.append(entry.full_path)
                input_types.append(
                    "drone" if entry.radio_drone.isChecked() else "sonar")
            else:
                self.log_output("No file selected, nothing to process.")
                return
        input_data = {"paths": input_paths,
                      "types": input_types, "sea_level_ref": 71.3}

        # Create a worker to deal with the pipeline in a separate thread
        self.log_output("Processing started...")
        self.thread = QThread()
        self.worker = SaescWorker(self.pipeline, input_data)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.log_output)
        self.worker.set_merged_point_cloud.connect(
            self._set_merged_point_cloud)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        
    def reset_button_callback(self):
        """Reset the data and clear the visualizer.
        """
        self.log_output("Resetting data...")
        self.merged_ptc_pyvista = None
        self.merged_ptc_ply = None
        self.visualizer.clear()
        self.visualizer.add_axes()
        self.visualizer.update()
        self.log_output("Merged point cloud data cleared.")
        
    def download_button_callback(self):
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

    def _set_merged_point_cloud(self, ptcs: dict) -> None:
        """Set the merged point clouds for visualization and download.
        """
        self.merged_ptc_ply = ptcs["ply"]
        self.merged_ptc_pyvista = ptcs["pyvista"]
        self.visualizer.clear()
        self.visualizer.add_mesh(
            self.merged_ptc_pyvista, scalars=self.merged_ptc_pyvista.point_data["RGB"], rgb=True)
        self.visualizer.reset_camera()
        self.visualizer.enable_anti_aliasing()
        self.visualizer.update()
        
        self.log_output("Merged point cloud set for visualization.")

# endregion


if __name__ == "__main__":
    app = QApplication([])
    window = SaescWindow()
    window.show()
    app.exec()
