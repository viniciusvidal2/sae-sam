import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QSplashScreen
from PySide6.QtGui import QPixmap, QPalette, QBrush, QFont
from PySide6.QtCore import Qt, QTimer
from pyvistaqt import QtInteractor
import pyvista as pv
from windows.apex_window import ApexWindow
from windows.saesc_window import SaescWindow
from windows.mb2_opt_window import Mb2OptWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        """Initialize the main window with a background image and buttons.
        The main window contains buttons to open different functionalities of the application.
        The buttons are connected to their respective functions which open new windows.
        """
        super().__init__()
        self.setWindowTitle("SAE SAM")
        self.setGeometry(400, 400, 800, 600)

        self.setup_background()
        self.setup_buttons()
        # The windows we can open from the main interface
        self.child_windows = []

    def setup_background(self) -> None:
        """Set up the background image for the main window.
        """
        self.background = QPixmap("resources/background.png")
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

    def setup_buttons(self) -> None:
        """Set up the buttons for the main window.
        """
        # Create one button for each isolated program module
        self.button_appex = QPushButton("Apex image processing", self)
        self.button_appex.setGeometry(100, 100, 200, 40)
        self.button_appex.clicked.connect(self.open_apex_window)

        self.button2 = QPushButton("MB2 data optimization", self)
        self.button2.setGeometry(100, 160, 200, 40)
        self.button2.clicked.connect(self.open_hypack_window)

        self.button_saesc = QPushButton("SAESC - Scene Creator", self)
        self.button_saesc.setGeometry(100, 220, 200, 40)
        self.button_saesc.clicked.connect(self.open_saesc_window)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # # Splash screen
    # original_pix = QPixmap("resources/saesam.png")
    # scaled_pix = original_pix.scaled(
    #     original_pix.width() // 4,
    #     original_pix.height() // 4,
    #     Qt.KeepAspectRatio,
    #     Qt.SmoothTransformation)
    # splash = QSplashScreen(scaled_pix)
    # splash.setFont(QFont("Arial", 20))
    # splash.show()

    # # Animate "Loading..." text
    # dots = ["", ".", "..", "..."]
    # current_index = [0]  # Using list to make it mutable in closure

    # def update_loading_text():
    #     splash.showMessage(f"Loading{dots[current_index[0]]}",
    #                        Qt.AlignCenter,
    #                        Qt.white)
    #     current_index[0] = (current_index[0] + 1) % len(dots)

    # timer = QTimer()
    # timer.timeout.connect(update_loading_text)
    # timer.start(1000)

    # After 6 seconds, close splash and open main window
    window = MainWindow()
    # QTimer.singleShot(6000, timer.stop)
    # QTimer.singleShot(6000, splash.close)
    # QTimer.singleShot(6000, window.show)
    window.show()
    sys.exit(app.exec())
