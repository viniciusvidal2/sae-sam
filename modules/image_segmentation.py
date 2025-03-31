from ultralytics import YOLO
import os
from typing import Tuple


class ImageSegmentation:
    def __init__(self, model_path: str):
        """This class is used to perform image segmentation using a YOLOv11 model.

        Args:
            model_path (str): path to the trained YOLOv11 model
        """
        self.model = YOLO(model_path)
        self.detections_by_class_dict = dict()

    def segment_classes(self, image_path: str) -> bool:
        """Predicts the segmentation masks, classes and boxes for the given image.

        Args:
            image_path (str): path to the image

        Returns:
            bool: True if masks and boxes were detected, False otherwise
        """
        # Predict detections in the image
        results = self.model.predict(source=image_path, show=True, save=False, conf=0.2,
                                     line_width=1, save_crop=False, save_txt=False,
                                     show_labels=True, show_conf=True)

        # Check if the model has detected any masks or boxes
        if results[0].masks is None or results[0].boxes is None:
            print("No masks or boxes detected.")
            return False

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
        return True

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

    def reset_detections(self) -> None:
        """Resets the detections dictionary.
        """
        self.detections_by_class_dict = dict()


if __name__ == "__main__":
    # Sample usage
    model_path = "runs/segment/train2/weights/best.pt"
    image_path = "/home/grin/yolo/full_train_set/train/images/snp0206251005_png.rf.a8bbdfbc64967838a2a76b632c711c7c.jpg"

    segmentation_model = ImageSegmentation(model_path)
    if segmentation_model.segment_classes(image_path):
        class_name = "sedimento"
        masks, boxes, confidences = segmentation_model.get_detections_by_class(class_name)
        print(f"Detected {len(boxes)} boxes for class {class_name}.")
        print(f"Detected {len(masks)} masks for class {class_name}.")
        print(f"Confidences: {confidences}")
        # Optionally, reset detections
        segmentation_model.reset_detections()
    else:
        print("Failed to find detections in the image.")
