import open3d as o3d
import numpy as np
import argparse
import os
from copy import deepcopy
import pyvista as pv
from matplotlib import colormaps
from typing import Generator


class CloudMerger:
    def __init__(self, input_clouds_paths: list, input_clouds_types: list, clouds_folder: str, merged_cloud_name: str, sea_level_ref: float) -> None:
        """Initializes the CloudMerger class with the output path and the input point clouds paths and types.

        Args:
            input_clouds_paths (list): input point clouds paths
            input_clouds_types (list): input point clouds types, wether sonar or sfm
            clouds_folder (str): folder where the point clouds are stored
            merged_cloud_name (str): name of the merged point cloud
            sea_level_ref (float): reference sea level to add to Z readings
        """
        self.input_clouds_paths = input_clouds_paths
        self.input_clouds_types = input_clouds_types
        self.merged_cloud = o3d.geometry.PointCloud()
        self.output_path = os.path.join(clouds_folder, merged_cloud_name)
        self.sea_level_ref = sea_level_ref  # Reference sea level [m]
        self.sonar_depth = 0.5  # [m]

    def process_sonar_cloud(self, cloud: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """Processes the sonar point cloud by removing the noise and the ground plane.

        Args:
            cloud (o3d.geometry.PointCloud): input sonar point cloud

        Returns:
            o3d.geometry.PointCloud: processed sonar point cloud
        """
        # Voxelgrid
        cloud = cloud.voxel_down_sample(voxel_size=0.05)
        # Flip the point cloud in z direction and correct sea level
        points = np.array(cloud.points) * np.array([1, 1, -1])
        points[:, 2] += self.sea_level_ref - self.sonar_depth
        cloud.points = o3d.utility.Vector3dVector(points)
        # Calculate the normals, flipping towards positive z
        cloud.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        cloud.normals = o3d.utility.Vector3dVector(
            np.array(cloud.normals) * np.array([1, 1, -1]))
        # Apply colormap intensity to the point cloud according to the depth in z
        z_values = np.abs(np.array(cloud.points)[:, 2])
        intensity = 1.0 - (z_values - np.min(z_values)) / \
            (np.max(z_values) - np.min(z_values))
        colormap_name = "seismic"  # or viridis
        cmap = colormaps.get_cmap(colormap_name)
        cloud.colors = o3d.utility.Vector3dVector(cmap(intensity)[:, :3])

        return deepcopy(cloud)

    def process_sfm_cloud(self, cloud: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """Processes the sfm point cloud by removing the noise and the ground plane.

        Args:
            cloud (o3d.geometry.PointCloud): input sfm point cloud

        Returns:
            o3d.geometry.PointCloud: processed sfm point cloud
        """
        # Remove SOR noise
        cloud, _ = cloud.remove_statistical_outlier(nb_neighbors=20,
                                                      std_ratio=2.0)
        points = np.array(cloud.points)
        # Find the minimum Z that should be close to the water level
        min_z = np.min(points[:, 2])
        # Add the sea level reference to ajust the Z values
        points[:, 2] += self.sea_level_ref - min_z
        cloud.points = o3d.utility.Vector3dVector(points)
        # Calculate the normals, flipping towards positive z
        cloud.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        cloud.normals = o3d.utility.Vector3dVector(
            np.array(cloud.normals) * np.array([1, 1, -1]))

        return deepcopy(cloud)

    def merge_clouds(self) -> Generator[dict, None, None]:
        """Merges the point clouds properly into a single point cloud object.

        Returns:
            dict: Status: message of the process. Result: true if the point cloud was merged successfully. Pct: percentage of the process [0.0, 1.0].
        """
        # If output directory does not exist, call an error
        if not os.path.exists(os.path.dirname(self.output_path)):
            yield {"status": f"Error: output directory {os.path.dirname(self.output_path)} does not exist", "result": False, "pct": 0}

        if len(self.input_clouds_paths) == 0:
            yield {"status": "Error: no input point clouds were provided", "result": False, "pct": 0}

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
            cloud = o3d.io.read_point_cloud(c_path)
            if cloud is None:
                yield {"status": f"Error: could not load point cloud from {c_path}", "result": False, "pct": 0}

            # Merge the point cloud according to the type
            if c_type == "unknown":
                yield {"status": f"Error: unknown point cloud type {c_type} for point cloud {c_path}", "result": False, "pct": 0}
            elif c_type == "sonar":
                self.merged_cloud += self.process_sonar_cloud(cloud)
            elif c_type == "sfm":
                self.merged_cloud += self.process_sfm_cloud(cloud)

            # Final percentage yield
            pct = float(i + 1) / process_count
            yield {"status": f"Processed point cloud {i + 1}!", "result": True, "pct": pct}

        # Save the merged point cloud
        yield {"status": "Saving merged cloud ...", "result": True, "pct": pct}
        if not self.save_merged_cloud():
            yield {"status": f"Unable to save the merged cloud to {self.output_path}", "result": False, "pct": 0}

        yield {"status": "Point cloud was merged succesfully", "result": True, "pct": 1.0}

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

    def get_merged_cloud_pyvista(self) -> pv.PolyData:
        """Returns the merged point cloud as a PyVista object.

        Returns:
            pv.PolyData: merged point cloud as a PyVista object
        """
        points = np.asarray(self.merged_cloud.points)
        polydata = pv.PolyData(points)
        if self.merged_cloud.has_colors():
            colors = (np.asarray(self.merged_cloud.colors)
                      * 255).astype(np.uint8)
            polydata.point_data["RGB"] = colors
        if self.merged_cloud.has_normals():
            normals = np.asarray(self.merged_cloud.normals)
            polydata.point_data["Normals"] = normals

        return polydata

    def get_merged_cloud_bytes(self) -> bytes:
        """Returns the merged point cloud as bytes.

        Returns:
            bytes: merged point cloud as bytes
        """
        with open(self.output_path, "rb") as f:
            return f.read()
        
    def set_sea_level_ref(self, sea_level_ref: float) -> None:
        """Sets the sea level reference.

        Args:
            sea_level_ref (float): reference sea level
        """
        self.sea_level_ref = sea_level_ref


if __name__ == "__main__":
    root_path = os.path.dirname(os.path.abspath(__file__))
    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="Merge point clouds into a single point cloud")
    parser.add_argument("--output_path", type=str,
                        default=os.path.join(root_path, "../merged_cloud.ply"), required=False,
                        help="path to save the merged point cloud")
    parser.add_argument("--input_clouds_paths", type=list,
                        default=[os.path.join(root_path, "../barragem.ply"), os.path.join(root_path, "../espigao.ply")], required=False,
                        help="list of paths to the input point clouds")
    parser.add_argument("--input_clouds_types", type=list,
                        default=["sonar", "sfm"], required=False,
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
    cloud_merger = CloudMerger(input_clouds_paths=input_clouds_paths,
                               input_clouds_types=input_clouds_types,
                               clouds_folder=os.path.join(
                                   os.path.dirname(output_path), ".."),
                               merged_cloud_name=output_path,
                               sea_level_ref=71.3)
    for status in cloud_merger.merge_clouds():
        print(status)
