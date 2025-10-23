import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QFileDialog,
    QTextEdit, QLineEdit, QHBoxLayout, QVBoxLayout, QSplitter
)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QResizeEvent
from PySide6.QtCore import Qt, QThread
from workers.apex_worker import ApexWorker
from modules.path_tool import get_file_placement_path
from modules.report_generator import ReportGenerator
from windows.editable_labels import EditableImageLabel


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

        # Left panel layout - data input btns, dat process and 
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.setup_left_panel(left_layout)

        # Middle panel - image label plus buttons
        self.middle_panel = QWidget()
        middle_layout = QVBoxLayout(self.middle_panel)
        self.setup_middle_panel(middle_layout)

        # Right panel - Plot visualizer placeholder plus btns
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_right_panel(right_layout)

        # Fill the splitter with both panels and add to main layout
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.middle_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([self.width() // 3, self.width() // 3, self.width() // 3])
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
        self.dat_path_line_edit = QLineEdit(self)
        self.dat_path_browse_btn = QPushButton("Browse", self)
        self.dat_path_browse_btn.clicked.connect(self.dat_path_browse_btn_callback)
        input_dat_layout.addWidget(self.dat_path_label)
        input_dat_layout.addWidget(self.dat_path_line_edit)
        input_dat_layout.addWidget(self.dat_path_browse_btn)
        # Process button
        self.dat_process_btn = QPushButton("Process DAT", self)
        self.dat_process_btn.clicked.connect(self.dat_process_btn_callback)
        # Text output panel
        self.output_panel = QTextEdit(self)
        self.output_panel.setReadOnly(True)
        self.output_panel.setPlaceholderText("Output log for the user...")
        # Setting styles
        label_style = "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;"
        self.dat_path_label.setStyleSheet(label_style)
        # Add widgets to the layout
        layout.addLayout(input_dat_layout)
        layout.addWidget(self.dat_process_btn)
        layout.addWidget(self.output_panel)

    def setup_middle_panel(self, layout: QVBoxLayout) -> None:
        """Setups the middle panel in the main window
        """
        pass

    def setup_right_panel(self, layout: QVBoxLayout) -> None:
        """Setups the right panel in the main window
        """
        pass

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
                idx_files = [f for f in os.listdir(folder_path) if f.endswith(".idx")]
                son_files = [f for f in os.listdir(folder_path) if f.endswith(".son")]
                self.log_output(f"Found {len(idx_files)} IDX files and {len(son_files)} SON files.")
                if len(idx_files) != len(son_files):
                    self.log_output("Warning: The number of IDX and SON files do not match, corrupted data!")
                else:
                    self.dat_son_idx_files_found = True
            else:
                self.log_output("No subfolder found with the same name of the DAT file. Missing SON/IDX files!")
        else:
            self.log_output("No valid DAT path was inserted.")
        self.enable_buttons()

    def dat_process_btn_callback(self) -> None:
        """Callback for the dat process btn
        """
        self.disable_buttons()
        self.log_output(self.skip_print)
        self.log_output("Starting process...")
        self.enable_buttons()

    def log_output(self, message: str) -> None:
        """Logs the output in the text panel

        Args:
            message (str): The message to be logged
        """
        self.output_panel.append(message)

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
    window = DatWindow()
    window.show()
    sys.exit(app.exec())

# endregion
