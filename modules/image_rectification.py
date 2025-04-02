import numpy as np
from PIL import Image
import os


class ImageRectification:
    def __init__(self, grid_width_m: float, collumn_width_m: float, meters_pixel_ratio: float) -> None:
        """This class is used to rectify the image in the X direction, given the varied boat velocity when acquiring the image.

        Args:
            grid_width_m (float): grid width in meters
            collumn_width_m (float): collumn width in meters
            meters_pixel_ratio (float): ratio of meters per pixel
        """
        self.grid_width_m = grid_width_m
        self.collumn_width_m = collumn_width_m
        self.meters_pixel_ratio = meters_pixel_ratio
        self.grid_width_px = int(grid_width_m / meters_pixel_ratio)
        self.collumn_width_px = int(collumn_width_m / meters_pixel_ratio)
        self.rectified_image = None
        self.collumn_boxes = []

    def snip_rectify_image(self, image: np.ndarray) -> np.ndarray:
        if not self.collumn_boxes:
            raise ValueError(
                "Column boxes must be set before rectifying the image.")

        # Sort the boxes and the type they belong to so we can rectify the image
        boxes, types = self.sort_enhance_detected_boxes(self.collumn_boxes)

        # Define the highest and lowest points of the grid, and update the boxes to match them
        grid_lowest_point = image.shape[0]
        grid_highest_point = np.min(np.array([box[1] for box in boxes]))
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

    def set_detected_boxes(self, collumn_boxes: list) -> None:
        """Sets the detected boxes for the collumns.

        Args:
            collumn_boxes (list): List of collumn boxes
        """
        self.collumn_boxes = collumn_boxes

    def set_image_real_params(self, grid_width_m: float, collumn_width_m: float, meters_pixel_ratio: float) -> None:
        """Sets the real parameters of the image.

        Args:
            grid_width_m (float): Grid width in meters
            collumn_width_m (float): Collumn width in meters
            meters_pixel_ratio (float): Ratio of meters per pixel
        """
        self.grid_width_m = grid_width_m
        self.collumn_width_m = collumn_width_m
        self.meters_pixel_ratio = meters_pixel_ratio


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
