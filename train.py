from ultralytics import YOLO
from ultralytics.utils import SETTINGS
import os


def main():
    # Load YOLOv11 model
    print("Loading YOLOv11 model for segmentation task...")
    yolo = YOLO("yolo11m-seg.pt", verbose=False)

    # Set the dataset subfolder in the settings
    dataset_subfolder = "full_train_set"
    SETTINGS['datasets_dir'] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), dataset_subfolder)
    print(f"Dataset subfolder set to: {SETTINGS['datasets_dir']}")

    # Train the model
    print("Training YOLOv11 model with the training set...")
    data_path = os.path.join(dataset_subfolder, "data.yaml")
    results = yolo.train(data=data_path, epochs=100,
                         batch=16, device="cpu", optimizer="adam", patience=0, lrf=0.001)

    # Try in a test image
    print("Predicting a test image with the trained model...")
    test_folder = os.path.joint(dataset_subfolder, "test", "images")
    test_image = os.path.join(
        test_folder, "snp0206250246_png.rf.5ddee07dffd8452d04487e6029a61d34.jpg")
    yolo.predict(source=test_image, show=True, save=True, conf=0.70,
                 line_width=1, save_crop=False, save_txt=False,
                 show_labels=True, show_conf=True)


if __name__ == "__main__":
    main()
