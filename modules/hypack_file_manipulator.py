from numpy import array
from os import path
from datetime import datetime, timedelta
from utm import to_latlon


class HypackFileManipulator:
    def __init__(self):
        """Constructor
        """
        self.input_hsx_file_path = ""
        self.input_raw_file_path = ""
        self.input_hsx_log_file_path = ""
        self.input_raw_log_file_path = ""
        # list of dictionaries containing utm_east, utm_north and timestamp
        self.gps_coordinates = []

# region Setters

    def set_hsx_file_path(self, file_path: str) -> None:
        """Set the path to the HSX file

        Args:
            file_path (str): the HSX path
        """
        self.input_hsx_file_path = file_path

    def set_raw_file_path(self, file_path: str) -> None:
        """Set the path to the RAW file

        Args:
            file_path (str): the RAW path
        """
        self.input_raw_file_path = file_path

    def set_hsx_log_file_path(self, file_path: str) -> None:
        """Set the path to the HSX log file

        Args:
            file_path (str): the HSX log path
        """
        self.input_hsx_log_file_path = file_path

    def set_raw_log_file_path(self, file_path: str) -> None:
        """Set the path to the RAW log file

        Args:
            file_path (str): the RAW log path
        """
        self.input_raw_log_file_path = file_path

    def set_timezone_offset(self, offset: int) -> None:
        """Set the timezone offset in hours

        Args:
            offset (int): Timezone offset in hours
        """
        self.time_zone_offset_hours = offset
