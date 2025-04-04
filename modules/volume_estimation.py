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
            grid_ptc=grid_ptc)

        # Get the grid point cloud aligned to the plane and the detection class smoothed along it
        grid_aligned_ptc = self.create_grid_aligned_ptc(
            grid_ptc=grid_ptc, plane_model=grid_plane_model)
        class_aligned_ptc = self.smooth_class_from_grid_plane(
            grid_ptc=grid_aligned_ptc, class_ptc=class_ptc, plane_model=grid_plane_model)
        if debug:
            axis = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=50, origin=[0, 0, 0])
            o3d.visualization.draw_geometries(
                [grid_aligned_ptc, class_aligned_ptc, axis])

        # Calculate the volume of the class point cloud based on the discrete integral for each point (pixel)
        pixel_res = {"x_res": 0.5, "y_res": 0.5}
        class_volume = self.calculate_detection_volume(
            pixel_res=pixel_res, ptc=class_aligned_ptc, plane_model=grid_plane_model)

        return class_volume

    def estimate_original_grid_plane(self, grid_ptc: o3d.geometry.PointCloud) -> Tuple:
        """Estimate the original grid plane using the grid point cloud
        This method uses the covariance matrix to find the plane equation (ax + by + cz + d = 0)

        Args:
            grid_ptc (o3d.geometry.PointCloud): The grid point cloud

        Returns:
            Tuple: The plane model coefficients (a, b, c, d) and the point cloud of the plane points
        """
        # Get the n points that are the furthest away using the z coordinate in a xy grid
        likely_grid_plane_points = self.get_grid_plane_candidate_points(
            grid_ptc=grid_ptc, n_cells_side=10)
        # Get the plane model using the points
        a, b, c, d = self.fit_plane(points=likely_grid_plane_points)
        # Create a point cloud for the plane points
        plane_ptc = o3d.geometry.PointCloud()
        plane_ptc.points = o3d.utility.Vector3dVector(
            likely_grid_plane_points)
        return [a, b, c, d], plane_ptc.paint_uniform_color([0, 1, 0])

    def get_grid_plane_candidate_points(self, grid_ptc: o3d.geometry.PointCloud, n_cells_side: int):
        """Get the grid plane candidate points based on the grid point cloud

        Args:
            grid_ptc (o3d.geometry.PointCloud): The grid point cloud
            n_cells_side (int): The number of cells in one side of the grid

        Returns:
            np.ndarray: The candidate points for the grid plane
        """
        # Get the points and colors of the grid point cloud
        points = np.array(grid_ptc.points)
        colors = np.array(grid_ptc.colors)
        # Get the min and max values for x and y
        min_x, max_x = np.min(points[:, 0]), np.max(points[:, 0])
        min_y, max_y = np.min(points[:, 1]), np.max(points[:, 1])
        # Compute bin size
        x_step = (max_x - min_x) / n_cells_side
        y_step = (max_y - min_y) / n_cells_side
        # Create a dictionary of bins with n by n cells to help find the points
        # that are the lowest in each bin
        bin_dict = dict()
        for p in points:
            bin_x = int((p[0] - min_x) / x_step)
            bin_y = int((p[1] - min_y) / y_step)

            bin_key = (bin_x, bin_y)
            if bin_key not in bin_dict or p[2] < bin_dict[bin_key][2]:
                bin_dict[bin_key] = p
        return np.array(list(bin_dict.values()))

    def fit_plane(self, points: np.ndarray) -> Tuple:
        """Estimates the plane equation (ax + by + cz + d = 0) from a set of 3D points using the covariance matrix.

        Args:
            points: Nx3 numpy array of 3D points.

        Returns:
            Tuple: Plane coefficients (a, b, c, d) where (a, b, c) is the normal vector and d is the plane offset.
        """
        # Compute centroid and cov matrix
        centroid = np.mean(points, axis=0)
        cov_matrix = np.cov(points.T)

        # The normal to the plane is the eigenvector corresponding to the smallest eigenvalue
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        normal = eigenvectors[:, np.argmin(eigenvalues)]

        # Plane equation: ax + by + cz + d = 0
        d = -np.dot(normal, centroid)
        return (*normal, d)

    def point_plane_distance_and_projection(self, point: np.ndarray, plane_model: list) -> Tuple:
        """Computes the distance of a 3D point to a plane and its projection onto the plane.

        Args:
            point (np.ndarray): query 3d point.
            plane_model (list): Plane equation coefficients a, b, c, d

        Returns:
            Tuple: distance and projected_point
        """
        a, b, c, d = plane_model
        normal = np.array([a, b, c])

        m = (np.dot(normal, point) + d) / (a*a + b*b + c*c)
        projected_point = point - m * normal
        distance = np.linalg.norm(projected_point - point)
        return distance, projected_point

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

    def calculate_detection_volume(self, pixel_res: dict, ptc: o3d.geometry.PointCloud, plane_model: list) -> float:
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
            projection_distance, projected_point = self.point_plane_distance_and_projection(
                point=point, plane_model=plane_model)
            if not self.point_hidden_behind_grid_plane(point=projected_point, plane_model=plane_model):
                # Calculate the volume of the pixel
                volume += pixel_res["x_res"] * pixel_res["y_res"] * \
                    pixel_res["z_res"] * projection_distance
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
        for x in range(-100, 100, 1):
            for y in range(-200, 200, 1):
                z = (-a * x - b * y - d) / c
                points.append([x, y, z])
        ptc = o3d.geometry.PointCloud()
        ptc.points = o3d.utility.Vector3dVector(np.array(points))
        return ptc.paint_uniform_color([0, 0, 1])

    def create_grid_aligned_ptc(self, grid_ptc: o3d.geometry.PointCloud, plane_model: list) -> o3d.geometry.PointCloud:
        """Creates a grid aligned point cloud based on the input model

        Args:
            grid_ptc (o3d.geometry.PointCloud): The grid point cloud
            class_ptc (o3d.geometry.PointCloud): The class point cloud
            plane_model (list): the plane model params ax + by + cz + d = 0

        Returns:
            o3d.geometry.PointCloud: The output grid aligned point cloud
        """
        projected_points = []
        projected_colors = []
        for p, c in zip(np.array(grid_ptc.points), np.array(grid_ptc.colors)):
            _, pp = self.point_plane_distance_and_projection(
                point=p, plane_model=plane_model)
            projected_points.append(pp)
            projected_colors.append(c)
        out_ptc = o3d.geometry.PointCloud()
        out_ptc.points = o3d.utility.Vector3dVector(np.array(projected_points))
        out_ptc.colors = o3d.utility.Vector3dVector(np.array(projected_colors))
        return out_ptc

    def smooth_class_from_grid_plane(self, grid_ptc: o3d.geometry.PointCloud, class_ptc: o3d.geometry.PointCloud, plane_model: list) -> o3d.geometry.PointCloud:
        """Smooths the class point cloud based on the grid plane

        Args:
            grid_ptc (o3d.geometry.PointCloud): The grid point cloud
            class_ptc (o3d.geometry.PointCloud): The class point cloud
            plane_model (list): the plane model params ax + by + cz + d = 0

        Returns:
            o3d.geometry.PointCloud: The output smoothed class point cloud
        """
        smoothed_points = []
        # Use both ptcs to find neighbors and smooth the grid result
        full_ptc = class_ptc + grid_ptc
        full_ptc_points = np.array(full_ptc.points)
        kdtree = o3d.geometry.KDTreeFlann(full_ptc)
        for p in np.array(class_ptc.points):
            # If point is hidden behind the grid plane, use the projected point as smoothed one
            if self.point_hidden_behind_grid_plane(point=p, plane_model=plane_model):
                _, p = self.point_plane_distance_and_projection(
                    point=p, plane_model=plane_model)
                smoothed_points.append(p)
                continue
            # Finds the n closest points in the grid point cloud
            [_, idx, _] = kdtree.search_knn_vector_3d(p, 100)
            # Calculate average as the smoothed point
            smoothed_point = p
            for i in range(len(idx)):
                smoothed_point += full_ptc_points[idx[i]]
            smoothed_points.append(smoothed_point/(len(idx)+1))
        # Create a point cloud for the smoothed points
        smoothed_class_ptc = o3d.geometry.PointCloud()
        smoothed_class_ptc.points = o3d.utility.Vector3dVector(
            np.array(smoothed_points))
        smoothed_class_ptc.colors = o3d.utility.Vector3dVector(
            np.array(class_ptc.colors))
        return smoothed_class_ptc

    def point_hidden_behind_grid_plane(self, point: np.ndarray, plane_model: list) -> bool:
        """Checks if a point is hidden behind the grid plane

        Args:
            point (np.ndarray): The point to check
            plane_model (list): The plane model coefficients

        Returns:
            bool: True if the point is hidden behind the grid plane, False otherwise
        """
        # If the angle between the projection to the point and the projection to the origin is greater than 90 degrees,
        # then the point is behind the grid plane
        _, projected_point = self.point_plane_distance_and_projection(
            point=point, plane_model=plane_model)
        projection_point_vector = projected_point - point
        projection_origin_vector = projected_point - np.array([0, 0, 0])
        angle = np.arccos(np.dot(projection_point_vector, projection_origin_vector) /
                          (np.linalg.norm(projection_point_vector) * np.linalg.norm(projection_origin_vector)))
        return angle > np.pi/2
