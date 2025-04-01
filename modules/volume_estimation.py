from transformers import pipeline
from PIL import Image
import numpy as np


class VolumeEstimation:
    def __init__(self, model_name: str, m_per_pixel: float, class_ids: list) -> None:
        """This class is used to estimate the volume of objects in an image using a depth estimation model.

        Args:
            model_name (str): name of the depth estimation model
            m_per_pixel (float): meters per pixel ratio
            class_ids (list): list of class IDs the model can detect in the form of 'name': code(int)
        """
        self.pipe = pipeline(task="depth-estimation", model=model_name)
        self.m_per_pixel = m_per_pixel

    def estimate_blocking_volume(self, image: np.ndarray, box: list, mask: np.ndarray, class_name: str) -> float:
        """Estimates the volume of objects in the image.

        Args:
            image (np.ndarray): original image
            box (list): bounding box of the object in the image
            mask (np.ndarray): binary mask of the region with grid, collumn and obstruction indices
            class_name (str): name of the class to estimate the volume for

        Returns:
            np.ndarray: estimated depth map
        """
        # Enhance the box by 20% in each direction, making sure it does not go outside the image boundaries
        box[0] = max(0, int(box[0] - 0.2 * (box[2] - box[0])))
        box[1] = max(0, int(box[1] - 0.2 * (box[3] - box[1])))
        box[2] = min(image.shape[1], int(box[2] + 0.2 * (box[2] - box[0])))
        box[3] = min(image.shape[0], int(box[3] + 0.2 * (box[3] - box[1])))
        # Get the bounding box section of the image and the mask
        image_bbox = image[box[1]:box[3], box[0]:box[2]]
        mask_bbox = mask[box[1]:box[3], box[0]:box[2]]

        # Run pipeline in the bounding box image section to get depth image in pixels
        image_pil = Image.fromarray(image_bbox)
        depth_image_pil = self.pipe(image_pil)["depth"]

        # Create a point cloud with the depth image and image coordinates

        # Get the point cloud centroid and centralize around it

        # Obtain the points that belong to the grid, if any

        # Estimate a plane that best fits the grid points

        return 0.5
