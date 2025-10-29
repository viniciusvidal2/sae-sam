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
                                  "sharpness", "saturation", "clahe", "detail_enhancement"]
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
        self.pixmap_current_displayed = QPixmap(image_path)
        self.image_original = cv2.imread(image_path)
        self.image_current = self.image_original.copy()
        self.image_filter_base = self.image_original.copy()
        self.image_filter_base_history = []
        self.set_pixmap(self.pixmap_current_displayed)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """
        Store the pixmap and show it in the label.

        Args:
            pixmap (QPixmap): Pixmap to set.
        """
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        super().setPixmap(scaled_pixmap)

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
            cropped = self.crop_selection()
            if cropped:
                self.set_pixmap(cropped)
            self.enable_crop_mode(False)

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

    def get_selection_rect(self) -> QRect:
        """
        Return the QRect of the selected region in label coordinates.

        Returns:
            QRect: The selection rectangle.
        """
        return QRect(self._start_point, self._end_point).normalized()

    def crop_selection(self) -> QPixmap:
        """
        Return a cropped QPixmap from the original image based on the selection.

        Returns:
            QPixmap: The cropped pixmap.
        """
        if self.pixmap_current_displayed and not self._start_point.isNull() and not self._end_point.isNull():
            rect = self.get_selection_rect()
            scaled_rect = self._scale_rect_to_pixmap(rect)
            return self.pixmap_current_displayed.copy(scaled_rect)
        return QPixmap()

    def _scale_rect_to_pixmap(self, rect: QRect) -> QRect:
        """
        Convert the selection rect from label coordinates to pixmap coordinates.

        Args:
            rect (QRect): Rectangle in label

        Returns:
            QRect: Rectangle in pixmap coordinates.
        """
        if not self.pixmap_current_displayed:
            return rect
        pixmap_size = self.pixmap_current_displayed.size()
        label_size = self.size()
        x_scale = pixmap_size.width() / label_size.width()
        y_scale = pixmap_size.height() / label_size.height()
        return QRect(
            int(rect.x() * x_scale),
            int(rect.y() * y_scale),
            int(rect.width() * x_scale),
            int(rect.height() * y_scale),
        )

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handle resize events to scale the pixmap appropriately.

        Args:
            event: Resize event.
        """
        if self.pixmap():
            pixmap = self.pixmap_current_displayed.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(pixmap)
        super().resizeEvent(event)

    # endregion
    # region Image Conversion Utilities

    def numpy_to_qpixmap(cv_img: np.ndarray) -> QPixmap:
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

    def qpixmap_to_numpy(pixmap: QPixmap) -> np.ndarray:
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
        ptr.setsize(height * width * 3)
        arr = np.array(ptr).reshape((height, width, 3))
        # Convert RGB (Qt) to BGR (OpenCV)
        cv_img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        return cv_img_bgr

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
        # Temp image to be filtered
        image_temp = self.image_filter_base.copy()
        # Check if we are applying the same filter, or must renew the base image
        if self.filters_state["current_filter"] and self.filters_state["current_filter"] == filter_name:
            if self.filters_state["current_filter"] != filter_name and filter_name in self.AVAILABLE_FILTERS:
                new_base_image_for_filtering = {
                    "filter_name": filter_name,
                    "image": self.image_current.copy()
                }
                self.image_filter_base_history.append(
                    new_base_image_for_filtering)
                self.image_filter_base = self.image_current.copy()
                image_temp = self.image_filter_base.copy()

        # Apply each filter accordingly

        # Set the images after filtering and control the logic states
        self.pixmap_current_displayed = self.numpy_to_qpixmap(image_temp)
        self.setPixmap(self.pixmap_current_displayed)
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
            self.pixmap_current_displayed = self.numpy_to_qpixmap(
                image_filter_base_data["image"])
            self.setPixmap(self.pixmap_current_displayed)
            self.filters_state["current_filter"] = image_filter_base_data["filter_name"]
            self.filters_state["last_filter"] = None
            return f"Moving back to when we were filtering {image_filter_base_data['filter_name']}."
        return "No filter to undo."
