from PySide6.QtCore import QObject, Signal, Slot
from pingmapper.dat_interpreter import DatInterpreter


class DatWorker(QObject):
    # Declaring Signals at the class level
    finished = Signal()
    log = Signal(str)
    merged_images_paths_signal = Signal(dict)

    def __init__(self) -> None:
        """Initialize the worker.
        """
        super().__init__()
        self.dat_interpreter = DatInterpreter()

    def set_dat_path(self, p: str) -> None:
        """Set the DAT file path for processing.

        Args:
            p (str): Path to the DAT file.
        """
        self.dat_interpreter.set_dat_path(p)

    def set_son_idx_subfolder_path(self, p: str) -> None:
        """Set the SON/IDX subfolder path for processing.

        Args:
            p (str): Path to the SON/IDX subfolder.
        """
        self.dat_interpreter.set_son_idx_subfolder_path(p)

    def set_project_path(self, p: str) -> None:
        """Set the project output path for processing.

        Args:
            p (str): Path to the project output directory.
        """
        self.dat_interpreter.set_project_path(p)

    @Slot()
    def run(self) -> None:
        """Run the waterfall generation pipeline and image manipulation."""
        self.log.emit("Processing waterfall images ...")
        result = self.dat_interpreter.generate_waterfall_images()
        self.log.emit(result)
        self.merged_images_paths_signal.emit(
            self.dat_interpreter.get_merged_images_paths())
        self.finished.emit()
