from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QFileDialog, QTextEdit, QLineEdit
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt, QObject, Signal
from apex_pipeline import ApexPipeline


class ApexWindow(QWidget):
    ##############################################################################################
    # region Constructor
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apex Window")
        self.setGeometry(300, 300, 1500, 900)

        self.setup_input_labels_boxes()
        self.setup_background()
        self.setup_buttons()
        self.setup_text_panel()
        self.setup_image_panel()

        # Images, original and processed one
        self.image_path = None
        self.image_original = None
        self.image_segmented = None

        # The Apex pipeline to call when running the process
        self.apex_pipeline = ApexPipeline(undistort_m_pixel_ratio=0.1)

    # endregion
    ##############################################################################################
    # region Setup UI
    def setup_background(self):
        self.background = QPixmap("resources/background.png")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def setup_input_labels_boxes(self):
        # Dimensions to use as basis
        height = 30
        width = 160
        base_x = 20
        base_y = 10
        margin = 10
        step = width + margin
        # Labels for the values
        self.grid_height_label = QLabel("Grid Height (meters):", self)
        self.grid_width_label = QLabel("Grid Width (meters):", self)
        self.column_width_label = QLabel("Column Width (meters):", self)
        label_style = "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;"
        for label in [self.grid_height_label, self.grid_width_label, self.column_width_label]:
            label.setStyleSheet(label_style)
            label.resize(width, height)
        # The line edits for the user to insert dimensions
        self.grid_height_input = QLineEdit(self)
        self.grid_width_input = QLineEdit(self)
        self.column_width_input = QLineEdit(self)
        self.grid_height_input.setText("40.0")
        self.grid_width_input.setText("15.618")
        self.column_width_input.setText("5.232")
        box_style = "background-color: white; padding: 4px;"
        for box in [self.grid_height_input, self.grid_width_input, self.column_width_input]:
            box.setStyleSheet(box_style)
            box.resize(width, height)
        # Place everything side by side
        self.grid_height_label.move(base_x, base_y)
        self.grid_height_input.move(self.grid_height_label.x() + step, base_y)
        self.grid_width_label.move(self.grid_height_input.x() + step, base_y)
        self.grid_width_input.move(self.grid_width_label.x() + step, base_y)
        self.column_width_label.move(self.grid_width_input.x() + step, base_y)
        self.column_width_input.move(self.column_width_label.x() + step, base_y)

    def setup_buttons(self):
        # Dimensions to use as basis
        base_x = 20
        margin_y = 20
        margin_x = 20
        base_y = self.grid_height_label.y() + self.grid_height_label.height() + margin_y
        button_height = 30
        button_width = 150
        step = button_width + margin_x
        # Setup the row of buttons
        self.load_button = QPushButton("Load Image", self)
        self.load_button.move(base_x, base_y)
        self.load_button.clicked.connect(self.load_image)
        self.process_button = QPushButton("Process", self)
        self.process_button.move(self.load_button.x() + step, base_y)
        self.process_button.clicked.connect(self.run_process)
        self.toggle_btn = QPushButton("Toggle Image", self)
        self.toggle_btn.move(self.process_button.x() + step, base_y)
        self.toggle_btn.clicked.connect(self.toggle_image)
        self.download_image_btn = QPushButton("Download Image", self)
        self.download_image_btn.move(self.toggle_btn.x() + step, base_y)
        self.download_image_btn.clicked.connect(self.download_image)
        self.download_report_btn = QPushButton("Download Report", self)
        self.download_report_btn.move(self.download_image_btn.x() + step, base_y)
        self.download_report_btn.clicked.connect(self.download_report)
        for button in [self.load_button, self.process_button, self.toggle_btn,
                        self.download_image_btn, self.download_report_btn]:
            button.resize(button_width, button_height)

    def setup_text_panel(self):
        self.output_panel = QTextEdit(self)
        self.output_panel.setReadOnly(True)
        self.output_panel.setStyleSheet(
            "background-color: rgba(255, 255, 255, 200); font-family: monospace;"
        )
        self.output_panel.move(20, self.load_button.y() + self.load_button.height() + 20)
        self.output_panel.resize(400, 500)

    def setup_image_panel(self):
        self.image_display = QLabel(self)
        self.image_display.setStyleSheet(
            "border: 1px solid white; background-color: rgba(0,0,0,50);")
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.resize(600, 500)
        self.image_display.move(
            self.output_panel.x() + self.output_panel.width() + 20,
            self.load_button.y() + self.load_button.height() + 20,
        )
        self.image_panel_state = "None"

    def resizeEvent(self, event):
        # Rescale background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)
        super().resizeEvent(event)

    # endregion
    ##############################################################################################
    # region Callbacks
    def load_image(self):
        self.image_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if self.image_path:
            filename = self.image_path.split("/")[-1]
            self.log_output(f"Loaded image: {filename}")
            self.image_original = QPixmap(self.image_path)
            self.display_image(self.image_original)
        else:
            self.log_output("No valid image path was inserted.")

    def run_process(self):
        # Check if the image is loaded
        self.log_output("Starting process...")
        if not self.image_original:
            self.log_output("No image loaded.")
            return
        self.log_output("Processing image...")
        # Set the dimensions of the barrier from the input boxes
        try:
            grid_height = float(self.grid_height_input.text())
            grid_width = float(self.grid_width_input.text())
            column_width = float(self.column_width_input.text())
        except ValueError:
            self.log_output("Invalid input for dimensions.")
            return
        barrier_dimensions = {"grid_width": grid_width, "grid_height": grid_height,
                              "collumn_width": column_width}
        self.apex_pipeline.set_barrier_dimensions(
            barrier_dimensions=barrier_dimensions)
        self.apex_pipeline.run(image_path=self.image_path)
        self.log_output("Image processed.")
        # Get the segmented image in 2d, plot it and set the image status
        self.image_segmented = QPixmap.fromImage(ImageQt(
            self.apex_pipeline.get_segmented_image()))
        self.display_image(self.image_segmented)
        self.image_panel_state = "segmented"
        self.log_output("Processing complete!")

    def log_output(self, message):
        self.output_panel.append(message)

    def toggle_image(self):
        if self.image_panel_state == "segmented" and self.image_original:
            self.display_image(self.image_original)
            self.log_output("Displaying original image.")
            self.image_panel_state = "original"
        elif self.image_panel_state == "original" and self.image_segmented:
            self.display_image(self.image_segmented)
            self.log_output("Displaying segmented image.")
            self.image_panel_state = "segmented"
        else:
            self.log_output("No image to toggle.")
            self.image_panel_state = "None"

    def display_image(self, image):
        scaled = image.scaled(
            self.image_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_display.setPixmap(scaled)

    def download_image(self):
        if not self.image_segmented:
            self.log_output("No image to download.")
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image As", "output.png", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
        )
        if save_path:
            self.image_segmented.save(save_path)
            self.log_output(f"Segmented image saved to {save_path}")

    def download_report(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report As", "report.txt", "Text Files (*.txt)"
        )
        if save_path:
            with open(save_path, "w") as f:
                f.write(self.output_panel.toPlainText())
            self.log_output(f"Report saved to {save_path}")

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
