import numpy as np
import os
from PIL import Image
from modules.image_rectification import ImageRectification
from modules.image_segmentation import ImageSegmentation
from modules.volume_estimation import VolumeEstimation


def volume_pipe():
    # Set the parameters
    seg_model_path = "runs/segment/train_colunas/weights/best.pt"
    image_path = "/home/vini/yolo/full_train_set/train/images/snp0206251005_png.rf.a8bbdfbc64967838a2a76b632c711c7c.jpg"
    grid_width_m = 10
    collumn_width_m = 3
    meters_pixel_ratio = 0.1

    # Read image into numpy array
    image = np.array(Image.open(image_path))

    # Lets segment the image to find the collumns
    image_segmentation = ImageSegmentation(model_path=seg_model_path)
    collumn_boxes = []
    if image_segmentation.segment_classes(image=image):
        _, collumn_boxes, _ = image_segmentation.get_detections_by_class(class_name="colunas")
    else:
        raise ValueError("Failed to find detections in the image.")
    
    # Now lets rectify the image
    image_rectification = ImageRectification(
        grid_width_m=grid_width_m, collumn_width_m=collumn_width_m, meters_pixel_ratio=meters_pixel_ratio)
    image_rectification.set_detected_boxes(collumn_boxes=collumn_boxes)
    rectified_image = image_rectification.snip_rectify_image(image=image)
    Image.fromarray(rectified_image).show()


if __name__ == "__main__":
    volume_pipe()
