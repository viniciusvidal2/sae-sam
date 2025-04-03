from transformers import pipeline
from PIL import Image
import numpy as np
import open3d as o3d
from typing import Tuple
from copy import deepcopy
from scipy.spatial.transform import Rotation


class VolumeEstimation:
    def __init__(self, model_name: str, m_per_pixel: float, class_ids: dict) -> None:
        """This class is used to estimate the volume of objects in an image using a depth estimation model.

        Args:
            model_name (str): name of the depth estimation model
            m_per_pixel (float): meters per pixel ratio
            class_ids (dict): Dict of class IDs the model can detect in the form of 'name': code(int)
        """
        self.pipe = pipeline(task="depth-estimation", model=model_name)
        self.m_per_pixel = m_per_pixel
        self.class_ids = class_ids

    def estimate_blocking_volume(self, image: np.ndarray, box: list, mask: np.ndarray, class_name: str, debug: bool = False) -> float:
        """Estimates the volume of objects in the image.

        Args:
            image (np.ndarray): original image
            box (list): bounding box of the object in the image
            mask (np.ndarray): binary mask of the region with grid, collumn and obstruction indices
            class_name (str): name of the class to estimate the volume for
            debug (bool, optional): if True, shows the debug point clouds. Defaults to False.

        Returns:
            np.ndarray: estimated depth map
        """
        # Enhance the box by h% in height and w% in width, making sure it does not go outside the image boundaries
        h, w = 0.1, 0.5
        box[0] = max(0, int(box[0] - w * (box[2] - box[0])))
        box[1] = max(0, int(box[1] - h * (box[3] - box[1])))
        box[2] = min(image.shape[1], int(box[2] + w * (box[2] - box[0])))
        box[3] = min(image.shape[0], int(box[3] + h * (box[3] - box[1])))

        # Get the bounding box section of the image and the mask
        image_bbox = image[box[1]:box[3], box[0]:box[2]]
        mask_bbox = mask[box[1]:box[3], box[0]:box[2]]

        # Run pipeline in the bounding box image section to get depth image in pixels
        image_bbox_pil = Image.fromarray(image_bbox)
        depth_image_bbox_pil = self.pipe(image_bbox_pil)["depth"]
        depth_image_bbox = np.array(depth_image_bbox_pil)

        # Split the depth image into grid and class_name point clouds
        grid_ptc, class_ptc = self.split_class_grid_ptcs(
            mask=mask_bbox, depth_image=depth_image_bbox,
            rgb_image=image_bbox, class_name=class_name)

        # Obtain the estimated plane for the grid point cloud
        grid_plane_model, plane_points_ptc = self.estimate_original_grid_plane(
            grid_ptc=grid_ptc, n=100)
        plane_normal = grid_plane_model[:3]
        plane_d = grid_plane_model[3]
        # Make sure the normal is pointing towards negative z
        if plane_normal[2] > 0:
            plane_normal = -plane_normal
        if debug:
            # Create a point cloud for the estimated plane
            plane_ptc = self.create_plane_ptc(plane_model=grid_plane_model)
            axis = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=50, origin=[0, 0, 0])
            class_ptc_debug = deepcopy(class_ptc)
            class_ptc_debug.paint_uniform_color([1, 0, 0])
            o3d.visualization.draw_geometries(
                [grid_ptc, class_ptc_debug, axis, plane_ptc, plane_points_ptc])

        # Get the rotation matrix to align the plane normal with the negative Z axis
        z_axis = np.array([0, 0, -1])
        rotation_matrix = self.get_rotation_matrix_from_vectors(
            source_vector=plane_normal, target_vector=z_axis)
        # Rotate the point clouds to align with the Z axis
        grid_ptc.rotate(rotation_matrix, center=grid_ptc.get_center())
        class_ptc.rotate(rotation_matrix, center=grid_ptc.get_center())
        # Translate the point clouds to the plane origin based on the d plane coefficient
        translation_vector = np.array([0, 0, plane_d])
        grid_ptc.translate(translation_vector)
        class_ptc.translate(translation_vector)
        if debug:
            # Create axis at the origin
            axis = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=50, origin=[0, 0, 0])
            # Show the point clouds
            class_ptc_debug = deepcopy(class_ptc)
            class_ptc_debug.paint_uniform_color([1, 0, 0])
            o3d.visualization.draw_geometries(
                [grid_ptc, class_ptc_debug, axis])

        # Calculate the volume of the class point cloud based on the discrete integral for each point (pixel)
        pixel_res = {"x_res": 0.5, "y_res": 0.5}
        class_volume = self.calculate_volume(
            pixel_res=pixel_res, ptc=class_ptc)

        return class_volume
    
    def estimate_original_grid_plane(self, grid_ptc: o3d.geometry.PointCloud, n: int) -> Tuple:
        # Get the n points that are the furthest away using the z coordinate
        likely_grid_plane_points = sorted(np.array(grid_ptc.points), key=lambda x: x[2], reverse=True)[:n]
        grid_plane_ptc = o3d.geometry.PointCloud()
        grid_plane_ptc.points = o3d.utility.Vector3dVector(np.array(likely_grid_plane_points))
        # Get the plane model using the points
        plane_model, inliers = grid_plane_ptc.segment_plane(
            distance_threshold=5, ransac_n=30, num_iterations=1000)
        # Get the ptc with inliers
        plane_ptc = grid_ptc.select_by_index(inliers)
        return plane_model, plane_ptc.paint_uniform_color([0, 1, 0])


    def get_rotation_matrix_from_vectors(self, source_vector: np.ndarray, target_vector: np.ndarray) -> np.ndarray:
        """
        Computes the rotation matrix that aligns the source vector to the target vector
        using the scipy Rotation module.

        Args:
            source_vector (np.ndarray): A 3D numpy array representing the source vector.
            target_vector (np.ndarray): A 3D numpy array representing the target vector.

        Returns:
            np.ndarray: A 3x3 numpy array representing the rotation matrix.
        """
        source_vector = np.asarray(source_vector)
        target_vector = np.asarray(target_vector)
        source_unit = source_vector / np.linalg.norm(source_vector)
        target_unit = target_vector / np.linalg.norm(target_vector)

        rotation = Rotation.align_vectors(
            source_unit.reshape(1, -1), target_unit.reshape(1, -1))

        rotation_matrix = rotation[0].as_matrix()

        return rotation_matrix

    def split_class_grid_ptcs(self, mask: np.ndarray, depth_image: np.ndarray, rgb_image: np.ndarray, class_name: str) -> Tuple:
        """Splits a depth image with mask information into two point clouds, with the detected class and the grid

        Args:
            mask (np.ndarray): the mask with class ids
            depth_image (np.ndarray): the depth image
            rgb_image (np.ndarray): the original image
            class_name (str): the class id to look for

        Returns:
            List: grid and desired class point clouds
        """
        class_id = self.class_ids[class_name]
        barragem_id = self.class_ids["barragem"]
        class_points, class_colors = [], []
        grid_points, grid_colors = [], []
        # Search the mask and add the proper points for barragem or class
        for row in range(depth_image.shape[0]):
            for col in range(depth_image.shape[1]):
                if mask[row, col] == class_id:
                    class_points.append([col, row, depth_image[row, col]])
                    class_colors.append(
                        rgb_image[row, col].astype(np.float32)/255)
                elif mask[row, col] == barragem_id:
                    grid_points.append([col, row, depth_image[row, col]])
                    grid_colors.append(
                        rgb_image[row, col].astype(np.float32)/255)
        # Create point clouds for the grid and the class
        class_ptc = o3d.geometry.PointCloud()
        grid_ptc = o3d.geometry.PointCloud()
        class_ptc.points = o3d.utility.Vector3dVector(np.array(class_points))
        grid_ptc.points = o3d.utility.Vector3dVector(np.array(grid_points))
        class_ptc.colors = o3d.utility.Vector3dVector(np.array(class_colors))
        grid_ptc.colors = o3d.utility.Vector3dVector(np.array(grid_colors))
        return grid_ptc, class_ptc

    def calculate_volume(self, pixel_res: dict, ptc: o3d.geometry.PointCloud) -> float:
        """Calculates the volume of a point cloud that is aligned to the Z axis based on the input pixel resolution

        Args:
            pixel_res (dict): Resolution for x and y, in terms of meters per pixel (each point comes from a pixel)
            ptc (o3d.geometry.PointCloud): point cloud to calculate the volume for

        Returns:
            float: the estimated volume in meters
        """
        pixel_res["z_res"] = (pixel_res["x_res"] + pixel_res["y_res"])/2
        volume = 0
        for point in np.array(ptc.points):
            if point[2] > 0:
                volume += pixel_res["x_res"] * \
                    pixel_res["y_res"] * point[2] * pixel_res["z_res"]

        return volume

    def create_plane_ptc(self, plane_model: list) -> o3d.geometry.PointCloud:
        """Creates a plane point cloud based on the input model

        Args:
            plane_model (list): the plane model params ax + by + cz + d = 0

        Returns:
            o3d.geometry.PointCloud: The output plane point cloud
        """
        a, b, c, d = plane_model
        points = []
        for x in range(-200, 200, 1):
            for y in range(-300, 300, 1):
                z = (a * x + b * y - d) / c
                points.append([x, y, z])
        ptc = o3d.geometry.PointCloud()
        ptc.points = o3d.utility.Vector3dVector(np.array(points))
        return ptc.paint_uniform_color([0, 0, 1])
