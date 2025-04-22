from pymavlink import mavutil
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import utm


class ArdupilotLogReader:
    def __init__(self):
        """Constructor for the ArdupilotLogReader class.
        """
        self.log_file_path = ''
        self.gps_data = []
        # Adjust for leap seconds (current offset as of 2024 is 18 seconds)
        self.leap_seconds = 18
        # GPS epoch is 6th January 1980
        self.gps_epoch = datetime(1980, 1, 6)

    def set_log_file_path(self, file_path: str) -> None:
        """Sets the ardupilot log file path to be read.

        Args:
            file_path (str): the file path
        """
        self.log_file_path = file_path
        self.missions_in_log = []

    def calculate_utc_timestamp(self, timestamp_ms: float, gps_week: int = 0) -> float:
        """Calculates the UTC timestamp from the GPS timestamp and week.

        Args:
            timestamp_ms (float): the timestamp in milliseconds
            gps_week (int, optional): the GPS week. Defaults to 0.

        Returns:
            float: the UTC timestamp
        """
        # Calculate GPS seconds of the week, then apply to GPS epoch
        gps_time_utc = self.gps_epoch + \
            timedelta(weeks=gps_week, seconds=timestamp_ms / 1e3) - \
            timedelta(seconds=self.leap_seconds)
        return gps_time_utc.timestamp()

    def read_data_from_log(self):
        """Generates the data from the log file.
        """
        if self.log_file_path == '':
            print('No file path set')
            return
        # First lets read the GPS data as necessary
        log_file = mavutil.mavlink_connection(
            self.log_file_path, robust_parsing=True)
        while True:
            msg = log_file.recv_match(type='GPS', blocking=True)
            if msg is None:
                break
            self.gps_data.append({
                "latitude": msg.Lat,
                "longitude": msg.Lng,
                "altitude": msg.Alt,
                "timestamp": self.calculate_utc_timestamp(msg.GMS, msg.GWk),
                "TimeUS": msg.TimeUS
            })
        log_file.close()

        # Now look for the CMD messages that contain mission points
        mission_command_messages = []
        log_file = mavutil.mavlink_connection(
            self.log_file_path, robust_parsing=True)
        while True:
            msg = log_file.recv_match(type='CMD', blocking=True)
            if msg is None:
                break
            if msg.Lat != 0 and msg.Lng != 0 and msg.Frame == 3 and msg.CId == 16:
                mission_command_messages.append(msg)
        log_file.close()
        # Split the mission command messages into missions
        # Get the timestamps from the messages and cluster them by getting groups that are less than 2 seconds apart
        # The timestamps are already sorted
        missions_in_log = []
        current_mission = []
        current_reference_timestamp = 0
        for msg in mission_command_messages:
            if len(current_mission) == 0:
                current_mission.append(msg)
                current_reference_timestamp = msg.TimeUS
            elif msg.TimeUS - current_reference_timestamp < 2e6:
                current_mission.append(msg)
            else:
                missions_in_log.append(current_mission)
                current_mission = []
        for mission in missions_in_log:
            # Only consider missions with more than one command, as a single command is merely a report we passed there
            if len(mission) > 1:
                # Calculate the UTM coordinates for the first and last waypoints
                first_waypoint = utm.from_latlon(
                    mission[0].Lat, mission[0].Lng)
                last_waypoint = utm.from_latlon(
                    mission[-1].Lat, mission[-1].Lng)
                # If they are more then 10 meters apart, add the first point to the end of the list
                # with a timestamp 1 millisecond after the last one
                if ((first_waypoint[0] - last_waypoint[0])**2 + (first_waypoint[1] - last_waypoint[1])**2)**0.5 > 10:
                    mission.append(mission[0])
                    mission[-1].TimeUS += 1e3
                # Convert each point to UTM coordinates
                waypoints_utm_coords = []
                for waypoint in mission:
                    utm_east, utm_north, _, _ = utm.from_latlon(
                        waypoint.Lat, waypoint.Lng)
                    waypoints_utm_coords.append({
                        'utm_east': utm_east,
                        'utm_north': utm_north
                    })
                self.missions_in_log.append({
                    'start_timestamp': mission[0].TimeUS,
                    'end_timestamp': mission[-1].TimeUS,
                    'waypoints': waypoints_utm_coords
                })

    def get_utm_points_with_utc_timestamps(self):
        """Gets the UTM points with UTC timestamps.

        Returns:
            list: the list of UTM points with UTC timestamps
        """
        utm_data = []
        for gps in self.gps_data:
            utm_coords = utm.from_latlon(gps['latitude'], gps['longitude'])
            utm_data.append({
                'utm_east': utm_coords[0],
                'utm_north': utm_coords[1],
                'altitude': gps['altitude'],
                'timestamp': gps['timestamp'],
                'TimeUS': gps['TimeUS']
            })
        return utm_data

    def get_missions_in_log(self):
        """Gets the missions in the log.
        """
        return self.missions_in_log

    def get_data_percentages_from_mission_waypoints(self, log_gps_points: list) -> list:
        """Returns a list of pairs representing the percentages of each scan line according to mission waypoint synchronization.

        Args:
            log_gps_points (list): the list of GPS points of the mission

        Returns:
            list: the list of pairs representing the percentages of each scan line
        """
        # Get the mission where the end time is the closest to the first gps point, but lower than it
        first_gps_time = log_gps_points[0]['TimeUS']
        closest_mission = None
        closest_diff = 1e10
        for mission in self.missions_in_log:
            if mission['end_timestamp'] < first_gps_time:
                diff = first_gps_time - mission['end_timestamp']
                if diff < closest_diff:
                    closest_diff = diff
                    closest_mission = mission
        # If we have a mission, find the percentages by matching the GPS points with the mission points
        if closest_mission is not None:
            gps_mission_match_indices = []
            last_matched_index = 0
            for mission_point in closest_mission['waypoints']:
                for i, gps_point in enumerate(log_gps_points):
                    if i <= last_matched_index:
                        continue
                    # If the gps point is closer than 5 meters to the waypoint in the mission, consider it a match
                    # and take the next mission point as reference
                    utm_east_diff = gps_point['utm_east'] - \
                        mission_point['utm_east']
                    utm_north_diff = gps_point['utm_north'] - \
                        mission_point['utm_north']
                    distance_diff = (utm_east_diff**2 + utm_north_diff**2)**0.5
                    if distance_diff < 5:
                        gps_mission_match_indices.append(i)
                        last_matched_index = i
                        break
            # Create the points percentages that we must save
            percentage_pairs = []
            for i in range(len(gps_mission_match_indices) - 1):
                percentage_pairs.append((gps_mission_match_indices[i]/len(
                    log_gps_points), gps_mission_match_indices[i + 1]/len(log_gps_points)))
            # Add the first leg if it is more than 10% of the mission
            if percentage_pairs[0][0] > 0.1:
                percentage_pairs.insert(
                    0, (0.0, gps_mission_match_indices[0]/len(log_gps_points)))
            # Add the last leg if it is less than 90% of the mission
            if percentage_pairs[-1][-1] < 0.9:
                percentage_pairs.append(
                    (gps_mission_match_indices[-1]/len(log_gps_points), 1.0))
            return percentage_pairs
        return None
