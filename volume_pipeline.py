import numpy as np
import os
from PIL import Image
from modules.image_rectification import ImageRectification
from modules.image_segmentation import ImageSegmentation
from modules.volume_estimation import VolumeEstimation


def volume_pipe():
    # Set the parameters
    seg_model_path = "runs/segment/train_colunas/weights/best.pt"
    image_path = os.path.join(os.getenv("HOME"), "yolo/full_train_set/train/images/snp0206251005_png.rf.a8bbdfbc64967838a2a76b632c711c7c.jpg")
    grid_width_m = 10
    collumn_width_m = 3
    meters_pixel_ratio = 0.1

    # Read image into numpy array
    image = np.array(Image.open(image_path))

    # Lets segment the image to find the collumns
    image_segmentation = ImageSegmentation(model_path=seg_model_path)
    collumn_boxes = []
    if image_segmentation.segment_classes(image=image):
        _, collumn_boxes, _ = image_segmentation.get_detections_by_class(class_name="coluna")
    else:
        raise ValueError("Failed to find detections in the image.")
    
    # Now lets rectify the image
    image_rectification = ImageRectification(
        grid_width_m=grid_width_m, collumn_width_m=collumn_width_m, meters_pixel_ratio=meters_pixel_ratio)
    image_rectification.set_detected_boxes(collumn_boxes=collumn_boxes)
    rectified_image = image_rectification.snip_rectify_image(image=image)

    # Lets estimate the volume of the macrofitas
    class_ids = image_segmentation.get_detections_codes()
    image_segmentation.reset_detections()
    volume_estimation = VolumeEstimation(
        model_name="xingyang1/Distill-Any-Depth-Large-hf", m_per_pixel=meters_pixel_ratio, class_ids=class_ids)
    if image_segmentation.segment_classes(image=rectified_image):
        rectified_image_resized = image_segmentation.get_resized_image()
        # Get the global mask and macrofitas boxes
        global_classes_mask = image_segmentation.get_detections_mask()  # This mask has proper IDs
        _, macrofitas_boxes, _ = image_segmentation.get_detections_by_class(class_name="macrofita")
        if not macrofitas_boxes:
            raise ValueError("Failed to find macrofitas in the image.")
        for box in macrofitas_boxes:
            # box = macrofitas_boxes[0]
            # Estimate the volume of each macrofita group
            volume = volume_estimation.estimate_blocking_volume(
                image=rectified_image_resized, box=box, mask=global_classes_mask, class_name="macrofita", debug=True)
            print(f"Estimated volume: {volume} m^3")


if __name__ == "__main__":
    volume_pipe()
