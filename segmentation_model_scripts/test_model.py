from ultralytics import YOLO
from ultralytics.engine.results import Results
import os
from time import time
from PIL import Image
import numpy as np
from typing import Tuple


def create_colormap(classes: dict, colormap: str) -> list:
    """Creates a colormap based on the input colormap and the number of classes

    Args:
        classes (dict): input classes names
        colormap (str): colormap to create with

    Returns:
        list: RGB colors (np.ndarrays) for each class 
    """
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib import colormaps
    mock_class_intensity = np.arange(len(classes))/len(classes)
    cmap = colormaps.get_cmap(colormap)
    colors = cmap(mock_class_intensity)[:, :3] * 255
    return colors.astype(np.uint8)


def get_masks_info(inference_data: Results, conf_thresh: float) -> Tuple:
    """Get info from the detection regarding each mask image with its class and confidence, 
    as long as the confidence is high

    Args:
        inference_data (Results): full data acquired with the yolo model
        conf_thresh (float): threshold the masks that are confident enough

    Returns:
        Tuple: masks list, class id list, confidence list
    """
    # Output list
    detections_classes = []
    detections_confidence = []
    masks_images = []
    # Get each mask info
    for i, mask in enumerate(inference_data.masks.data):
        conf = inference_data.boxes.conf[i].cpu().numpy().max()
        cls_id = int(inference_data.boxes.cls[i].cpu().numpy())
        # Add the most confident ones
        if conf > conf_thresh:
            detections_classes.append(cls_id)
            detections_confidence.append(conf)
            masks_images.append(mask.cpu().numpy())

    return masks_images, detections_classes, detections_confidence


def draw_masks(img: np.ndarray, masks: np.ndarray, ids: list, colors: list, color_weight: float) -> np.ndarray:
    """Draw the masks on top of the original image

    Args:
        img (np.ndarray): original image
        masks (np.ndarray): the list of masks
        ids (list): list of class ids for each mask
        colors (list): list of colors for each class
        color_weight (float): the weight we should use to average each class color

    Returns:
        np.ndarray: the output masked image
    """
    # Output image with masks
    masked_image = img.astype(np.float32).copy()
    # Go through all the detected masks
    for class_id, mask in zip(ids, masks):
        # Region of pixels as bool values
        mask_region = mask.astype(bool)
        # Defines the colored mask with the colormap for the class
        colored_mask = np.zeros_like(masked_image)
        colored_mask[mask_region] = colors[class_id]
        # Weighted sum to draw the class mask
        masked_image[mask_region] = masked_image[mask_region] * (1 - color_weight) \
            + colored_mask[mask_region] * color_weight

    return masked_image.astype(np.uint8)


def main():
    # Load the best model from the training results
    print("Loading the best model from the training results...")
    results_folder = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "runs/segment")
    train_result_folder = "train_colunas/weights/best.pt"
    trained_model = YOLO(os.path.join(results_folder, train_result_folder))

    # Test images list for inference
    test_folder = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "../full_train_set/train/images")
    test_images = os.listdir(test_folder)

    # Try in test images
    for test_image in test_images:
        print(f"Predicting a test image: {test_image}...")
        start = time()
        results = trained_model.predict(source=os.path.join(test_folder, test_image),
                                        show=False, save=False, conf=0.6,
                                        line_width=1, save_crop=False, save_txt=False,
                                        show_labels=False, show_conf=False)
        end = time()
        print(f"Prediction time: {end-start:.2f} seconds")

        # Prevent from crashing if no masks are detected
        if results[0].masks == None:
            print("No masks detected in this image.")
            continue

        # Get a colormap based on the classes
        classes = results[0].names
        classes_colormap = create_colormap(classes=classes, colormap="viridis")

        # Get the masks with correspondent class and confidence
        masks, detected_class_ids, _ = get_masks_info(
            inference_data=results[0], conf_thresh=0.5)

        # Draw the result in an image
        img = Image.open(os.path.join(test_folder, test_image))
        masked_img = draw_masks(img=np.array(
            img), masks=masks, ids=detected_class_ids, colors=classes_colormap, color_weight=0.5)
        # Plot the image
        import matplotlib
        matplotlib.use('Qt5Agg')
        import matplotlib.pyplot as plt
        plt.imshow(masked_img)
        plt.show(block=False)
        plt.pause(2)
        plt.close()


if __name__ == "__main__":
    main()
