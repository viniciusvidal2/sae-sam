import numpy as np
from PIL import Image
import os


class ImageRectification:
    def __init__(self, barrier_dimensions: dict, undistort_meters_pixel_ratio: float) -> None:
        """This class is used to rectify the image in the X direction, given the varied boat velocity when acquiring the image.

        Args:
            barrier_dimensions (dict): Dictionary containing the grid and collumn dimensions in meters
            undistort_meters_pixel_ratio (float): Ratio of meters per pixel in the width direction for undistortion
        """
        self.grid_width_m = barrier_dimensions["grid_width_m"]
        self.grid_height_m = barrier_dimensions["grid_height_m"]
        self.collumn_width_m = barrier_dimensions["collumn_width_m"]
        self.meters_pixel_ratio = undistort_meters_pixel_ratio
        self.grid_width_px = int(grid_width_m / meters_pixel_ratio)
        self.grid_height_px = None
        self.row_direction_meters_pixel_ratio = None
        self.collumn_width_px = int(collumn_width_m / meters_pixel_ratio)
        self.rectified_image = None
        self.collumn_boxes = []

    def snip_rectify_image(self, image: np.ndarray) -> np.ndarray:
        """Snips the region of interest and rectifies the content based on the detected boxes.

        Args:
            image (np.ndarray): input image

        Raises:
            ValueError: We must set the collumn boxes before rectifying the image

        Returns:
            np.ndarray: rectified image
        """
        if not self.collumn_boxes:
            raise ValueError(
                "Column boxes must be set before rectifying the image.")

        # Sort the boxes and the type they belong to so we can rectify the image
        boxes, types = self.sort_enhance_detected_boxes(self.collumn_boxes)

        # Define the highest and lowest points of the grid, and update the boxes to match them
        grid_lowest_point = image.shape[0]
        grid_highest_point = int(np.min(np.array([box[1] for box in boxes])))
        for box in boxes:
            box[1] = int(grid_highest_point)
            box[3] = int(grid_lowest_point)

        # For each box, rectify according to the desired dimension and add to the output image
        self.rectified_image = np.ndarray(
            shape=(grid_lowest_point - grid_highest_point, 1, 3), dtype=np.uint8)
        for box, box_type in zip(boxes, types):
            image_section = image[box[1]:box[3], box[0]:box[2]]
            rectified_section = self.rectify_image_section(
                image_section, box_type)
            self.rectified_image = np.hstack(
                (self.rectified_image, rectified_section))

        # Remove the first column of the image, which is empty, and return
        self.rectified_image = self.rectified_image[:, 1:, :]
        return self.rectified_image

    def sort_enhance_detected_boxes(self, collumn_boxes: list) -> tuple:
        """Sorts the detected boxes and their types. Creates grid boxes in between the collumn boxes.

        Args:
            collumn_boxes (list): List of collumn boxes

        Returns:
            tuple: Sorted boxes and their types
        """
        # Sort the collumn boxes by their x-coordinates
        collumn_boxes = sorted(collumn_boxes, key=lambda x: x[0])
        # Create grid boxes between the collumn boxes
        grid_boxes = []
        for i in range(len(collumn_boxes) - 1):
            left_box = collumn_boxes[i]
            right_box = collumn_boxes[i + 1]
            # Create a grid box between the two collumn boxes
            grid_box = [
                int(left_box[2]), int(left_box[1]), int(right_box[0]), int(right_box[3])]
            grid_boxes.append(grid_box)
        # Sort the boxes by their x-coordinates and assign the proper types in the same order
        boxes = grid_boxes + collumn_boxes
        types = ['grid'] * len(grid_boxes) + ['collumn'] * len(collumn_boxes)
        sorted_boxes, sorted_types = zip(
            *sorted(zip(boxes, types), key=lambda x: x[0][0]))
        return list(sorted_boxes), list(sorted_types)

    def rectify_image_section(self, image_section: np.ndarray, box_type: str) -> np.ndarray:
        """Apply rectification to the image section based on the box type.

        Args:
            image_section (np.ndarray): input image section
            box_type (str): type of the box ('grid' or 'collumn')

        Returns:
            np.ndarray: rectified image section
        """
        img = Image.fromarray(image_section)
        # Desired new width from the box type, keeping the same height
        new_width = self.grid_width_px if box_type == 'grid' else self.collumn_width_px
        new_height = img.size[1]
        resized_img = img.resize(
            (new_width, new_height), Image.Resampling.LANCZOS)
        return np.array(resized_img)

    def get_rectified_image(self) -> np.ndarray:
        """Returns the rectified image.

        Returns:
            np.ndarray: Rectified image
        """
        return self.rectified_image

    def get_original_image_section(self, image: np.ndarray) -> np.ndarray:
        """Returns the original image section based on the detected boxes.

        Args:
            image (np.ndarray): Original image

        Returns:
            np.ndarray: Original image section
        """
        if not self.collumn_boxes:
            raise ValueError(
                "Column boxes must be set before getting the original image section.")

        collumn_boxes = sorted(self.collumn_boxes, key=lambda x: x[0])
        section = image[collumn_boxes[0][1]:collumn_boxes[-1][3],
                        collumn_boxes[0][0]:collumn_boxes[-1][2]]
        return section

    def set_detected_boxes(self, collumn_boxes: list, barrier_boxes: list) -> None:
        """Sets the detected boxes for the collumns and the main grid.

        Args:
            collumn_boxes (list): List of collumn boxes
            barrier_boxes (list): List of grid boxes
        """
        # Get organized collumn boxes
        collumn_boxes_int = []
        for box in collumn_boxes:
            collumn_boxes_int.append([int(p) for p in box])
        self.collumn_boxes = self.filter_colliding_boxes(collumn_boxes_int)
        # Set the barrier box as the biggest box
        self.barrier_box = barrier_boxes[0]
        barrier_box_area = (barrier_boxes[0][2] - barrier_boxes[0][0]) * \
            (barrier_boxes[0][3] - barrier_boxes[0][1])
        for box in barrier_boxes:
            box_area = (box[2] - box[0]) * (box[3] - box[1])
            if box_area > barrier_box_area:
                barrier_box_area = box_area
                self.barrier_box = box
        self.barrier_box = [int(p) for p in self.barrier_box]

    def filter_colliding_boxes(self, boxes: list) -> list:
        """
        Filters a list of bounding boxes, removing the smallest area box in each collision.

        Args:
            boxes (list): A list of bounding boxes, where each box is represented as [x1, y1, x2, y2].

        Returns:
            A list of non-colliding bounding boxes.
        """
        non_colliding_boxes = []
        removed_indices = set()

        for i, box1 in enumerate(boxes):
            if i in removed_indices:
                continue
            is_colliding = False
            for j, box2 in enumerate(boxes):
                if i == j or j in removed_indices:
                    continue
                is_colliding = not (
                    box1[2] < box2[0] or box1[0] > box2[2] or box1[3] < box2[1] or box1[1] > box2[3])
                if is_colliding:
                    # Determine which box to remove based on area
                    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
                    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
                    removed_indices.add(i if area1 < area2 else j)
                    break

            if not is_colliding:
                non_colliding_boxes.append(box1)
        return non_colliding_boxes

    def get_meters_pixel_ratio(self) -> dict:
        """Returns the meters per pixel ratio for both directions.

        Returns:
            dict: meters per pixel ratio for width and height
        """
        if self.barrier_box is None:
            raise ValueError("Barrier box is not set.")
        self.grid_height_px = abs(self.barrier_box[3] - self.barrier_box[1])
        self.row_direction_meters_pixel_ratio = self.grid_height_m / self.grid_height_px
        return {
            "width": self.meters_pixel_ratio,
            "height": self.row_direction_meters_pixel_ratio
        }


if __name__ == "__main__":
    # Sample usage
    grid_width_m = 10
    collumn_width_m = 3
    meters_pixel_ratio = 0.1
    rectifier = ImageRectification(
        grid_width_m, collumn_width_m, meters_pixel_ratio)
    # Load an image
    image = np.array(Image.open(os.path.join(os.getenv("HOME"), "yolo", "full_train_set",
                     "train", "images", "snp0206251005_png.rf.a8bbdfbc64967838a2a76b632c711c7c.jpg")))
    # Set detected boxes (example values)
    collumn_boxes = [[50, 200, 150, 300], [250, 200, 350, 300]]
    rectifier.set_detected_boxes(collumn_boxes)
    # Get the original image section based on the detected boxes
    original_image_section = rectifier.get_original_image_section(image)
    # Rectify the image
    rectified_image = rectifier.snip_rectify_image(image)
    # Show the original and rectified image
    Image.fromarray(original_image_section).show()
    Image.fromarray(rectified_image).show()
