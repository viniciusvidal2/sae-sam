import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QFileDialog, QSlider,
    QTextEdit, QLineEdit, QHBoxLayout, QVBoxLayout, QSplitter, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QResizeEvent
from PySide6.QtCore import Qt, QThread
from modules.path_tool import get_file_placement_path
from windows.son_proc_label import SonProcLabel


class DatWindow(QMainWindow):
    ##############################################################################################
    # region Constructor
    def __init__(self) -> None:
        """Constructor for the main window
        """
        super().__init__()
        self.setWindowTitle("DAT Window")
        self.setWindowIcon(
            QPixmap(get_file_placement_path("resources/dat.png")))
        self.setGeometry(300, 300, 1500, 900)

        # Default values for the window control
        self.skip_print = "------------------------------------------------"
        self.dat_son_idx_files_found = False
        self.label_style = "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;"

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

        # Left panel layout - data input btns, dat process and output log
        # Filter applications btns
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.setup_left_panel(left_layout)

        # Right panel - Plot visualizer placeholder plus btns
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_right_panel(right_layout)

        # Fill the splitter with both panels and add to main layout
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes(
            [self.width() // 3, self.width() // 3, self.width() // 3])
        main_layout.addWidget(splitter)

# endregion
##############################################################################################
# region Setup UI
    def setup_left_panel(self, layout: QVBoxLayout) -> None:
        """Setups the left panel in the main window
        """
        # Input dat path layout
        input_dat_layout = QHBoxLayout()
        self.dat_path_label = QLabel("DAT File:", self)
        self.dat_path_label.setStyleSheet(self.label_style)
        self.dat_path_label.setFixedWidth(75)
        self.dat_path_line_edit = QLineEdit(self)
        self.dat_path_browse_btn = QPushButton("Browse", self)
        self.dat_path_browse_btn.clicked.connect(
            self.dat_path_browse_btn_callback)
        input_dat_layout.addWidget(self.dat_path_label)
        input_dat_layout.addWidget(self.dat_path_line_edit)
        input_dat_layout.addWidget(self.dat_path_browse_btn)
        # Project output path layout
        project_output_layout = QHBoxLayout()
        self.project_output_label = QLabel("Project path:", self)
        self.project_output_label.setStyleSheet(self.label_style)
        self.project_output_label.setFixedWidth(75)
        self.project_output_line_edit = QLineEdit(self)
        self.project_output_browse_btn = QPushButton("Browse", self)
        self.project_output_browse_btn.clicked.connect(
            self.project_output_browse_btn_callback)
        project_output_layout.addWidget(self.project_output_label)
        project_output_layout.addWidget(self.project_output_line_edit)
        project_output_layout.addWidget(self.project_output_browse_btn)
        # Process button
        self.dat_process_btn = QPushButton("Process DAT", self)
        self.dat_process_btn.clicked.connect(self.dat_process_btn_callback)
        # Text output panel
        self.output_panel = QTextEdit(self)
        self.output_panel.setReadOnly(True)
        self.output_panel.setPlaceholderText("Output log for the user...")
        # Contrast adjustment layout
        contrast_layout = QHBoxLayout()
        self.contrast_label = QLabel("Contrast:", self)
        self.contrast_label.setStyleSheet(self.label_style)
        self.contrast_label.setFixedWidth(75)
        self.contrast_slider = QSlider(Qt.Horizontal, self)
        self.contrast_slider.setRange(50, 300)
        self.contrast_slider.setValue(100)
        self.contrast_value_label = QLabel("1", self)
        self.contrast_value_label.setFixedWidth(25)
        self.contrast_slider.valueChanged.connect(
            lambda value: self.contrast_value_label.setText(str(value / 100)))
        self.contrast_apply_btn = QPushButton("Apply", self)
        self.contrast_apply_btn.clicked.connect(
            self.contrast_apply_btn_callback)
        contrast_layout.addWidget(self.contrast_label)
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_value_label)
        contrast_layout.addWidget(self.contrast_apply_btn)
        # Brightness adjustment layout
        brightness_layout = QHBoxLayout()
        self.brightness_label = QLabel("Brightness:", self)
        self.brightness_label.setStyleSheet(self.label_style)
        self.brightness_label.setFixedWidth(75)
        self.brightness_slider = QSlider(Qt.Horizontal, self)
        self.brightness_slider.setRange(-100.0, 100.0)
        self.brightness_slider.setValue(0.0)
        self.brightness_value_label = QLabel("0", self)
        self.brightness_value_label.setFixedWidth(25)
        self.brightness_slider.valueChanged.connect(
            lambda value: self.brightness_value_label.setText(str(value)))
        self.brightness_apply_btn = QPushButton("Apply", self)
        self.brightness_apply_btn.clicked.connect(
            self.brightness_apply_btn_callback)
        brightness_layout.addWidget(self.brightness_label)
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addWidget(self.brightness_value_label)
        brightness_layout.addWidget(self.brightness_apply_btn)
        # Gamma adjustment layout
        gamma_layout = QHBoxLayout()
        self.gamma_label = QLabel("Gamma:", self)
        self.gamma_label.setStyleSheet(self.label_style)
        self.gamma_label.setFixedWidth(75)
        self.gamma_slider = QSlider(Qt.Horizontal, self)
        self.gamma_slider.setRange(0, 300)
        self.gamma_slider.setValue(100)
        self.gamma_value_label = QLabel("1", self)
        self.gamma_value_label.setFixedWidth(25)
        self.gamma_slider.valueChanged.connect(
            lambda value: self.gamma_value_label.setText(str(value / 100)))
        self.gamma_apply_btn = QPushButton("Apply", self)
        self.gamma_apply_btn.clicked.connect(
            self.gamma_apply_btn_callback)
        gamma_layout.addWidget(self.gamma_label)
        gamma_layout.addWidget(self.gamma_slider)
        gamma_layout.addWidget(self.gamma_value_label)
        gamma_layout.addWidget(self.gamma_apply_btn)
        # Sharpness adjustment layout
        sharpness_layout = QHBoxLayout()
        self.sharpness_label = QLabel("Sharpness:", self)
        self.sharpness_label.setStyleSheet(self.label_style)
        self.sharpness_label.setFixedWidth(75)
        self.sharpness_slider = QSlider(Qt.Horizontal, self)
        self.sharpness_slider.setRange(0, 300)
        self.sharpness_slider.setValue(0)
        self.sharpness_value_label = QLabel("0", self)
        self.sharpness_value_label.setFixedWidth(25)
        self.sharpness_slider.valueChanged.connect(
            lambda value: self.sharpness_value_label.setText(str(value / 100)))
        self.sharpness_apply_btn = QPushButton("Apply", self)
        self.sharpness_apply_btn.clicked.connect(
            self.sharpness_apply_btn_callback)
        sharpness_layout.addWidget(self.sharpness_label)
        sharpness_layout.addWidget(self.sharpness_slider)
        sharpness_layout.addWidget(self.sharpness_value_label)
        sharpness_layout.addWidget(self.sharpness_apply_btn)
        # Saturation adjustment layout
        saturation_layout = QHBoxLayout()
        self.saturation_label = QLabel("Saturation:", self)
        self.saturation_label.setStyleSheet(self.label_style)
        self.saturation_label.setFixedWidth(75)
        self.saturation_slider = QSlider(Qt.Horizontal, self)
        self.saturation_slider.setRange(50, 200)
        self.saturation_slider.setValue(100)
        self.saturation_value_label = QLabel("1", self)
        self.saturation_value_label.setFixedWidth(25)
        self.saturation_slider.valueChanged.connect(
            lambda value: self.saturation_value_label.setText(str(value / 100)))
        self.saturation_apply_btn = QPushButton("Apply", self)
        self.saturation_apply_btn.clicked.connect(
            self.saturation_apply_btn_callback)
        saturation_layout.addWidget(self.saturation_label)
        saturation_layout.addWidget(self.saturation_slider)
        saturation_layout.addWidget(self.saturation_value_label)
        saturation_layout.addWidget(self.saturation_apply_btn)
        # clahe adjustment layout
        clahe_layout = QHBoxLayout()
        self.clahe_label = QLabel("CLAHE:", self)
        self.clahe_label.setStyleSheet(self.label_style)
        self.clahe_label.setFixedWidth(75)
        self.clahe_slider = QSlider(Qt.Horizontal, self)
        self.clahe_slider.setRange(100, 500)
        self.clahe_slider.setValue(200)
        self.clahe_value_label = QLabel("2", self)
        self.clahe_value_label.setFixedWidth(25)
        self.clahe_slider.valueChanged.connect(
            lambda value: self.clahe_value_label.setText(str(value / 100)))
        self.clahe_apply_btn = QPushButton("Apply", self)
        self.clahe_apply_btn.clicked.connect(
            self.clahe_apply_btn_callback)
        clahe_layout.addWidget(self.clahe_label)
        clahe_layout.addWidget(self.clahe_slider)
        clahe_layout.addWidget(self.clahe_value_label)
        clahe_layout.addWidget(self.clahe_apply_btn)
        # Detail enhancement layout
        detail_enhancement_layout = QHBoxLayout()
        self.detail_enhancement_label = QLabel("Detail:", self)
        self.detail_enhancement_label.setStyleSheet(self.label_style)
        self.detail_enhancement_label.setFixedWidth(75)
        self.detail_enhancement_slider = QSlider(Qt.Horizontal, self)
        self.detail_enhancement_slider.setRange(0, 100)
        self.detail_enhancement_slider.setValue(0)
        self.detail_enhancement_value_label = QLabel("0", self)
        self.detail_enhancement_value_label.setFixedWidth(25)
        self.detail_enhancement_slider.valueChanged.connect(
            lambda value: self.detail_enhancement_value_label.setText(str(value / 100)))
        self.detail_enhancement_apply_btn = QPushButton("Apply", self)
        self.detail_enhancement_apply_btn.clicked.connect(
            self.detail_enhancement_apply_btn_callback)
        detail_enhancement_layout.addWidget(self.detail_enhancement_label)
        detail_enhancement_layout.addWidget(self.detail_enhancement_slider)
        detail_enhancement_layout.addWidget(
            self.detail_enhancement_value_label)
        detail_enhancement_layout.addWidget(self.detail_enhancement_apply_btn)
        # Clear last filter and reset buttons
        reset_buttons_layout = QHBoxLayout()
        self.clear_last_filter_btn = QPushButton("Clear Last Filter", self)
        self.clear_last_filter_btn.clicked.connect(
            self.clear_last_filter_btn_callback)
        self.reset_filters_btn = QPushButton("Reset Filters to default values", self)
        self.reset_filters_btn.clicked.connect(self.reset_filters_btn_callback)
        reset_buttons_layout.addWidget(self.clear_last_filter_btn)
        reset_buttons_layout.addWidget(self.reset_filters_btn)
        # Add them all to the left layout
        layout.addLayout(input_dat_layout)
        layout.addLayout(project_output_layout)
        layout.addWidget(self.dat_process_btn)
        layout.addWidget(self.output_panel)
        layout.addLayout(contrast_layout)
        layout.addLayout(brightness_layout)
        layout.addLayout(gamma_layout)
        layout.addLayout(sharpness_layout)
        layout.addLayout(saturation_layout)
        layout.addLayout(clahe_layout)
        layout.addLayout(detail_enhancement_layout)
        layout.addLayout(reset_buttons_layout)

    def setup_right_panel(self, layout: QVBoxLayout) -> None:
        """Setups the right panel in the main window
        """
        # Image labels
        self.image_description_label = QLabel(
            "Extracted image processing:", self)
        self.image_description_label.setAlignment(Qt.AlignCenter)
        self.image_description_label.setStyleSheet(self.label_style)
        self.extracted_image_label = SonProcLabel()
        self.extracted_image_label.setStyleSheet(self.label_style)
        self.extracted_image_label.setAlignment(Qt.AlignCenter)
        self.extracted_image_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.extracted_image_label.setScaledContents(True)
        # Add the background image for starters
        placeholder_pixmap = QPixmap(
            get_file_placement_path("resources/dat.png"))
        self.extracted_image_label.set_pixmap(placeholder_pixmap)
        # Buttons
        btns_layout = QHBoxLayout()
        self.crop_btn = QPushButton("Enable Crop Tool", self)
        self.crop_btn.setToolTip(
            "Crop the image based on selection (ENTER to confirm, ESC to cancel)")
        self.crop_btn.setCheckable(True)
        self.crop_btn.setChecked(False)
        self.crop_btn.clicked.connect(self.crop_btn_callback)
        self.reset_image_btn = QPushButton("Reset Image", self)
        self.reset_image_btn.clicked.connect(self.reset_image_btn_callback)
        self.save_image_btn = QPushButton("Save Image", self)
        self.save_image_btn.clicked.connect(self.save_image_btn_callback)
        btns_layout.addWidget(self.crop_btn)
        btns_layout.addWidget(self.reset_image_btn)
        btns_layout.addWidget(self.save_image_btn)
        # Add widgets to the layout
        layout.addWidget(self.image_description_label)
        layout.addWidget(self.extracted_image_label)
        layout.addLayout(btns_layout)

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
    def dat_path_browse_btn_callback(self) -> None:
        """Callback for the browse button
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.dat_path, _ = QFileDialog.getOpenFileName(
            self, "Open DAT", "", "DAT Files (*.dat)"
        )
        if self.dat_path:
            # Set the path in the line edit
            filename = self.dat_path.split("/")[-1]
            self.log_output(f"Loaded DAT: {filename}")
            self.dat_path_line_edit.setText(filename)
            # Check if we have a folder with the same name
            folder_path = self.dat_path.replace(".dat", "")
            if os.path.isdir(folder_path):
                # The folder should have several .IDX and .SON files
                # Count them up and return
                idx_files = [f for f in os.listdir(
                    folder_path) if f.endswith(".idx")]
                son_files = [f for f in os.listdir(
                    folder_path) if f.endswith(".son")]
                self.log_output(
                    f"Found {len(idx_files)} IDX files and {len(son_files)} SON files.")
                if len(idx_files) != len(son_files):
                    self.log_output(
                        "Warning: The number of IDX and SON files do not match, corrupted data!")
                else:
                    self.dat_son_idx_files_found = True
            else:
                self.log_output(
                    "No subfolder found with the same name of the DAT file. Missing SON/IDX files!")
        else:
            self.log_output("No valid DAT path was inserted.")
        self.enable_buttons()

    def project_output_browse_btn_callback(self) -> None:
        """Callback for the project output browse button
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.project_output_path = QFileDialog.getExistingDirectory(
            self, "Select Project Output Directory", ""
        )
        if self.project_output_path:
            self.log_output(f"Selected project output path: {self.project_output_path}")
            self.project_output_line_edit.setText(self.project_output_path)
        else:
            self.log_output("No valid project output path was selected.")
        self.enable_buttons()

    def dat_process_btn_callback(self) -> None:
        """Callback for the dat process btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.log_output("Starting process...")
        self.enable_buttons()

    def crop_btn_callback(self, checked: bool) -> None:
        """Callback for the crop image btn
        """
        self.log_output(self.skip_print)
        """Enable or disable crop mode."""
        if checked:
            self.disable_buttons()
            self.crop_btn.setEnabled(True)
            self.log_output("Image cropping enabled.")
            self.extracted_image_label.enable_crop_mode(True)
            self.crop_btn.setText("Cancel Crop Tool")
            self.extracted_image_label.setFocus()
        else:
            self.enable_buttons()
            self.log_output("Image cropping disabled.")
            self.extracted_image_label.enable_crop_mode(False)
            self.crop_btn.setText("Enable Crop Tool")

    def reset_image_btn_callback(self) -> None:
        """Callback for the reset image btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.log_output("Reset image button clicked.")
        self.enable_buttons()

    def save_image_btn_callback(self) -> None:
        """Callback for the save image btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.log_output("Save image button clicked.")
        self.enable_buttons()

    def contrast_apply_btn_callback(self) -> None:
        """Callback for the contrast apply btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        contrast_value = self.contrast_slider.value()
        self.log_output(f"Applying contrast: {contrast_value}")
        self.enable_buttons()

    def brightness_apply_btn_callback(self) -> None:
        """Callback for the brightness apply btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        brightness_value = self.brightness_slider.value()
        self.log_output(f"Applying brightness: {brightness_value}")
        self.enable_buttons()

    def gamma_apply_btn_callback(self) -> None:
        """Callback for the gamma apply btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        gamma_value = self.gamma_slider.value()
        self.log_output(f"Applying gamma: {gamma_value}")
        self.enable_buttons()

    def sharpness_apply_btn_callback(self) -> None:
        """Callback for the sharpness apply btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        sharpness_value = self.sharpness_slider.value()
        self.log_output(f"Applying sharpness: {sharpness_value}")
        self.enable_buttons()

    def saturation_apply_btn_callback(self) -> None:
        """Callback for the saturation apply btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        saturation_value = self.saturation_slider.value()
        self.log_output(f"Applying saturation: {saturation_value}")
        self.enable_buttons()

    def clahe_apply_btn_callback(self) -> None:
        """Callback for the clahe apply btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        clahe_value = self.clahe_slider.value()
        self.log_output(f"Applying CLAHE: {clahe_value}")
        self.enable_buttons()

    def detail_enhancement_apply_btn_callback(self) -> None:
        """Callback for the detail enhancement apply btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        detail_enhancement_value = self.detail_enhancement_slider.value()
        self.log_output(
            f"Applying detail enhancement: {detail_enhancement_value}")
        self.enable_buttons()

    def clear_last_filter_btn_callback(self) -> None:
        """Callback for the clear last filter btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.log_output("Clearing last applied filter.")
        self.enable_buttons()

    def reset_filters_btn_callback(self) -> None:
        """Callback for the reset filters btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.log_output("Resetting all applied filters.")
        self.enable_buttons()


# endregion
##############################################################################################
# region Utility functions


    def log_output(self, message: str) -> None:
        """Logs the output in the text panel

        Args:
            message (str): The message to be logged
        """
        self.output_panel.append(message)

    def enable_buttons(self) -> None:
        """Enables the buttons in the window
        """
        self.dat_path_browse_btn.setEnabled(True)
        self.dat_process_btn.setEnabled(True)
        self.crop_btn.setEnabled(True)
        self.reset_image_btn.setEnabled(True)
        self.save_image_btn.setEnabled(True)

    def disable_buttons(self) -> None:
        """Disables the buttons in the window
        """
        self.dat_path_browse_btn.setEnabled(False)
        self.dat_process_btn.setEnabled(False)
        self.crop_btn.setEnabled(False)
        self.reset_image_btn.setEnabled(False)
        self.save_image_btn.setEnabled(False)

# endregion
##############################################################################################
# region Main


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = DatWindow()
    window.show()
    sys.exit(app.exec())

# endregion
