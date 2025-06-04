from PySide6.QtCore import QObject, Signal, Slot
from modules.saesc_pipeline import SaescPipeline


class SaescWorker(QObject):
    # Declaring Signals at the class level
    finished = Signal()
    log = Signal(str)
    set_merged_point_cloud = Signal(dict)

    def __init__(self, input_data: dict) -> None:
        """Initialize the worker with the pipeline and input data.
        Args:
            input_data (dict): A dictionary containing the paths, types, sea level reference and flags for preprocessing.
        """
        super().__init__()
        self.saesc_pipeline = SaescPipeline()
        self.cloud_paths = input_data["paths"]
        self.cloud_types = input_data["types"]
        self.sea_level_refs = input_data["sea_level_refs"]
        self.apply_preprocessing = input_data["preprocess_flags"]

    @Slot()
    def run(self) -> None:
        """Run the processing pipeline.
        """
        # Set input data and process
        self.saesc_pipeline.set_input_data(input_clouds_paths=self.cloud_paths,
                                           input_clouds_types=self.cloud_types,
                                           sea_level_refs=self.sea_level_refs,
                                           preprocess_flags=self.apply_preprocessing)
        # Run pipeline and get each stage feedback
        for stage_msg in self.saesc_pipeline.merge_clouds():
            status = stage_msg["status"]
            pct = 100.0 * stage_msg["pct"]
            if stage_msg["result"]:
                self.log.emit(f"{status} ({pct:.2f}%)")
            else:
                self.log.emit(f"Error: {status} ({pct:.2f}%)")
                return
        # Obtain merged cloud to display
        self.log.emit(
            "Processing finished. Setting cloud for visualization ...")
        ptcs = {"pyvista": self.saesc_pipeline.get_merged_cloud_pyvista(),
                "ply": self.saesc_pipeline.get_merged_cloud()}
        self.set_merged_point_cloud.emit(ptcs)
        self.finished.emit()
