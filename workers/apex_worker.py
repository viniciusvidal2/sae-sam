from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage
from PIL.ImageQt import ImageQt
from modules.apex_pipeline import ApexPipeline
from modules.path_tool import get_file_placement_path


class ApexWorker(QObject):
    # Declaring Signals at the class level
    finished = Signal()
    log = Signal(str)
    set_segmented_image = Signal(QImage)
    set_metrics = Signal(list)

    def __init__(self, image_path: str, barrier_dimensions: dict) -> None:
        """Initialize the worker with the pipeline and image path.

        Args:
            image_path (str): The path to the image to be processed.
            barrier_dimensions (dict): The dimensions of the barriers in the image.
        """
        super().__init__()
        self.apex_pipeline = ApexPipeline(undistort_m_pixel_ratio=0.1)  # Initialize the pipeline with a pixel ratio
        self.image_path = image_path
        self.barrier_dimensions = barrier_dimensions

    @Slot()
    def run(self) -> None:
        """Run the image processing pipeline.
        This method emits logs and signals during the processing.
        """
        # Emitting log messages to indicate the progress of the pipeline
        self.log.emit("Setting up image and parameters...")
        self.apex_pipeline.set_barrier_dimensions(
            barrier_dimensions=self.barrier_dimensions)
        self.log.emit("Loading image and processing pipeline...")
        # Running the pipeline and emitting progress updates
        for state in self.apex_pipeline.run(self.image_path):
            self.log.emit(f"Progress: {state[0]}%, Status: {state[1]}")
        # Getting the segmented image and emitting it as a signal
        segmented = self.apex_pipeline.get_segmented_image()
        if segmented:
            image_qt = ImageQt(segmented)
            qimage = QImage(image_qt)
            self.set_segmented_image.emit(qimage)
        self.log.emit("Processing complete!")
        # Getting the detection metrics and emitting them as a signal
        metrics = self.apex_pipeline.get_detections_metrics()
        self.set_metrics.emit(metrics or [])
        self.finished.emit()
