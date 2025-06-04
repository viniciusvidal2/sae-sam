from PySide6.QtCore import QObject, Signal, Slot
from modules.ardupilot_log_reader import ArdupilotLogReader
from modules.hypack_file_manipulator import HypackFileManipulator


class Mb2OptWorker(QObject):
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.figure import Figure
    # Declaring Signals at the class level
    slot_process_finished = Signal()
    log = Signal(str)
    optimized_hypack_data_signal = Signal(list)
    data_split_content_signal = Signal(list)
    map_canvas_signal = Signal(Figure)
    run_gps_opt_signal = Signal()
    run_hsx_split_signal = Signal()
    run_view_data_signal = Signal()

    def __init__(self) -> None:
        """Initialize the worker with the proper class objects and input data.
        """
        super().__init__()
        self.pixhawk_reader = ArdupilotLogReader()
        self.hypack_reader = HypackFileManipulator()
        self.hypack_reader.set_timezone_offset(-3)  # UTC-3 for Brazil
        # The optimized points from GPS optimization procedure
        self.optimized_points_hypack = None
        # The list of dicts with split content, when spliting the original file with the pixhawk log
        self.data_split_content = None
        # Connect the signals to the slots
        self.run_gps_opt_signal.connect(self.run_gps_opt)
        self.run_hsx_split_signal.connect(self.run_hsx_mission_split)
        self.run_view_data_signal.connect(self.create_map_data_figure)
        # The paths to the HSX and RAW files
        self.hsx_path = None
        self.raw_path = None
        self.hsx_log_path = None
        self.raw_log_path = None
        self.bin_path = None

    def set_project_paths(self, input_paths: dict) -> None:
        """Set the project paths for the HSX and RAW files.

        Args:
            input_paths (dict): The paths to the HSX and RAW files.
        """
        self.hsx_path = input_paths["hsx_path"]
        self.raw_path = input_paths["raw_path"]
        self.hsx_log_path = input_paths["hsx_log_path"]
        self.raw_log_path = input_paths["raw_log_path"]
        self.bin_path = input_paths["bin_path"]
        self.pixhawk_reader.set_log_file_path(self.bin_path)
        self.hypack_reader.set_project_paths(hsx_file_path=self.hsx_path,
                                             hsx_log_file_path=self.hsx_log_path,
                                             raw_file_path=self.raw_path,
                                             raw_log_file_path=self.raw_log_path)

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

    def reset_data(self) -> None:
        """Reset the data in the worker.
        """
        self.hypack_reader.reset_data()
        self.pixhawk_reader.reset_data()

    def write_hypack_optimized_files(self, optimized_gps_data: list, output_files_base_path: str) -> None:
        """Write the optimized GPS data to files.

        Args:
            optimized_gps_data (list): The optimized GPS data to be written to files.
            output_files_base_path (str): The base path for the output files.
        """
        self.hypack_reader.write_optimized_files(optimized_gps_data=optimized_gps_data,
                                                 output_files_base_path=output_files_base_path)

    def write_file_and_log(self, content: list, file_path: str) -> None:
        """Write the content to a file.

        Args:
            content (list): The content to be written to the file.
            file_path (str): The path of the file to be written.
        """
        self.hypack_reader.write_file_and_log(
            content=content, file_path=file_path)

    @Slot()
    def run_gps_opt(self) -> None:
        """Run the file optimization process for GPS data.
        """
        self.log.emit(
            "Starting GPS data optimization, reading the files (that can take a couple of minutes if first time) (0%)...")
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
        self.slot_process_finished.emit()

    @Slot()
    def run_hsx_mission_split(self) -> None:
        """Splits the original HSX file into multiple HSX files based on the mission in the pixhawk log.
        """
        self.log.emit(
            "Starting HSX mission split, reading the files (that can take a couple of minutes if first time) (0%)...")
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
        # Get the percentages of the initial and final points for each line
        ardupilot_pct_pairs_list = self.pixhawk_reader.get_data_percentages_from_mission_waypoints(
            log_gps_points=points_pixhawk)
        if not ardupilot_pct_pairs_list:
            self.log.emit(
                "No mission sychronized waypoints found in the log file (100%).")
            self.finished.emit()
            return
        self.log.emit("Obtained the percentage pairs for each line (80%)...")
        # Get each section content plus the proper name for the generated files
        self.data_split_content = []
        for i, pair in enumerate(ardupilot_pct_pairs_list):
            # Get the section of the HSX file to be selected
            initial_point_pct = pair[0]
            final_point_pct = pair[1]
            hsx_content, hsx_name = self.hypack_reader.get_file_section_content_and_name(
                initial_pct=initial_point_pct, final_pct=final_point_pct, original_path=self.hsx_path, name_index=i+1)
            raw_content, raw_name = self.hypack_reader.get_file_section_content_and_name(
                initial_pct=initial_point_pct, final_pct=final_point_pct, original_path=self.raw_path, name_index=i+1)
            # Save the content to the list
            self.data_split_content.append(
                {"hsx_content": hsx_content, "raw_content": raw_content, "hsx_name": hsx_name, "raw_name": raw_name})
            # Log the percentage
            log_pct = 80 + 18 / len(ardupilot_pct_pairs_list) * (i+1)
            self.log.emit(
                f"Splitting HSX and RAW files {i+1}/{len(ardupilot_pct_pairs_list)} ({log_pct:.2f}%)...")
        self.data_split_content_signal.emit(self.data_split_content)
        self.log.emit(
            f"Done spliting original content into {len(ardupilot_pct_pairs_list)} files (100%).")
        self.slot_process_finished.emit()

    @Slot()
    def create_map_data_figure(self) -> None:
        """Create the map data figure with GPS points from ardupilot log and HSX file.
        """
        import matplotlib
        matplotlib.use('Qt5Agg')
        from matplotlib.figure import Figure
        self.log.emit(
            "Generating synchronized UTM data for the map, reading the files (that can take a couple of minutes if first time) (0%)...")
        # Read the data from the files
        self.hypack_reader.read_coordinates()
        self.pixhawk_reader.read_data_from_log()
        self.log.emit("Data read from files (40%)...")
        # Get the points to be synchronized
        points_hypack = self.hypack_reader.get_utm_points_with_utc_timestamps()
        points_pixhawk = self.pixhawk_reader.get_utm_points_with_utc_timestamps()
        # Crop pixhawk points data to be in the same time interval as the hypack data
        initial_time = points_hypack[0]['timestamp']
        final_time = points_hypack[-1]['timestamp']
        points_pixhawk = self.crop_data_from_time_range(
            initial_time=initial_time, final_time=final_time, offset=2, gps_data=points_pixhawk)
        self.log.emit("Points synchronized (70%)...")
        fig = Figure(figsize=(5, 4))
        ax = fig.add_subplot(111)
        if len(points_hypack) > 0:
            ax.plot([gps['utm_east'] for gps in points_hypack],
                    [gps['utm_north']for gps in points_hypack], 'o-', color='blue', label='HSX')
        if len(points_pixhawk) > 0:
            ax.plot([gps['utm_east'] for gps in points_pixhawk],
                    [gps['utm_north']for gps in points_pixhawk], '*-', color='black', label='Pixhawk')
        ax.set_xlabel('UTM Easting')
        ax.set_ylabel('UTM Northing')
        ax.legend()
        ax.set_aspect('equal', adjustable='datalim')
        ax.set_title(
            f'GPS Data')
        self.map_canvas_signal.emit(fig)
        self.log.emit(
            "Map data generated. Canvas updated with the new map (100%).")
        self.slot_process_finished.emit()
