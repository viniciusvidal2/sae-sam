from sys import exit
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSplashScreen,
    QHBoxLayout, QVBoxLayout, QLabel, QWidget, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QFont, QGuiApplication
from PySide6.QtCore import Qt, QTimer
from windows.apex_window import ApexWindow
from windows.saesc_window import SaescWindow
from windows.mb2_opt_window import Mb2OptWindow
from modules.path_tool import get_file_placement_path


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        """Initialize the main window with a background image and buttons.
        The main window contains buttons to open different functionalities of the application.
        The buttons are connected to their respective functions which open new windows.
        """
        super().__init__()
        # The windows we can open from the main interface
        self.child_windows = []
        # Variables to control labels
        self.label_size = (300, 300)
        self.dat_label_path = get_file_placement_path("resources/dat.png")
        self.apex_label_path = get_file_placement_path("resources/apex.png")
        self.hypack_label_path = get_file_placement_path(
            "resources/mb2_opt.png")
        self.saesc_label_path = get_file_placement_path("resources/saesc.jpeg")

        # Title, icons, and position/sizes
        self.setWindowTitle("SAE SAM")
        self.setWindowIcon(
            QPixmap(get_file_placement_path("resources/saesam.png")))
        self.setFixedWidth(600)
        self.setFixedHeight(self.label_size[1])
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.frameGeometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)
        # Background
        self.setup_background()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        # Left panel with the buttons
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.setup_buttons(left_layout)
        # Right panel with the label
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_label_panel(right_layout)
        # Add the panels to the main layout
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

    def setup_background(self) -> None:
        """Set up the background image for the main window.
        """
        self.background = QPixmap(
            get_file_placement_path("resources/background.png"))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def resizeEvent(self, event: None) -> None:
        """Resize the contents when the window is resized.
        """
        # Resizing background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)

    def setup_buttons(self, layout: QVBoxLayout) -> None:
        """Set up the buttons for the main window.
        """
        # Create one button for each isolated program module
        self.button_dat = QPushButton("Apex DAT processing", self)
        self.button_dat.clicked.connect(self.open_dat_window)
        self.button_dat.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button_dat.enterEvent = lambda event: self.label_programs.setPixmap(
            QPixmap(self.dat_label_path).scaled(
                self.label_size[0], self.label_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.button_dat.setStyleSheet("""
            QPushButton {
                background-color: #f9f9f0;
                color: black;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #f0f0f9;
            }
            QPushButton:pressed {
                background-color: #f0f0f9;
            }
        """)
        self.button_appex = QPushButton("Apex image processing", self)
        self.button_appex.clicked.connect(self.open_apex_window)
        self.button_appex.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button_appex.enterEvent = lambda event: self.label_programs.setPixmap(
            QPixmap(self.apex_label_path).scaled(
                self.label_size[0], self.label_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.button_appex.setStyleSheet("""
            QPushButton {
                background-color: #a0a0a0;
                color: black;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #b0b0b0;
            }
            QPushButton:pressed {
                background-color: #8a8a8a;
            }
        """)
        self.button_hypack = QPushButton("MB2 data optimization", self)
        self.button_hypack.clicked.connect(self.open_hypack_window)
        self.button_hypack.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button_hypack.enterEvent = lambda event: self.label_programs.setPixmap(
            QPixmap(self.hypack_label_path).scaled(
                self.label_size[0], self.label_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.button_hypack.setStyleSheet("""
            QPushButton {
                background-color: #8fbf88;
                color: black;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #9fd998;
            }
            QPushButton:pressed {
                background-color: #7aad73;
            }
        """)
        self.button_saesc = QPushButton("SAESC - Scene Creator", self)
        self.button_saesc.clicked.connect(self.open_saesc_window)
        self.button_saesc.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button_saesc.enterEvent = lambda event: self.label_programs.setPixmap(
            QPixmap(self.saesc_label_path).scaled(
                self.label_size[0], self.label_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.button_saesc.setStyleSheet("""
            QPushButton {
                background-color: #7da8c3;
                color: black;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #8cb9d4;
            }
            QPushButton:pressed {
                background-color: #6992ae;
            }
        """)
        # Add them the layout
        layout.addWidget(self.button_dat)
        layout.addWidget(self.button_appex)
        layout.addWidget(self.button_hypack)
        layout.addWidget(self.button_saesc)

    def setup_label_panel(self, layout: QVBoxLayout) -> None:
        """Set up the label panel for the main window.
        """
        # Label that will contain an image with each program illustrative image
        self.label_programs = QLabel(self)
        self.label_programs.setStyleSheet(
            "border: 1px solid white; background-color: rgba(0,0,0,50);")
        self.label_programs.setAlignment(Qt.AlignCenter)
        # Add the label to the layout
        layout.addWidget(self.label_programs)

    def open_dat_window(self) -> None:
        """Open the Sonar DAT processing window.
        """
        # Create and add to the list of child windows
        # The child windows are stored in a list to be closed when the main window is closed
        pass

    def open_apex_window(self) -> None:
        """Open the Apex window.
        """
        # Create and add to the list of child windows
        # The child windows are stored in a list to be closed when the main window is closed
        apex_window = ApexWindow()
        self.child_windows.append(apex_window)
        apex_window.setAttribute(Qt.WA_DeleteOnClose)
        apex_window.destroyed.connect(
            lambda: self.child_windows.remove(apex_window))
        apex_window.show()

    def open_hypack_window(self) -> None:
        """Open the MB2 data optimization window.
        """
        # Create and add to the list of child windows
        # The child windows are stored in a list to be closed when the main window is closed
        mb2_window = Mb2OptWindow()
        self.child_windows.append(mb2_window)
        mb2_window.setAttribute(Qt.WA_DeleteOnClose)
        mb2_window.destroyed.connect(
            lambda: self.child_windows.remove(mb2_window))
        mb2_window.show()

    def open_saesc_window(self) -> None:
        """Open the SAESC window.
        """
        # Create and add to the list of child windows
        # The child windows are stored in a list to be closed when the main window is closed
        saesc_window = SaescWindow()
        self.child_windows.append(saesc_window)
        saesc_window.setAttribute(Qt.WA_DeleteOnClose)
        saesc_window.destroyed.connect(
            lambda: self.child_windows.remove(saesc_window))
        saesc_window.show()

    def closeEvent(self, event: None) -> None:
        """Close all child windows when the main window is closed.
        """
        for window in self.child_windows:
            if window is not None and window.isVisible():
                window.close()
        event.accept()


def main() -> None:
    """Main function to run the application.
    """
    app = QApplication()

    # Splash screen
    original_pix = QPixmap(get_file_placement_path("resources/saesam.png"))
    scaled_pix = original_pix.scaled(
        original_pix.width() // 3,
        original_pix.height() // 3,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation)
    splash = QSplashScreen(scaled_pix)
    splash.setFont(QFont("Arial", 20))
    splash.show()

    # Animate "Loading..." text
    dots = ["", ".", "..", "..."]
    current_index = [0]  # Using list to make it mutable in closure

    def update_loading_text():
        splash.showMessage(f"Loading{dots[current_index[0]]}",
                           Qt.AlignCenter,
                           Qt.white)
        current_index[0] = (current_index[0] + 1) % len(dots)
    timer = QTimer()
    timer.timeout.connect(update_loading_text)
    timer.start(1000)

    # After 6 seconds, close splash and open main window
    window = MainWindow()
    QTimer.singleShot(6000, timer.stop)
    QTimer.singleShot(6000, splash.close)
    QTimer.singleShot(6000, window.show)
    exit(app.exec())


if __name__ == '__main__':
    main()
