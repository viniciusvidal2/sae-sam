import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QSplashScreen
from PySide6.QtGui import QPixmap, QPalette, QBrush, QFont
from PySide6.QtCore import Qt, QTimer
from pyvistaqt import QtInteractor
import pyvista as pv
from windows.apex_window import ApexWindow
from windows.saesc_window import SaescWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAE SAM")
        self.setGeometry(400, 400, 800, 600)

        self.setup_background()
        self.setup_buttons()
        # The windows we can open from the main interface
        self.child_windows = []

    def setup_background(self):
        self.background = QPixmap("resources/background.png")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def resizeEvent(self, event):
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)

    def init_3d_tab(self):
        layout = QVBoxLayout(self.tab_3d)

        # Create a pyvista Plotter embedded in a Qt widget
        self.plotter = QtInteractor(self.tab_3d)
        layout.addWidget(self.plotter.interactor)
        self.tab_3d.setLayout(layout)

        # Example: Load a mesh or point cloud and add it to the plotter
        try:
            # Example with a simple sphere
            mesh = pv.Sphere()
            self.plotter.add_mesh(mesh)
            self.plotter.reset_camera()

        except Exception as e:
            print(f"Error loading or displaying with PyVista: {e}")

    def setup_buttons(self):
        # Create three buttons
        self.button_appex = QPushButton("Apex image processing", self)
        self.button_appex.setGeometry(100, 100, 200, 40)
        self.button_appex.clicked.connect(self.open_apex_window)

        self.button2 = QPushButton("MB2 data optimization", self)
        self.button2.setGeometry(100, 160, 200, 40)
        self.button2.clicked.connect(self.open_window2)

        self.button3 = QPushButton("SAESC - Scene Creator", self)
        self.button3.setGeometry(100, 220, 200, 40)
        self.button3.clicked.connect(self.open_saesc_window)

    def open_apex_window(self):
        apex_window = ApexWindow()
        apex_window.setAttribute(Qt.WA_DeleteOnClose)
        self.child_windows.append(apex_window)
        apex_window.destroyed.connect(
            lambda: self.child_windows.remove(apex_window))
        apex_window.show()

    def open_window2(self):
        # Placeholder for second window
        pass

    def open_saesc_window(self):
        saesc_window = SaescWindow()
        saesc_window.setAttribute(Qt.WA_DeleteOnClose)
        self.child_windows.append(saesc_window)
        saesc_window.destroyed.connect(
            lambda: self.child_windows.remove(saesc_window))
        saesc_window.show()

    def closeEvent(self, event):
        for window in self.child_windows:
            if window is not None and window.isVisible():
                window.close()
        event.accept()
        
    def _remove_dead_child(self, ref):
        self.child_windows = [r for r in self.child_windows if r is not ref]


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
