from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QFileDialog, QTextEdit
from PySide6.QtGui import QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt


class ApexWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apex Window")
        self.setGeometry(200, 200, 800, 600)
        
        self.setup_background()
        self.setup_labels()
        self.setup_buttons()
        self.setup_text_panel()

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
        self.load_button = QPushButton("Load Image", self)
        self.load_button.move(20, 10)
        self.load_button.resize(100, 10)
        self.load_button.clicked.connect(self.load_image)

        self.process_button = QPushButton("Process", self)
        self.process_button.move(20, 60)  # Positioned just below the Load button
        self.process_button.resize(100, 10)
        self.process_button.clicked.connect(self.run_process)

    def setup_text_panel(self):
        self.output_panel = QTextEdit(self)
        self.output_panel.setReadOnly(True)
        self.output_panel.setStyleSheet(
            "background-color: rgba(255, 255, 255, 200); font-family: monospace;"
        )
        self.output_panel.move(20, 110)
        self.update_output_panel_size()

    def resizeEvent(self, event):
        # Rescale background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)

        # Dynamically resize text panel
        self.update_output_panel_size()

        super().resizeEvent(event)

    def update_output_panel_size(self):
        margin = 20
        panel_top = 110
        panel_width = self.width() - 2 * margin
        panel_height = self.height() - panel_top - margin
        self.output_panel.resize(panel_width, panel_height)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            filename = file_path.split("/")[-1]
            self.image_label.setText(filename)
            self.log_output(f"Loaded image: {filename}")

    def run_process(self):
        self.log_output("Starting process...")
        # Simulate something
        self.log_output("Processing complete!")

    def log_output(self, message):
        self.output_panel.append(message)
