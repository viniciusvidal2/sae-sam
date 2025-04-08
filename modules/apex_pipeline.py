import numpy as np
import os
from PIL import Image
from image_rectification import ImageRectification
from image_segmentation import ImageSegmentation
from metrics_estimation import MetricsEstimation


class ApexPipeline:
    def __init__(self, undistort_m_pixel_ratio: float) -> None:
        """Initialize the pipeline with the given parameters.
        Args:
            undistort_m_pixel_ratio (float): Ratio of meters per pixel in the width direction for undistortion.
        """
        self.undistort_m_pixel_ratio = undistort_m_pixel_ratio
        self.detections_metrics = dict()
        # Classes to keep track of metrics
        self.desired_classes = ["macrofita", "sedimento"]

    def set_barrier_dimensions(self, barrier_dimensions: dict) -> None:
        """Set the barrier dimensions for the pipeline.
        Args:
            barrier_dimensions (dict): Dictionary containing the grid and collumn dimensions in meters.
        """
        self.barrier_dimensions = barrier_dimensions

    def run(self, image_path: str) -> None:
        """Run the pipeline with the given parameters.
        Args:
            image_path (str): Path to the image.
        """
        # If there are no dimensions set yet, raise an error
        if not hasattr(self, 'barrier_dimensions'):
            raise ValueError(
                "Barrier dimensions must be set before running the pipeline.")

        # Read image into numpy array
        image = np.array(Image.open(image_path))

        # Lets segment the image to find the collumns
        seg_model_path = "runs/segment/train_colunas/weights/best.pt"
        image_segmentation = ImageSegmentation(model_path=seg_model_path)
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

        # Now lets rectify the image and the detected global mask
        image_rectification = ImageRectification(
            barrier_dimensions=self.barrier_dimensions, undistort_meters_pixel_ratio=self.undistort_m_pixel_ratio)
        image_rectification.set_detected_boxes(
            collumn_boxes=collumn_boxes, barrier_boxes=barrier_boxes)
        rectified_image = image_rectification.snip_rectify_image(image=image)
        meter_pixel_ratios = image_rectification.get_meters_pixel_ratio()

        # Perform another segmentation on the rectified image
        image_segmentation.reset_detections()
        if image_segmentation.segment_classes(image=rectified_image):
            # Get the global mask and macrofitas boxes
            rectified_global_classes_mask = image_segmentation.get_detections_mask()
        else:
            raise ValueError(
                "Failed to find detections in the rectified image.")

        # Lets estimate the metrics
        metrics_estimation = MetricsEstimation(
            model_name="xingyang1/Distill-Any-Depth-Large-hf", m_per_pixel=meter_pixel_ratios, class_ids=class_ids)
        for desired_class in self.desired_classes:
            # Get the global mask and macrofitas boxes
            boxes, _ = image_segmentation.get_detections_by_class(
                class_name=desired_class)
            if not boxes:
                raise ValueError(
                    f"Failed to find the class {desired_class} in the image.")
            for box in boxes:
                # Estimate the volume of each macrofita group
                print(f"Class: {desired_class}")
                area, volume = metrics_estimation.estimate_blocking_area_volume(
                    image=rectified_image, box=box, mask=rectified_global_classes_mask, class_name=desired_class, debug=False)
                print(f"Estimated area: {area} m^2")
                print(f"Estimated volume: {volume} m^3")
                # Add the detection metrics to the dictionary
                if not desired_class in self.detections_metrics:
                    self.detections_metrics[desired_class] = []
                self.detections_metrics[desired_class].append(
                    {"area": area, "volume": volume, "box": box})

    def get_detections_metrics(self) -> dict:
        """Get the detected metrics.
        Returns:
            dict: Dictionary containing the detected metrics.
        """
        return self.detections_metrics


if __name__ == "__main__":
    # Sample usage
    image_path = os.path.join(os.getenv(
        "HOME"), "yolo/full_train_set/train/images/snp0206251005_png.rf.a8bbdfbc64967838a2a76b632c711c7c.jpg")
    barrier_dimensions = {"grid_width": 10, "grid_height": 40,
                          "collumn_width": 3}  # Example dimensions in meters
    undistort_m_pixel_ratio = 0.1  # Example meters per pixel ratio
    # Initialize the pipeline with the given parameters and run it
    pipeline = ApexPipeline(undistort_m_pixel_ratio=undistort_m_pixel_ratio)
    pipeline.set_barrier_dimensions(barrier_dimensions=barrier_dimensions)
    pipeline.run(image_path=image_path)
