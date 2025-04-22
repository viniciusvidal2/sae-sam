from PySide6.QtCore import QObject, Signal, Slot
from modules.ardupilot_log_reader import ArdupilotLogReader
from modules.hypack_file_manipulator import HypackFileManipulator


class Mb2OptWorker(QObject):
    # Declaring Signals at the class level
    finished = Signal()
    log = Signal(str)
    optimized_hypack_data_signal = Signal(list)

    def __init__(self, pixhawk_reader: ArdupilotLogReader, hypack_reader: HypackFileManipulator, input_paths: dict) -> None:
        """Initialize the worker with the proper class objects and input data.

        Args:
            pixhawk_reader (ArdupilotLogReader): Object to deal with the ardupilot log from bin file
            hypack_reader (HypackFileManipulator): object to deal with the hypack files 
            input_paths (dict): the paths to all the files to be processed
        """
        super().__init__()
        self.pixhawk_reader = pixhawk_reader
        self.hypack_reader = hypack_reader
        # The paths from the dict
        self.hsx_path = input_paths["hsx_path"]
        self.hsx_log_path = input_paths["hsx_log_path"]
        self.raw_path = input_paths["raw_path"]
        self.raw_log_path = input_paths["raw_log_path"]
        self.bin_path = input_paths["bin_path"]
        self.project_path = input_paths["project_path"]
        self.hypack_reader.set_hsx_file_path(self.hsx_path)
        self.hypack_reader.set_hsx_log_file_path(self.hsx_log_path)
        self.hypack_reader.set_raw_file_path(self.raw_path)
        self.hypack_reader.set_raw_log_file_path(self.raw_log_path)
        self.hypack_reader.set_project_folder_path(self.project_path)
        self.pixhawk_reader.set_log_file_path(self.bin_path)
        self.optimized_points_hypack = None
        
    def crop_data_from_time_range(self, initial_time: float, final_time: float, offset: float, gps_data: dict) -> list:
        """Crop the GPS data based on the given time range and offset.

        Args:
            initial_time (float): The start time for cropping.
            final_time (float): The end time for cropping.
            offset (float): The offset to be added to the initial and final times.
            gps_data (dict): The GPS data to be cropped.

        Returns:
            list: The cropped GPS data.
        """
        cropped_data = []
        for gps in gps_data:
            if gps['timestamp'] >= initial_time - offset and gps['timestamp'] <= final_time + offset:
                cropped_data.append(gps)
        return cropped_data

    @Slot()
    def run_gps_opt(self) -> None:
        """Run the file optimization process for GPS data.
        """
        self.log.emit("Starting GPS data optimization (0%)...")
        # Read the data from the files
        self.hypack_reader.read_coordinates()
        self.pixhawk_reader.read_data_from_log()
        self.log.emit("Data read from files (10%)...")
        # Get the points to be synchronized
        points_hypack = self.hypack_reader.get_utm_points_with_utc_timestamps()
        points_pixhawk = self.pixhawk_reader.get_utm_points_with_utc_timestamps()
        self.log.emit("Loaded GPS and points to optimize (30%)...")
        # Crop pixhawk points data to be in the same time interval as the hypack data
        initial_time = points_hypack[0]['timestamp']
        final_time = points_hypack[-1]['timestamp']
        points_pixhawk = self.crop_data_from_time_range(
            initial_time=initial_time, final_time=final_time, offset=2, gps_data=points_pixhawk)
        self.log.emit("Cropped GPS data to the same time interval (60%)...")
        # Optimize the GPS data for the HSX file
        self.log.emit("Starting HSX GPS data optimization (60%)...")
        self.optimized_points_hypack = self.hypack_reader.optimize_gps_data(
            reference_gps_points=points_pixhawk)
        self.log.emit("Optimized HSX GPS data (100%)...")
        self.optimized_hypack_data_signal.emit(self.optimized_points_hypack)
        # Obtain merged cloud to display
        self.log.emit("We are finished optimizing the HSX file GPS points.")
        self.finished.emit()
