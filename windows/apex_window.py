from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QFileDialog,
    QTextEdit, QLineEdit, QHBoxLayout, QVBoxLayout, QSplitter, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QResizeEvent
from PySide6.QtCore import Qt, QThread, QSize
from workers.apex_worker import ApexWorker
from modules.path_tool import get_file_placement_path
from modules.report_generator import ReportGenerator
from windows.editable_labels import EditableImageLabel


class ApexWindow(QMainWindow):
    ##############################################################################################
    # region Constructor
    def __init__(self) -> None:
        """Constructor for the main window
        """
        super().__init__()
        self.setWindowTitle("Apex Window")
        self.setWindowIcon(
            QPixmap(get_file_placement_path("resources/apex.png")))
        self.setGeometry(300, 300, 1500, 900)

        # Default values for the window control
        self.skip_print = "------------------------------------------------"
        # Images, original and processed one
        self.image_path = None
        self.image_original = None
        self.image_segmented = None
        # Output report generator
        self.output_metrics = None
        self.report_generator = ReportGenerator()

        # Setup the UI background
        self.setup_background()
        # Main layout split into left and right panels
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #888;
                width: 6px;
                margin: 1px;
            }
        """)

        # Left panel layout - data input btns, process btns and text panel
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.setup_input_data_section(left_layout)
        self.setup_processing_section(left_layout)

        # Right panel - Plot visualizer placeholder plus btns
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_right_panel(right_layout)

        # Fill the splitter with both panels and add to main layout
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([self.width() // 2, self.width() // 2])
        main_layout.addWidget(splitter)

    # endregion
    ##############################################################################################
    # region Setup UI
    def setup_input_data_section(self, layout: QVBoxLayout) -> None:
        """Setups the input data section in the left panel
        """
        # Layout for input texts and labels
        input_layout = QHBoxLayout()
        # Labels for the values
        self.grid_height_label = QLabel("Grid height [m]:", self)
        self.grid_width_label = QLabel("Grid width [m]:", self)
        self.column_width_label = QLabel("Column width [m]:", self)
        label_style = "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;"
        for label in [self.grid_height_label, self.grid_width_label, self.column_width_label]:
            label.setStyleSheet(label_style)
        # The line edits for the user to insert dimensions
        self.grid_height_input = QLineEdit(self)
        self.grid_width_input = QLineEdit(self)
        self.column_width_input = QLineEdit(self)
        self.grid_height_input.setText("30.0")
        self.grid_width_input.setText("15.618")
        self.column_width_input.setText("5.232")
        # Place everything side by side
        input_layout.addWidget(self.grid_height_label)
        input_layout.addWidget(self.grid_height_input)
        input_layout.addWidget(self.grid_width_label)
        input_layout.addWidget(self.grid_width_input)
        input_layout.addWidget(self.column_width_label)
        input_layout.addWidget(self.column_width_input)
        # Add the input layout to the parameter layout
        layout.addLayout(input_layout)

    def setup_processing_section(self, layout: QVBoxLayout) -> None:
        """Setups the processing section in the left panel
        """
        # Layout for processing buttons
        process_layout = QHBoxLayout()
        # Setup the row of buttons
        self.load_image_label = QLabel("Loaded Image:", self)
        self.load_image_label.setStyleSheet(
            "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;")
        self.load_image_text_box = QLineEdit(self)
        self.load_image_text_box.setReadOnly(True)
        self.load_image_text_box.setPlaceholderText("No image loaded")
        self.load_btn = QPushButton("Browse", self)
        self.load_btn.clicked.connect(self.load_image_btn_callback)
        self.process_btn = QPushButton("Process Image", self)
        self.process_btn.clicked.connect(self.process_btn_callback)
        # Add the widgets to the layout
        process_layout.addWidget(self.load_image_label)
        process_layout.addWidget(self.load_image_text_box)
        process_layout.addWidget(self.load_btn)
        process_layout.addWidget(self.process_btn)
        # Create and add the text box bellow the buttons
        self.output_panel = QTextEdit(self)
        self.output_panel.setReadOnly(True)
        self.output_panel.setPlaceholderText("Log output")
        # Add the process layout to the parameter layout
        layout.addLayout(process_layout)
        layout.addWidget(self.output_panel)

    def setup_right_panel(self, layout: QVBoxLayout) -> None:
        """Setups the right panel in the main window
        """
        # Toggle between the original and segmented image
        self.toggle_btn = QPushButton("Toggle Image", self)
        self.toggle_btn.clicked.connect(self.toggle_btn_callback)
        # Setting image display
        self.editable_image_label = EditableImageLabel(self)
        self.image_panel_state = "None"
        # Download buttons and layout
        download_layout = QHBoxLayout()
        self.download_image_btn = QPushButton("Download Image", self)
        self.download_image_btn.clicked.connect(
            self.download_image_btn_callback)
        self.download_report_btn = QPushButton("Download Report", self)
        self.download_report_btn.clicked.connect(
            self.download_report_btn_callback)
        download_layout.addWidget(self.download_image_btn)
        download_layout.addWidget(self.download_report_btn)
        # Add the widgets to the layout
        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.editable_image_label)
        layout.addLayout(download_layout)

    def setup_background(self) -> None:
        """Generates the background with proper image and scales
        """
        self.background = QPixmap(
            get_file_placement_path("resources/background.png"))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Resizes the window and all the elements in it when resize callback is called

        Args:
            event (QResizeEvent): The resize event.
        """
        # Rescale background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)
        # Call the base class method
        super().resizeEvent(event)

    def destroyEvent(self) -> None:
        """Handles the destruction of the window and cleans up resources
        """
        self.editable_image_label.text_labels.clear()
        super().destroyEvent()

    # endregion
    ##############################################################################################
    # region Callbacks
    def load_image_btn_callback(self) -> None:
        """Callback for the load image btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.image_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if self.image_path:
            filename = self.image_path.split("/")[-1]
            self.log_output(f"Loaded image: {filename}")
            self.load_image_text_box.setText(filename)
            self.image_original = QPixmap(self.image_path)
            self.image_panel_state = "original"
            self.editable_image_label.set_image(
                image=self.image_original, state=self.image_panel_state)
            # Remove any old segmented image
            self.image_segmented = None
        else:
            self.log_output("No valid image path was inserted.")
        self.enable_buttons()

    def process_btn_callback(self) -> None:
        """Callback for the process btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.log_output("Starting process...")
        if not self.image_original:
            self.log_output("No image loaded.")
            self.enable_buttons()
            return
        try:
            grid_height = float(self.grid_height_input.text())
            grid_width = float(self.grid_width_input.text())
            column_width = float(self.column_width_input.text())
        except ValueError:
            self.log_output("Invalid input for dimensions.")
            return
        barrier_dimensions = {
            "grid_width": grid_width,
            "grid_height": grid_height,
            "collumn_width": column_width
        }
        # Deal with parallelism in the worker thread to run the pipeline
        self.thread = QThread()
        self.worker = ApexWorker(self.image_path, barrier_dimensions)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.log_output)
        self.worker.set_segmented_image.connect(self._set_segmented_image)
        self.worker.set_metrics.connect(self._log_metrics)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.enable_buttons)
        self.thread.start()

    def _set_segmented_image(self, image: QPixmap) -> None:
        """Callback for the segmented image
        Args:
            image (QPixmap): The segmented image to be displayed
        """
        self.image_segmented = QPixmap.fromImage(image)
        if self.image_segmented.isNull():
            self.log_output("Failed to generate segmented image.")
            return
        self.log_output("Segmented image generated successfully.")
        self.image_panel_state = "segmented"
        self.editable_image_label.set_image(
            image=self.image_segmented, state=self.image_panel_state)

    def _log_metrics(self, metrics: tuple) -> None:
        """Logs the metrics from the pipeline

        Args:
            metrics (tuple): the metrics per detection and per class
        """
        self.log_output(self.skip_print)
        self.log_output(self.skip_print)
        if metrics:
            self.output_metrics = metrics
            metrics_per_detection = metrics[0]
            self.log_output("Metrics:")
            for i, metric in enumerate(metrics_per_detection):
                self.log_output(self.skip_print)
                self.log_output(
                    f" Detection {i}: class {metric['class']}, area: {metric['area']} m2, volume: {metric['volume']} m3")
        else:
            self.log_output("No metrics detected.")

    def log_output(self, message: str) -> None:
        """Logs the output in the text panel

        Args:
            message (str): The message to be logged
        """
        self.output_panel.append(message)

    def toggle_btn_callback(self) -> None:
        """Callback for the toggle image btn
        """
        self.log_output(self.skip_print)
        if self.image_panel_state == "segmented" and self.image_original:
            self.log_output("Displaying original image.")
            self.image_panel_state = "original"
            self.editable_image_label.set_image(
                image=self.image_original, state=self.image_panel_state)
        elif self.image_panel_state == "original" and self.image_segmented:
            self.log_output("Displaying segmented image.")
            self.image_panel_state = "segmented"
            self.editable_image_label.set_image(
                image=self.image_segmented, state=self.image_panel_state)
        else:
            self.log_output("No image to toggle.")
            self.image_panel_state = "None"

    def download_image_btn_callback(self) -> None:
        """Callback for the download image btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image As", "output.png", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
        )
        if save_path:
            painted_image = self.editable_image_label.get_painted_image(
                state=self.image_panel_state)
            painted_image.save(save_path)
            self.log_output(
                f"{self.image_panel_state} image saved to {save_path}")
        self.enable_buttons()

    def download_report_btn_callback(self) -> None:
        """Callback for the download report btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        if not self.output_metrics:
            self.log_output("No metrics to save.")
            self.enable_buttons()
            return
        # Get the save path for the report
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report As", "report.pdf", "PDF Files (*.pdf)"
        )
        self.report_generator.set_output_path(save_path)
        # Creating the report data on top of the output metrics
        report_data = {
            "image_name": self.image_path.split("/")[-1],
            "model_name": "distill_any_depth",
            "original_image": self.editable_image_label.get_painted_image(state="original"),
            "segmented_image": self.editable_image_label.get_painted_image(state="segmented"),
            "metrics": self.output_metrics
        }
        self.report_generator.set_data(report_data)
        # Generating the report
        report_message = self.report_generator.build_report()
        self.log_output(f"{report_message}")
        self.enable_buttons()

    def enable_buttons(self) -> None:
        """Enables the buttons in the window
        """
        self.load_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self.toggle_btn.setEnabled(True)
        self.download_image_btn.setEnabled(True)
        self.download_report_btn.setEnabled(True)

    def disable_buttons(self) -> None:
        """Disables the buttons in the window
        """
        self.load_btn.setEnabled(False)
        self.process_btn.setEnabled(False)
        self.toggle_btn.setEnabled(False)
        self.download_image_btn.setEnabled(False)
        self.download_report_btn.setEnabled(False)
    # endregion


##############################################################################################
# region Main
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ApexWindow()
    window.show()
    sys.exit(app.exec())

# endregion
