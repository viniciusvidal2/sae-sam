from ultralytics import YOLO
import os
from typing import Tuple
from PIL import Image
import numpy as np


class ImageSegmentation:
    def __init__(self, model_path: str):
        """This class is used to perform image segmentation using a YOLOv11 model.

        Args:
            model_path (str): path to the trained YOLOv11 model
        """
        self.model = YOLO(model_path)
        self.detections_by_class_dict = dict()
        self.image_detections_mask = None  # All the classes for each pixel
        # Class codes from the model, can be used in other modules
        self.image_class_mask_codes = dict()
        self.image_class_mask_codes["background"] = 0

    def segment_classes(self, image_path: str) -> bool:
        """Predicts the segmentation masks, classes and boxes for the given image.

        Args:
            image_path (str): path to the image

        Returns:
            bool: True if masks and boxes were detected, False otherwise
        """
        # Load the image to get the dimensions
        image = Image.open(image_path)
        image_width, image_height = image.size
        # If image is not 640x640, resize it
        if image_width != 640 or image_height != 640:
            image = image.resize((640, 640), Image.Resampling.LANCZOS)
            image_width, image_height = image.size

        # Initialize the global mask
        self.image_detections_mask = np.zeros(
            (image_height, image_width), dtype=np.uint8)

        # Predict detections in the image
        results = self.model.predict(source=image, show=False, save=False, conf=0.2,
                                     line_width=1, save_crop=False, save_txt=False,
                                     show_labels=False, show_conf=False)

        # Check if the model has detected any masks or boxes
        if results[0].masks is None or results[0].boxes is None:
            print("No masks or boxes detected.")
            return False

        # Build the class codes dictionary from the names
        for i, name in enumerate(results[0].names.values()):
            self.image_class_mask_codes[name] = i + 1

        # Iterate through the results and store the masks, boxes and confidences
        for result in results:
            for i in range(len(result.boxes)):
                # Extract info
                box = result.boxes[i].xyxy[0].tolist()
                conf = result.boxes[i].conf[0].item()
                mask = result.masks.data[i].cpu().numpy()

                # Store in dictionary
                cls_id = int(result.boxes[i].cls[0].item())
                class_name = result.names[cls_id]
                if class_name not in self.detections_by_class_dict:
                    self.detections_by_class_dict[class_name] = {
                        "masks": [], "boxes": [], "confidences": []}
                self.detections_by_class_dict[class_name]["masks"].append(mask)
                self.detections_by_class_dict[class_name]["boxes"].append(box)
                self.detections_by_class_dict[class_name]["confidences"].append(
                    conf)

                # Save the mask in the global mask with the proper detection code
                self.draw_detection_in_global_mask(mask, class_name)
        return True

    def draw_detection_in_global_mask(self, mask: np.ndarray, class_name: str) -> None:
        """Draws a single detection in the global mask.
        Args:
            mask (np.ndarray): mask of the detection
            class_name (str): name of the class
        """
        mask_region = mask.astype(bool)
        class_code = self.image_class_mask_codes[class_name]
        for i in range(mask.shape[0]):
            for j in range(mask.shape[1]):
                # If the pixel is already marked as sedimento or macrofita, skip it
                if self.image_detections_mask[i, j] == self.image_class_mask_codes["sedimento"] or self.image_detections_mask[i, j] == self.image_class_mask_codes["macrofita"]:
                    continue
                # If the pixel is part of the mask, set it to the class code
                if mask_region[i, j]:
                    self.image_detections_mask[i, j] = class_code

    def get_detections_by_class(self, class_name: str) -> Tuple[list, list, list]:
        """Returns the detections for a specific class.

        Args:
            class_name (str): name of the class

        Returns:
            Tuple[list, list, list]: masks, boxes and confidences for the specified class
        """
        if class_name in self.detections_by_class_dict:
            masks = self.detections_by_class_dict[class_name]["masks"]
            boxes = self.detections_by_class_dict[class_name]["boxes"]
            confidences = self.detections_by_class_dict[class_name]["confidences"]
            return masks, boxes, confidences
        else:
            print(f"No detections found for class: {class_name}")
            return [], [], []

    def get_detections_codes(self) -> dict:
        """Returns the class codes dictionary.

        Returns:
            dict: class codes dictionary
        """
        return self.image_class_mask_codes

    def get_detections_mask(self) -> np.ndarray:
        """Returns the global detections mask.

        Returns:
            np.ndarray: global detections mask
        """
        return self.image_detections_mask

    def reset_detections(self) -> None:
        """Resets the detections dictionary.
        """
        self.detections_by_class_dict = dict()
        self.image_class_mask_codes = dict()
        self.image_class_mask_codes["background"] = 0
        self.image_detections_mask = None


if __name__ == "__main__":
    # Sample usage
    model_path = "runs/segment/train_colunas/weights/best.pt"
    image_path = "/home/vini/yolo/full_train_set/train/images/snp0206251005_png.rf.a8bbdfbc64967838a2a76b632c711c7c.jpg"

    segmentation_model = ImageSegmentation(model_path)
    if segmentation_model.segment_classes(image_path):
        class_name = "sedimento"
        masks, boxes, confidences = segmentation_model.get_detections_by_class(
            class_name)
        print(f"Detected {len(boxes)} boxes for class {class_name}.")
        print(f"Detected {len(masks)} masks for class {class_name}.")
        print(f"Confidences: {confidences}")
        # Get the class codes
        class_codes = segmentation_model.get_detections_codes()
        print(f"Class codes: {class_codes}")
        # Get the global detections mask
        classes_mask = segmentation_model.get_detections_mask().astype(np.float32)
        # Convert the mask to PIL, apply scale to 255 and show
        mask_image_pil = Image.fromarray(
            (classes_mask * 255/np.max(classes_mask)).astype(np.uint8))
        mask_image_pil.show()
        # Optionally, reset detections
        segmentation_model.reset_detections()
    else:
        print("Failed to find detections in the image.")
