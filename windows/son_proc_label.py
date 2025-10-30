import os
import numpy as np
import cv2
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QKeyEvent,
    QMouseEvent, QPaintEvent, QResizeEvent, QImage
)
from PySide6.QtCore import Qt, QRect, QPoint


class SonProcLabel(QLabel):
    # region Constructor
    """Dealing with sonogram image display and processing.

    Args:
        QLabel: QLabel subclass for displaying and processing sonogram images.
    """

    def __init__(self, parent: QLabel = None) -> None:
        """
        Class constructor

        Args:
            parent (QLabel, optional): Parent label. Defaults to None.
        """
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self._start_point = QPoint()
        self._end_point = QPoint()
        self._is_selecting = False
        self._is_crop_mode = False
        self.pixmap_current_displayed = None
        # Image control variables
        self.AVAILABLE_FILTERS = ["contrast", "brightness", "gamma",
                                  "sharpness", "saturation", "clahe", 
                                  "detail_enhancement", "crop"]
        self.filters_state = {"last_filter": None, "current_filter": None}
        self.image_original = None
        self.image_current = None
        self.image_filter_base = None
        self.image_filter_base_history = []

    # endregion
    # region Pixmap Methods

    def set_pixmap_from_path(self, image_path: str) -> None:
        """
        Load an image from the given path and set it as the pixmap.

        Args:
            image_path (str): Path to the image file.
        """
        self.image_original = cv2.imread(image_path)
        self.image_current = self.image_original.copy()
        self.image_filter_base = self.image_original.copy()
        self.image_filter_base_history = []
        self.set_pixmap(self.numpy_to_qpixmap(self.image_current))

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """
        Store the pixmap and show it in the label.

        Args:
            pixmap (QPixmap): Pixmap to set.
        """
        self.pixmap_current_displayed = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        super().setPixmap(self.pixmap_current_displayed)

    def save_current_pixmap(self, project_path: str) -> str:
        """
        Save the currently displayed pixmap to the specified path.

        Args:
            project_path (str): Path to save the image.

        Returns:
            str: Full path of the saved image.
        """
        if self.image_current is None:
            return "No image to save."
        # Check all the images in the project folder that start with 'extracted_sonogram_' and create the
        # next index, using 001 format
        snapshot_prefix = "extracted_sonogram_"
        existing_files = [f for f in os.listdir(
            project_path) if f.startswith(snapshot_prefix)]
        if existing_files:
            # Extract the highest index number from existing files
            indices = [int(f.split('_')[-1].split('.')[0])
                       for f in existing_files]
            next_index = max(indices) + 1
        else:
            next_index = 1
        # Save the current image, with its full resolution
        cv2.imwrite(
            f"{project_path}/{snapshot_prefix}{next_index:03d}.png", self.image_current)
        return f"Image saved at: {project_path}/{snapshot_prefix}{next_index:03d}.png"

    # endregion
    # region Crop Selection Methods

    def enable_crop_mode(self, enable: bool) -> None:
        """
        Enable or disable crop selection mode.

        Args:
            enable (bool): True to enable crop mode, False to disable.
        """
        self._is_crop_mode = enable
        self.clear_selection()
        self.update()

    def clear_selection(self) -> None:
        """Remove any existing selection."""
        self._start_point = QPoint()
        self._end_point = QPoint()
        self._is_selecting = False
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Define the rectangle borders

        Args:
            event (QMouseEvent): Mouse press event.
        """
        if not self._is_crop_mode:
            return
        if event.button() == Qt.LeftButton:
            self._start_point = event.position().toPoint()
            self._end_point = self._start_point
            self._is_selecting = True
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Update the end point of the selection rectangle.

        Args:
            event (QMouseEvent): Mouse move event.
        """
        if self._is_crop_mode and self._is_selecting:
            self._end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Finalize the selection rectangle.

        Args:
            event (QMouseEvent): Mouse release event.
        """
        if self._is_crop_mode and event.button() == Qt.LeftButton:
            self._end_point = event.position().toPoint()
            self._is_selecting = False
            self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handle keyboard shortcuts: ESC clears, ENTER crops.

        Args:
            event (QKeyEvent): Key press event.
        """
        if not self._is_crop_mode:
            return
        if event.key() == Qt.Key_Escape:
            self.clear_selection()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            rect = self.crop_rectangle()
            if rect:
                # Get the cropping rectangle in scale to crop the current image
                self.image_current = self.image_current[
                    rect.y():rect.y() + rect.height(),
                    rect.x():rect.x() + rect.width()
                ]
                self.set_pixmap(self.numpy_to_qpixmap(self.image_current))
                # Update the filters state to reflect cropping
                self.filters_state["last_filter"] = self.filters_state["current_filter"]
                self.filters_state["current_filter"] = "crop"
                # Updating base image and history
                self.image_filter_base = self.image_current.copy()
                self.image_filter_base_history.append(
                    {
                        "image": self.image_filter_base,
                        "filter_name": "crop"
                    }
                )
            self.clear_selection()

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Draw the selection rectangle on top of the QLabel pixmap.

        Args:
            event (QPaintEvent): Paint event.
        """
        super().paintEvent(event)
        if not self._is_crop_mode:
            return
        if not self._start_point.isNull() and not self._end_point.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRect(self._start_point, self._end_point).normalized()
            pen = QPen(QColor(0, 150, 255), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect)

    def crop_rectangle(self) -> QRect:
        """
        Return a cropped QRect from the original image based on the selection.

        Returns:
            QRect: The scaled cropping rectangle.
        """
        if self.pixmap_current_displayed \
                and not self._start_point.isNull() and not self._end_point.isNull() \
                and self.image_current is not None:
            # Selection in label coordinates
            rect_label = QRect(self._start_point, self._end_point).normalized()
            # Get label and pixmap sizes
            label_w, label_h = self.width(), self.height()
            pixmap = self.pixmap_current_displayed
            pixmap_w, pixmap_h = pixmap.width(), pixmap.height()
            # Compute aspect ratio fit scaling
            ratio = min(label_w / pixmap_w, label_h / pixmap_h)
            scaled_w = pixmap_w * ratio
            scaled_h = pixmap_h * ratio
            # Compute offset (margins) if pixmap is centered inside the label
            offset_x = (label_w - scaled_w) / 2
            offset_y = (label_h - scaled_h) / 2
            # Adjust selection to pixmap coordinates (remove offsets)
            x_in_pixmap = (rect_label.x() - offset_x) * (pixmap_w / scaled_w)
            y_in_pixmap = (rect_label.y() - offset_y) * (pixmap_h / scaled_h)
            w_in_pixmap = rect_label.width() * (pixmap_w / scaled_w)
            h_in_pixmap = rect_label.height() * (pixmap_h / scaled_h)
            # Map to original image coordinates
            image_h, image_w = self.image_current.shape[:2]
            x_ratio = image_w / pixmap_w
            y_ratio = image_h / pixmap_h
            x0 = int(x_in_pixmap * x_ratio)
            y0 = int(y_in_pixmap * y_ratio)
            w = int(w_in_pixmap * x_ratio)
            h = int(h_in_pixmap * y_ratio)
            return QRect(x0, y0, w, h)
        return QRect()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handle resize events to scale the pixmap appropriately.

        Args:
            event: Resize event.
        """
        if self.pixmap():
            self.pixmap_current_displayed = self.pixmap_current_displayed.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(self.pixmap_current_displayed)
        super().resizeEvent(event)

    # endregion
    # region Image Conversion Utilities

    def numpy_to_qpixmap(self, cv_img: np.ndarray) -> QPixmap:
        """
        Convert a BGR OpenCV image (numpy array) to QPixmap.

        Args:
            cv_img (np.ndarray): BGR image array.

        Returns:
            QPixmap: Converted QPixmap image.
        """
        height, width, channels = cv_img.shape
        bytes_per_line = channels * width
        # Convert BGR (OpenCV) to RGB (Qt)
        cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        qimg = QImage(cv_img_rgb.data, width, height,
                      bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def qpixmap_to_numpy(self, pixmap: QPixmap) -> np.ndarray:
        """
        Convert a QPixmap to a BGR OpenCV image (numpy array).

        Args:
            pixmap (QPixmap): QPixmap image.

        Returns:
            np.ndarray: Converted BGR image array.
        """
        qimg = pixmap.toImage().convertToFormat(QImage.Format_RGB888)
        width = qimg.width()
        height = qimg.height()
        ptr = qimg.bits()
        arr = np.array(ptr, dtype=np.uint8).reshape((height, width, 3))
        # Convert RGB (Qt) → BGR (OpenCV)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    # endregion
    # region filtering methods

    def apply_filter(self, filter_name: str, value: float) -> None:
        """
        Apply a filter to the current image.

        Args:
            filter_name (str): The name of the filter to apply.
            value (float): The value to use with the filter.
        """
        if not self.pixmap_current_displayed:
            return
        if filter_name not in self.AVAILABLE_FILTERS:
            return
        # Check if we are applying the same filter, or if we must renew the base image
        if self.filters_state["current_filter"] is not None:
            if self.filters_state["current_filter"] != filter_name:
                self.image_filter_base_history.append(
                    {
                        "filter_name": self.filters_state["current_filter"],
                        "image": self.image_current.copy()
                    }
                )
                self.image_filter_base = self.image_current.copy()
        # Temp image to be filtered
        image_temp = self.image_filter_base.copy()

        # Apply each filter accordingly
        if filter_name == "contrast":
            image_temp = cv2.convertScaleAbs(
                image_temp, alpha=value, beta=0)
        elif filter_name == "brightness":
            image_temp = cv2.convertScaleAbs(
                image_temp, alpha=1, beta=value)
        elif filter_name == "gamma":
            inv_gamma = 1.0 / value
            table = np.array(
                [((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]
            ).astype("uint8")
            image_temp = cv2.LUT(image_temp, table)
        elif filter_name == "sharpness":
            blurred = cv2.GaussianBlur(image_temp, (9, 9), 0)
            high_pass = cv2.addWeighted(image_temp, 1.5, blurred, -0.5, 0)
            image_temp = cv2.addWeighted(
                image_temp, 1.0, high_pass, 0.5 * value, 0)
        elif filter_name == "saturation":
            hsv_img = cv2.cvtColor(
                image_temp, cv2.COLOR_BGR2HSV).astype("float32")
            (h, s, v) = cv2.split(hsv_img)
            s = s * value
            s = np.clip(s, 0, 255)
            hsv_img = cv2.merge([h, s, v])
            image_temp = cv2.cvtColor(
                hsv_img.astype("uint8"), cv2.COLOR_HSV2BGR)
        elif filter_name == "clahe":
            lab = cv2.cvtColor(image_temp, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=value, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            image_temp = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        elif filter_name == "detail_enhancement":
            image_temp = cv2.detailEnhance(
                image_temp, sigma_s=10, sigma_r=value)

        # Set the images after filtering and control the logic states
        self.image_current = image_temp.copy()
        self.set_pixmap(self.numpy_to_qpixmap(self.image_current))
        self.filters_state["last_filter"] = self.filters_state["current_filter"]
        self.filters_state["current_filter"] = filter_name

    def undo_last_filter(self) -> str:
        """
        Undo the last applied filter.

        Returns:
            str: Resulting message.
        """
        if self.image_filter_base_history:
            image_filter_base_data = self.image_filter_base_history.pop()
            self.image_current = image_filter_base_data["image"].copy()
            self.image_filter_base = self.image_current.copy()
            self.set_pixmap(
                self.numpy_to_qpixmap(self.image_current))
            self.filters_state["current_filter"] = image_filter_base_data["filter_name"]
            self.filters_state["last_filter"] = None
            return f"Moving back to when we were filtering {image_filter_base_data['filter_name']}."
        return "No filter to undo."
