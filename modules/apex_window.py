from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QFileDialog, QTextEdit
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt


class ApexWindow(QWidget):
    ##############################################################################################
    # region Constructor
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apex Window")
        self.setGeometry(200, 200, 800, 600)

        self.setup_background()
        self.setup_labels()
        self.setup_buttons()
        self.setup_text_panel()
        self.setup_image_panel()

        # Images, original and processed one
        self.image_original = None
        self.image_segmented = None

    # endregion
    ##############################################################################################
    # region Setup UI
    def setup_background(self):
        self.background = QPixmap("resources/saesc1.png")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def setup_labels(self):
        self.image_label = QLabel("No image loaded", self)
        self.image_label.setStyleSheet(
            "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;"
        )
        self.image_label.move(140, 10)
        self.image_label.resize(200, 10)

    def setup_buttons(self):
        base_left_x = 20
        base_right_x = 680
        base_y = 10
        spacing = 50

        self.load_button = QPushButton("Load Image", self)
        self.load_button.move(base_left_x, base_y)
        self.load_button.resize(100, 10)
        self.load_button.clicked.connect(self.load_image)

        self.process_button = QPushButton("Process", self)
        self.process_button.move(base_left_x, base_y + spacing)
        self.process_button.resize(100, 10)
        self.process_button.clicked.connect(self.run_process)

        self.toggle_btn = QPushButton("Toggle Image", self)
        self.toggle_btn.move(base_right_x, base_y)
        self.toggle_btn.clicked.connect(self.toggle_image)

        self.download_image_btn = QPushButton("Download Image", self)
        self.download_image_btn.move(base_right_x, base_y + spacing)
        self.download_image_btn.clicked.connect(self.download_image)

        self.download_report_btn = QPushButton("Download Report", self)
        self.download_report_btn.move(base_right_x, base_y + 2 * spacing)
        self.download_report_btn.clicked.connect(self.download_report)

    def setup_text_panel(self):
        self.output_panel = QTextEdit(self)
        self.output_panel.setReadOnly(True)
        self.output_panel.setStyleSheet(
            "background-color: rgba(255, 255, 255, 200); font-family: monospace;"
        )
        self.output_panel.move(20, 110)
        self.output_panel.resize(400, 500)

    def setup_image_panel(self):
        self.image_display = QLabel(self)
        self.image_display.setStyleSheet(
            "border: 1px solid white; background-color: rgba(0,0,0,50);")
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setGeometry(440, 20, 460, 460)
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            filename = file_path.split("/")[-1]
            self.image_label.setText(filename)
            self.log_output(f"Loaded image: {filename}")
            self.image_original = QPixmap(file_path)
            self.display_image(self.image_original)

    def run_process(self):
        self.log_output("Starting process...")
        # Simulate something
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
