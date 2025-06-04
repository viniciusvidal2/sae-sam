import open3d as o3d
from numpy import array, asarray, uint8
from numpy import min as np_min, max as np_max, abs as np_abs
from numpy import median as np_median, std as np_std, sum as np_sum
from argparse import ArgumentParser
from os import path
from copy import deepcopy
from pyvista import PolyData
from typing import Generator


class SaescPipeline:
    def __init__(self) -> None:
        """Initializes the SaescPipeline class.
        """
        self.merged_cloud = o3d.geometry.PointCloud()
        self.output_path = ""
        self.sonar_depth = 0.5  # [m]

    def set_input_data(self, input_clouds_paths: list, input_clouds_types: list, sea_level_refs: list, preprocess_flags: list) -> None:
        """Sets the input data for the pipeline.

        Args:
            input_clouds_paths (list): input point clouds paths
            input_clouds_types (list): input point clouds types, wether sonar or drone
            sea_level_ref (list): reference sea level [m] to add to Z readings
            preprocess_flags (list): flags to indicate if preprocessing must be applied to each cloud
        """
        self.input_clouds_paths = input_clouds_paths
        self.input_clouds_types = input_clouds_types
        self.sea_level_refs = sea_level_refs  # Reference sea level [m]
        self.preprocess_flags = preprocess_flags

    def xyz_to_point_cloud(self, filename: str, invert_z: bool = True) -> o3d.geometry.PointCloud:
        """Converts a .xyz file to an open3d point cloud.

        Args:
            filename (str): _path to the .xyz file
            invert_z (bool, optional): If we must invert the z coordinate from the sonar acquisition frame. Defaults to True.

        Returns:
            o3d.geometry.PointCloud: point cloud object
        """
        with open(filename, 'r') as f:
            lines = f.readlines()

        # Extract x, y, z coordinates from each line
        points = []
        invert_z_mult = -1 if invert_z else 1
        for line in lines:
            coords = line.strip().split()
            if len(coords) >= 3:
                points.append([float(coords[0]), float(
                    coords[1]), invert_z_mult*float(coords[2])])

        # Convert points to numpy array and then to open3d point cloud
        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(asarray(points))
        return point_cloud

    def process_sonar_cloud(self, cloud: o3d.geometry.PointCloud, sea_level_ref: float, preprocess_flag: bool) -> o3d.geometry.PointCloud:
        """Processes the sonar point cloud by removing the noise and the ground plane.

        Args:
            cloud (o3d.geometry.PointCloud): input sonar point cloud
            sea_level_ref (float): reference sea level to add to Z readings
            preprocess_flag (bool): flag to indicate if preprocessing must be applied

        Returns:
            o3d.geometry.PointCloud: processed sonar point cloud
        """
        import matplotlib
        matplotlib.use('Qt5Agg')
        from matplotlib import colormaps
        # Voxelgrid
        cloud = cloud.voxel_down_sample(voxel_size=0.3)
        if preprocess_flag:
            # Remove SOR noise
            cloud, _ = cloud.remove_statistical_outlier(nb_neighbors=20,
                                                        std_ratio=1)
            # Remove spikes in the Z axis
            cloud = self.remove_spikes(pcd=cloud, radius=2, deviation=1.5)
        # Correct sea level
        points = array(cloud.points)
        points[:, 2] += sea_level_ref - self.sonar_depth
        cloud.points = o3d.utility.Vector3dVector(points)
        # Calculate the normals, flipping towards positive z
        cloud.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        cloud.normals = o3d.utility.Vector3dVector(
            array(cloud.normals) * array([1, 1, -1]))
        # Apply colormap intensity to the point cloud according to the depth in z
        z_values = np_abs(array(cloud.points)[:, 2])
        intensity = (z_values - np_min(z_values)) / \
            (np_max(z_values) - np_min(z_values))
        colormap_name = "jet"  # [jet, seismic, viridis]
        cmap = colormaps.get_cmap(colormap_name)
        cloud.colors = o3d.utility.Vector3dVector(cmap(intensity)[:, :3])
        return deepcopy(cloud)

    def process_drone_cloud(self, cloud: o3d.geometry.PointCloud, sea_level_ref: float) -> o3d.geometry.PointCloud:
        """Processes the drone point cloud by removing the noise and the ground plane.

        Args:
            cloud (o3d.geometry.PointCloud): input drone point cloud
            sea_level_ref (float): reference sea level to add to Z readings

        Returns:
            o3d.geometry.PointCloud: processed drone point cloud
        """
        # Remove SOR noise
        cloud, _ = cloud.remove_statistical_outlier(nb_neighbors=20,
                                                    std_ratio=2.0)
        points = array(cloud.points)
        # Find the minimum Z that should be close to the water level
        min_z = np_min(points[:, 2])
        # Add the sea level reference to ajust the Z values
        points[:, 2] += sea_level_ref - min_z
        cloud.points = o3d.utility.Vector3dVector(points)
        # Calculate the normals, flipping towards positive z
        cloud.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        cloud.normals = o3d.utility.Vector3dVector(
            array(cloud.normals) * array([1, 1, -1]))
        return deepcopy(cloud)

    def remove_spikes(self, pcd: o3d.geometry.PointCloud, radius: float, deviation: float) -> o3d.geometry.PointCloud:
        """Remove spikes from the point cloud.

        Args:
            pcd (o3d.geometry.PointCloud): input point cloud
            radius (float): radius to search for neighbors
            deviation (float): deviation to filter points

        Returns:
            o3d.geometry.PointCloud: processed point cloud
        """
        # Count neighbors within radius for each point
        kdtree = o3d.geometry.KDTreeFlann(pcd)
        neighbor_counts = []
        for i in range(len(pcd.points)):
            [_, idx, _] = kdtree.search_radius_vector_3d(pcd.points[i], radius)
            neighbor_counts.append(len(idx) - 1)
        # Filter metrics
        neighbor_counts = array(neighbor_counts)
        median = np_median(neighbor_counts)
        std_dev = np_std(neighbor_counts)
        # Filter points
        min_neighbors = median - deviation * std_dev
        mask = (neighbor_counts >= min_neighbors)
        filtered_points = asarray(pcd.points)[mask]
        return o3d.geometry.PointCloud() if np_sum(mask) == 0 else o3d.geometry.PointCloud(o3d.utility.Vector3dVector(filtered_points))

    def calculate_global_sea_level_reference(self) -> float:
        """Calculates the global sea level reference.

        Returns:
            float: global sea level reference
        """
        highest_ref = 0  # We compare to 0 to account for the drone values
        for ref in self.sea_level_refs:
            if ref > highest_ref:
                highest_ref = ref
        return highest_ref

    def merge_clouds(self) -> Generator[dict, None, None]:
        """Merges the point clouds properly into a single point cloud object.

        Returns:
            dict: Status: message of the process. Result: true if the point cloud was merged successfully. Pct: percentage of the process [0.0, 1.0].
        """
        if len(self.input_clouds_paths) == 0:
            yield {"status": "Error: no input point clouds were provided", "result": False, "pct": 0}

        # Get the global sea level that we will refer to for drone ptcs
        global_sea_level_ref = self.calculate_global_sea_level_reference()

        # Amount of processes to run
        process_count = float(len(self.input_clouds_paths) + 1)
        pct = 0

        for i in range(len(self.input_clouds_paths)):
            c_path = self.input_clouds_paths[i]
            c_type = self.input_clouds_types[i]

            # Initial percentage yield
            pct = float(i) / process_count
            yield {"status": f"Processing point cloud {i + 1} out of {len(self.input_clouds_paths)}", "result": True, "pct": pct}

            # Load the point cloud
            cloud = o3d.io.read_point_cloud(
                c_path) if c_type == "drone" else self.xyz_to_point_cloud(c_path)
            if cloud is None:
                yield {"status": f"Error: could not load point cloud from {c_path}", "result": False, "pct": 0}

            # Merge the point cloud according to the type
            if c_type == "unknown":
                yield {"status": f"Error: unknown point cloud type {c_type} for point cloud {c_path}", "result": False, "pct": 0}
            elif c_type == "sonar":
                self.merged_cloud += self.process_sonar_cloud(
                    cloud=cloud, sea_level_ref=self.sea_level_refs[i], preprocess_flag=self.preprocess_flags[i])
            elif c_type == "drone":
                self.merged_cloud += self.process_drone_cloud(
                    cloud=cloud, sea_level_ref=global_sea_level_ref)

            # Final percentage yield
            pct = float(i + 1) / process_count
            yield {"status": f"Processed point cloud {i + 1}!", "result": True, "pct": pct}
        yield {"status": "Point cloud was merged succesfully and is ready for download.", "result": True, "pct": 1.0}

    def save_merged_cloud(self) -> bool:
        """Saves the merged point cloud to the output path.

        Returns:
            bool: true if the point cloud was saved successfully
        """
        # Save the merged point cloud
        if not o3d.io.write_point_cloud(self.output_path, self.merged_cloud):
            return False
        return True

    def get_merged_cloud(self) -> o3d.geometry.PointCloud:
        """Returns the merged point cloud.

        Returns:
            o3d.geometry.PointCloud: merged point cloud
        """
        return self.merged_cloud

    def get_merged_cloud_pyvista(self) -> PolyData:
        """Returns the merged point cloud as a PyVista object.

        Returns:
            PolyData: merged point cloud as a PyVista object
        """
        points = asarray(self.merged_cloud.points)
        polydata = PolyData(points)
        if self.merged_cloud.has_colors():
            colors = (asarray(self.merged_cloud.colors)
                      * 255).astype(uint8)
            polydata.point_data["RGB"] = colors
        if self.merged_cloud.has_normals():
            normals = asarray(self.merged_cloud.normals)
            polydata.point_data["Normals"] = normals
        return polydata

    def set_sea_level_ref(self, sea_level_ref: float) -> None:
        """Sets the sea level reference.

        Args:
            sea_level_ref (float): reference sea level
        """
        self.sea_level_ref = sea_level_ref


