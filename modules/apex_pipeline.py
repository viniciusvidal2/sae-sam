import numpy as np
import os
from PIL import Image
import cv2
from typing import Generator, Any
from modules.image_rectification import ImageRectification
from modules.image_segmentation import ImageSegmentation
from modules.metrics_estimation import MetricsEstimation


class ApexPipeline:
    def __init__(self, undistort_m_pixel_ratio: float) -> None:
        """Initialize the pipeline with the given parameters.
        Args:
            undistort_m_pixel_ratio (float): Ratio of meters per pixel in the width direction for undistortion.
        """
        self.undistort_m_pixel_ratio = undistort_m_pixel_ratio
        self.detections_metrics = list()
        # Classes to keep track of metrics
        self.desired_classes = ["macrofita", "sedimento", "tronco"]
        # Segmented image to show after processing is done
        self.segmented_image = None

    def set_barrier_dimensions(self, barrier_dimensions: dict) -> None:
        """Set the barrier dimensions for the pipeline.
        Args:
            barrier_dimensions (dict): Dictionary containing the grid and collumn dimensions in meters.
        """
        self.barrier_dimensions = barrier_dimensions

    def get_boxes_from_image(self, image: np.ndarray, class_id: int) -> list:
        """Get bouding boxes and confidences from the image.

        Args:
            image (np.ndarray): input bounding box with the codes given by semantic segmentation class
            class_id (int): the class id to get the boxes from

        Returns:
            list: boxes for this class id
        """
        binary = (image == class_id).astype(np.uint8) * 255
        # Dilate the binary image to fill in gaps
        kernel = np.ones((5, 5), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for contour in contours:
            # if area is too small, skip it
            if cv2.contourArea(contour) < 100:
                continue
            # Get the bounding box for the contour
            x, y, w, h = cv2.boundingRect(contour)
            boxes.append([x, y, x + w, y + h])

        return boxes

    def run(self, image_path: str) -> Generator[float, str, Any]:
        """Run the pipeline with the given parameters.
        Args:
            image_path (str): Path to the image.
        """
        # If there are no dimensions set yet, raise an error
        if not hasattr(self, 'barrier_dimensions'):
            raise ValueError(
                "Barrier dimensions must be set before running the pipeline.")

        # Read image into numpy array
        yield 0, "Starting the pipeline..."
        image = np.array(Image.open(image_path))

        # Lets segment the image to find the collumns
        image_segmentation = ImageSegmentation(model_path="models/image_segmentation/weights/best.pt")
        collumn_boxes = []
        barrier_boxes = []
        if image_segmentation.segment_classes(image=image):
            collumn_boxes, _ = image_segmentation.get_detections_by_class(
                class_name="coluna")
            barrier_boxes, _ = image_segmentation.get_detections_by_class(
                class_name="barragem")
        else:
            raise ValueError("Failed to find detections in the image.")
        class_ids = image_segmentation.get_detections_codes()
        if not collumn_boxes or not barrier_boxes:
            yield 30, "No collumns or barriers detected in the image."
            return
        yield 30, "Image segmented successfully. Starting rectification..."

        # Now lets rectify the image and the detected global mask
        image_rectification = ImageRectification(
            barrier_dimensions=self.barrier_dimensions, undistort_meters_pixel_ratio=self.undistort_m_pixel_ratio)
        image_rectification.set_detected_boxes(
            collumn_boxes=collumn_boxes, barrier_boxes=barrier_boxes)
        rectified_image = image_rectification.snip_rectify_image(image=image)
        rectified_mask = image_rectification.snip_rectify_image(
            image=image_segmentation.get_detections_mask())
        meter_pixel_ratios = image_rectification.get_meters_pixel_ratio()
        self.segmented_image = image_rectification.snip_rectify_image(
            image_segmentation.get_masked_image())
        yield 60, "Image rectified successfully. Starting metrics estimation..."

        # Lets estimate the metrics
        metrics_estimation = MetricsEstimation(
            model_local_path="./models/distill_any_depth/22c685bb9cd0d99520f2438644d2a9ad2cea41dc", m_per_pixel=meter_pixel_ratios, class_ids=class_ids)
        for k, desired_class in enumerate(self.desired_classes):
            pct = 60 + (k + 1) * 10
            # Get the global mask and macrofitas boxes
            boxes = self.get_boxes_from_image(
                image=rectified_mask, class_id=class_ids[desired_class])
            if not boxes:
                yield pct, f"No {desired_class} detected in the image."
                continue
            for box in boxes:
                # Estimate the volume of each macrofita group
                area, volume = metrics_estimation.estimate_blocking_area_volume(
                    image=rectified_image, box=box, mask=rectified_mask, class_name=desired_class, debug=False)
                if area < 10:
                    continue
                # Add the detection metrics to the dictionary
                self.detections_metrics.append(
                    {"area": area, "volume": volume, "box": box, "class": desired_class})
            yield pct, f"{desired_class} metrics estimated successfully."

        yield pct, "Metrics estimation completed successfully. Generating image with detections..."
        # Draw the codes in the image for each detection
        colormap = image_segmentation.get_colormap()
        for d, detection in enumerate(self.detections_metrics):
            box = detection["box"]
            pt1, pt2 = (box[0], box[1]), (box[2], box[3])
            pt3 = ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
            # Draw the bounding box and text on the image
            class_id = class_ids[detection["class"]]
            color = tuple(int(c) for c in colormap[class_id])
            cv2.rectangle(self.segmented_image, pt1, pt2, color, 2)
            cv2.putText(self.segmented_image, str(d), pt3,
                        cv2.FONT_HERSHEY_SIMPLEX, 3, color, 2)
        yield 100, "Masked image with detections was generated successfully."

    def get_detections_metrics(self) -> dict:
        """Get the detected metrics.
        Returns:
            dict: Dictionary containing the detected metrics.
        """
        return self.detections_metrics

    def get_segmented_image(self) -> Image.Image:
        """Get the segmented image.
        Returns:
            Image.Image: Segmented image in PIL format.
        """
        return Image.fromarray(self.segmented_image)


if __name__ == "__main__":
    # Sample usage
    image_path = os.path.join(os.getenv(
        "HOME"), "sae-sam/full_train_set/train/images/snp0206251005_png.rf.a8bbdfbc64967838a2a76b632c711c7c.jpg")
    barrier_dimensions = {"grid_width": 15.618, "grid_height": 40,
                          "collumn_width": 5.232}  # Example dimensions in meters
    undistort_m_pixel_ratio = 0.1  # Example meters per pixel ratio
    # Initialize the pipeline with the given parameters and run it
    pipeline = ApexPipeline(undistort_m_pixel_ratio=undistort_m_pixel_ratio)
    pipeline.set_barrier_dimensions(barrier_dimensions=barrier_dimensions)
    for state in pipeline.run(image_path=image_path):
        print(f"Progress: {state[0]}%, Status: {state[1]}")
    # Show segmented image
    pipeline.get_segmented_image().show()
