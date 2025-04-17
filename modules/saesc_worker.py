from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage
from PIL.ImageQt import ImageQt
from modules.saesc_pipeline import SaescPipeline


class SaescWorker(QObject):
    # Declaring Signals at the class level
    finished = Signal()
    log = Signal(str)
    set_segmented_image = Signal(QImage)
    set_metrics = Signal(list)

    def __init__(self, saesc_pipeline, image_path, barrier_dimensions):
        super().__init__()
        self.saesc_pipeline = saesc_pipeline
        self.image_path = image_path
        self.barrier_dimensions = barrier_dimensions

    @Slot()
    def run(self):
        self.log.emit("Setting up image and parameters...")
        self.saesc_pipeline.set_barrier_dimensions(
            barrier_dimensions=self.barrier_dimensions)
        self.log.emit("Loading image and processing pipeline...")
        for state in self.saesc_pipeline.run(self.image_path):
            self.log.emit(f"Progress: {state[0]}%, Status: {state[1]}")

        segmented = self.saesc_pipeline.get_segmented_image()
        if segmented:
            image_qt = ImageQt(segmented)
            qimage = QImage(image_qt)
            self.set_segmented_image.emit(qimage)
        self.log.emit("Processing complete!")

        metrics = self.saesc_pipeline.get_detections_metrics()
        self.set_metrics.emit(metrics or [])
        self.finished.emit()