if __name__ == "__main__":
    root_path = path.dirname(path.abspath(__file__))
    # Parse the arguments
    parser = ArgumentParser(
        description="Merge point clouds into a single point cloud")
    parser.add_argument("--output_path", type=str,
                        default=path.join(root_path, "../merged_cloud.ply"), required=False,
                        help="path to save the merged point cloud")
    parser.add_argument("--input_clouds_paths", type=list,
                        default=[path.join(root_path, "../barragem.ply"), path.join(root_path, "../espigao.ply")], required=False,
                        help="list of paths to the input point clouds")
    parser.add_argument("--input_clouds_types", type=list,
                        default=["sonar", "drone"], required=False,
                        help="list of types of the input point clouds")
    args = parser.parse_args()

    # Create the input point clouds data dictionary and the output path
    output_path = args.output_path
    input_clouds_paths = args.input_clouds_paths
    input_clouds_types = args.input_clouds_types
    print("Input parameters:")
    print(f"Output path: {output_path}")
    print(f"Input clouds paths: {input_clouds_paths}")
    print(f"Input clouds types: {input_clouds_types}")

    # Merge the point clouds
    cloud_merger = SaescPipeline(input_clouds_paths=input_clouds_paths,
                                 input_clouds_types=input_clouds_types,
                                 clouds_folder=path.join(
                                     path.dirname(output_path), ".."),
                                 merged_cloud_name=output_path,
                                 sea_level_ref=71.3)
    for status in cloud_merger.merge_clouds():
        print(status)
