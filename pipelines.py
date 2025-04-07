import numpy as np
import os
from PIL import Image
from modules.image_rectification import ImageRectification
from modules.image_segmentation import ImageSegmentation
from modules.metrics_estimation import MetricsEstimation


def run_metrics_pipeline(image_path: str, barrier_dimensions: dict, undistort_m_pixel_ratio: float):
    """Run the desired pipeline with the given parameters.
    Args:
        image_path (str): Path to the image.
        barrier_dimensions (dict): Dictionary containing the grid and collumn dimensions in meters.
        undistort_m_pixel_ratio (float): Ratio of meters per pixel in the width direction for undistortion.
    """
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
        barrier_dimensions=barrier_dimensions, undistort_meters_pixel_ratio=undistort_m_pixel_ratio)
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
        raise ValueError("Failed to find detections in the rectified image.")
    
    # Lets estimate the metrics
    metrics_estimation = MetricsEstimation(
        model_name="xingyang1/Distill-Any-Depth-Large-hf", m_per_pixel=meter_pixel_ratios, class_ids=class_ids)
    desired_classes = ["macrofita", "sedimento"]
    for desired_class in desired_classes:
        # Get the global mask and macrofitas boxes
        boxes, _ = image_segmentation.get_detections_by_class(
            class_name=desired_class)
        if not boxes:
            raise ValueError("Failed to find macrofitas in the image.")
        for box in boxes:
            # Estimate the volume of each macrofita group
            print(f"Class: {desired_class}")
            area, volume = metrics_estimation.estimate_blocking_area_volume(
                image=rectified_image, box=box, mask=rectified_global_classes_mask, class_name=desired_class, debug=False)
            print(f"Estimated area: {area} m^2")
            print(f"Estimated volume: {volume} m^3")


if __name__ == "__main__":
    # Sample usage
    image_path = os.path.join(os.getenv(
        "HOME"), "yolo/full_train_set/train/images/snp0206251005_png.rf.a8bbdfbc64967838a2a76b632c711c7c.jpg")
    barrier_dimensions = {"grid_width": 10, "grid_height": 40, "collumn_width": 3}  # Example dimensions in meters
    undistort_m_pixel_ratio = 0.1  # Example meters per pixel ratio
    run_metrics_pipeline(image_path, barrier_dimensions, undistort_m_pixel_ratio)