# endregion
# region FileReading

    def read_coordinates(self) -> None:
        """Read the coordinates from the HSX file in UTM, with the timestamp
        """
        if self.input_hsx_file_path == '':
            print('No file path set')
            return
        # If a mission is loaded, do not read again
        if len(self.gps_coordinates) > 0:
            return
        # Fill the gps_coordinates list with the UTM coordinates and the timestamp
        with open(self.input_hsx_file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line_split = line.split()
                if line_split[0] == 'POS' and len(line_split) >= 4:
                    gps_point = {
                        'utm_east': float(line.split()[3]),
                        'utm_north': float(line.split()[4]),
                        'timestamp': float(line.split()[2])
                    }
                    self.gps_coordinates.append(gps_point)
            f.close()

    def reset_data(self) -> None:
        """Reset the data from the HSX file
        """
        self.gps_coordinates = []

    def get_date_from_file(self, file_path: str) -> str:
        """Gets the date in the file header

        Args:
            file_path (str): the file path

        Returns:
            str: the date in the file header
        """
        date = ''
        if not path.exists(file_path):
            return date
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line_split = line.split()
                if line_split[0] == 'TND':
                    date = line_split[2]
                    break
        f.close()
        return date

    def get_data_file_section_content(self, initial_point_index: int, final_point_index: int, file_path: str) -> list:
        """Get the content of the file from the initial to the final point

        Args:
            initial_point_index (int): the index of the initial point
            final_point_index (int): the index of the final point
            file_path (str): the file path.

        Returns:
            list: the content of the file from the initial to the final point
        """
        initial_timestamp = self.gps_coordinates[initial_point_index]['timestamp']
        final_timestamp = self.gps_coordinates[final_point_index]['timestamp']
        base_timestamp = self.gps_coordinates[0]['timestamp']
        with open(file_path, 'r') as f:
            lines = f.readlines()
            output_lines = []
            header_section = True
            data_section = False
            for line in lines:
                line_split = line.split()
                if header_section:
                    output_lines.append(line)
                    if line_split[0] == 'EOH':
                        header_section = False
                    continue
                elif not data_section:
                    if len(line_split) < 3:
                        continue
                    timestamp_candidate = line_split[2]
                    # Check if the candidate is a string
                    if not timestamp_candidate.replace('.', '', 1).isdigit():
                        continue
                    if float(timestamp_candidate) == initial_timestamp:
                        data_section = True
                        output_lines.append(line)
                else:
                    if len(line_split) < 3:
                        output_lines.append(line)
                        continue
                    timestamp_candidate = line_split[2]
                    # Check if the candidate is a string, and if it is, add the line to the output
                    if not timestamp_candidate.replace('.', '', 1).isdigit():
                        output_lines.append(line)
                        continue
                    # If any number is found, it should be lower than the max timestamp diff
                    timestamp_candidate = float(timestamp_candidate)
                    if timestamp_candidate > final_timestamp:
                        break
                    if timestamp_candidate > initial_timestamp or timestamp_candidate < base_timestamp:
                        output_lines.append(line)
        f.close()
        return output_lines
# endregion
# region FileSelectionAndGeneration

    def get_file_section_content_and_name(self, initial_pct: float, final_pct: float, original_path: str, name_index: int) -> tuple:
        """Returns the contents for the file with the name to save them later

        Args:
            initial_pct (float): Initial file percentage
            final_pct (float): Final file percentage
            original_path (str): Original file path
            name_index (int): Index of the file to generate the name for

        Returns:
            tuple: The content and the name for the split file
        """
        # Create the name for the file based on the original name and the desired index
        file_name = path.basename(original_path)
        file_name_split = file_name.split('.')
        selected_file_name = file_name_split[0] + "_" + \
            f"{name_index}".zfill(3) + "." + file_name_split[1]

        # Get the section indices
        initial_point_index = int(
            len(self.gps_coordinates) * initial_pct) - 1
        final_point_index = int(
            len(self.gps_coordinates) * final_pct) - 1
        # Warp the indices to the limits
        initial_point_index = max(0, initial_point_index)
        final_point_index = min(
            len(self.gps_coordinates) - 1, final_point_index)
        # Init value cannot be bigger or equal than the final value
        if initial_point_index >= final_point_index:
            return None, None

        # Get the content itself and return
        selected_content = self.get_data_file_section_content(
            initial_point_index=initial_point_index, final_point_index=final_point_index, file_path=original_path)
        return selected_content, selected_file_name

    def write_file_and_log(self, content: list, file_path: str) -> bool:
        """Writes the file and appends it to the log

        Args:
            content (list): The lines of the content to be written
            file_path (str): the output file path

        Returns:
            bool: True if the content was properly written
        """
        try:
            # Write the file content
            with open(file_path, 'w') as f:
                for line in content:
                    f.write(line)
            f.close()
            # Get the log file name from the file path
            file_name = path.basename(file_path)
            log_file_dir = path.dirname(file_path)
            log_file_name = file_name.split(
                ".")[-1] + "_files.LOG"
            self.add_file_to_log(file_path=file_path,
                                 log_file_path=path.join(log_file_dir, log_file_name))
            return True
        except Exception as e:
            print(f'Error writing file {file_path}: {e}')
            return False

    def add_file_to_log(self, file_path: str, log_file_path: str) -> None:
        """Append the selected file to the log, if necessary

        Args:
            file_path (str): the new file path
            log_file_path (str): the original log path
        """
        file_name = path.basename(file_path)
        # If the log file does not exist, just create it and write the name
        if not path.exists(log_file_path):
            with open(log_file_path, 'w') as f:
                f.write(file_name + '\n')
            f.close()
            return
        # Check if the file is already in the log
        files_present_in_log = []
        with open(log_file_path, 'r') as f:
            files_present_in_log = f.readlines()
        f.close()
        if file_name+"\n" in files_present_in_log:
            return
        # Write the file name to the log
        with open(log_file_path, 'a') as f:
            f.write(file_name + '\n')
        f.close()

# endregion
# region FileGPSOptimization

    def calculate_utc_timestamp(self) -> datetime:
        """Calculate the UTC timestamp from the original file date

        Returns:
            datetime: the UTC timestamp
        """
        hsx_date = self.get_date_from_file(self.input_hsx_file_path)
        # Convert the hsx date to UTC seconds timestamp considering the time zone offset
        hsx_date_split = hsx_date.split('/')
        hsx_datetime_timezone = datetime(year=int(hsx_date_split[2]), month=int(hsx_date_split[0]), day=int(hsx_date_split[1]),
                                         hour=0, minute=0, second=0)
        return hsx_datetime_timezone - timedelta(hours=self.time_zone_offset_hours)

    def get_utm_points_with_utc_timestamps(self) -> list:
        """Get the UTM points with the UTC timestamps

        Returns:
            list: the UTM points with the UTC timestamps
        """
        hsx_time_utc = self.calculate_utc_timestamp()
        return [{'utm_east': gps['utm_east'], 'utm_north': gps['utm_north'],
                 'timestamp': (hsx_time_utc + timedelta(seconds=gps["timestamp"])).timestamp()}
                for gps in self.gps_coordinates]

    def optimize_gps_data(self, reference_gps_points: list) -> list:
        """Optimize the GPS data based on the reference GPS points and write to the output files

        Args:
            reference_gps_points (list): the reference GPS points

        Returns:
            list: the optimized GPS data
        """
        # Creating the optimized gps data based on timestamps interpolation between the reference gps points and the
        # hypack gps points, considering the timestamps of the hypack gps points
        hsx_time_utc = self.calculate_utc_timestamp()
        optimized_gps_data = []
        for hypack_point in self.gps_coordinates:
            original_hypack_time = hypack_point["timestamp"]
            hypack_time = (
                hsx_time_utc + timedelta(seconds=original_hypack_time)).timestamp()
            previous_ref_point = None
            next_ref_point = None
            for i, ref_point in enumerate(reference_gps_points):
                if i == len(reference_gps_points) - 1:
                    continue
                ref_time = ref_point['timestamp']
                if ref_time == hypack_time:
                    optimized_gps_data.append(ref_point)
                    break
                elif hypack_time > ref_time:
                    previous_ref_point = ref_point
                elif hypack_time < ref_time and previous_ref_point is not None:
                    next_ref_point = ref_point
                    break
            if previous_ref_point is not None and next_ref_point is not None:
                previous_time = previous_ref_point['timestamp']
                previous_utm = array(
                    [previous_ref_point['utm_east'], previous_ref_point['utm_north'], previous_ref_point['altitude']])
                next_time = next_ref_point['timestamp']
                next_utm = array(
                    [next_ref_point['utm_east'], next_ref_point['utm_north'], next_ref_point['altitude']])

                diff_time_hypack = abs(hypack_time - previous_time)
                diff_time_ref = abs(next_time - previous_time)

                scaled_point_utm = previous_utm + \
                    (next_utm - previous_utm) * \
                    (diff_time_hypack / diff_time_ref)
                optimized_gps_data.append(
                    {'utm_east': scaled_point_utm[0], 'utm_north': scaled_point_utm[1], 'altitude': scaled_point_utm[2], 'timestamp': original_hypack_time})
        return optimized_gps_data

    def write_optimized_files(self, optimized_gps_data: list, output_files_base_path: str) -> bool:
        """Write the optimized files

        Args:
            optimized_gps_data (list): the optimized GPS data
            output_files_base_path (str): the output file names to base on

        Returns:
            bool: if the operation was successful
        """
        # Write the optimized data to new files in the desired directory
        output_hsx_file_path = output_files_base_path + ".HSX"
        output_raw_file_path = output_files_base_path + ".RAW"
        wrote_hsx = self.write_optimized_file(
            optimized_gps_data=optimized_gps_data, input_file_path=self.input_hsx_file_path, output_file_path=output_hsx_file_path)
        wrote_raw = self.write_optimized_file(
            optimized_gps_data=optimized_gps_data, input_file_path=self.input_raw_file_path, output_file_path=output_raw_file_path)
        # Append the new files to the log files in the output directory, if any
        output_hsx_log_file_path = path.join(path.dirname(
            output_files_base_path), "HSX_files.LOG")
        output_raw_log_file_path = path.join(path.dirname(
            output_files_base_path), "RAW_files.LOG")
        self.add_file_to_log(file_path=output_hsx_file_path,
                             log_file_path=output_hsx_log_file_path)
        self.add_file_to_log(file_path=output_raw_file_path,
                             log_file_path=output_raw_log_file_path)
        return wrote_hsx and wrote_raw

    def write_optimized_file(self, optimized_gps_data: list, input_file_path: str, output_file_path: str) -> bool:
        """Write the optimized file

        Args:
            optimized_gps_data (list): the optimized GPS data
            input_file_path (str): the input file path
            output_file_path (str): the output file path

        Returns:
            bool: if the operation was successful
        """
        # Read the file and alter the lines that contain GPS information
        with open(input_file_path, 'r') as f:
            lines = f.readlines()
            zone_number = 23
            # Get the zone we are at
            for i, line in enumerate(lines):
                line_split = line.split()
                if line_split[0] == "INI" and len(line_split) >= 3 and line_split[1] == "ZoneName=Zone":
                    zone_number = int(line_split[-1].split('(')[0])
                    break
            # Substitute the GPS data with the optimized data by searching the timestamp
            for i, line in enumerate(lines):
                line_split = line.split()
                if line_split[0] == "POS" or line_split[0] == "RAW":
                    timestamp = float(line_split[2])
                    new_line = ''
                    for new_data in optimized_gps_data:
                        if abs(new_data['timestamp'] - timestamp) < 0.1:
                            utm_east = new_data['utm_east']
                            utm_north = new_data['utm_north']
                            alt = new_data['altitude']
                            if line_split[0] == "POS":
                                new_line = f'POS {line_split[1]} {line_split[2]} {utm_east} {utm_north}\n'
                            elif line_split[0] == "RAW":
                                lat, lon = to_latlon(
                                    utm_east, utm_north, zone_number, northern=False)
                                new_line = f'RAW {line_split[1]} {line_split[2]} {line_split[3]} {lat*1e4} {lon*1e4} {alt} {line_split[7]}\n'
                            break
                    lines[i] = new_line
        f.close()

        with open(output_file_path, 'w') as f:
            for line in lines:
                f.write(line)
        f.close()
        return True

# endregion
