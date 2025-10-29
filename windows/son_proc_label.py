from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QKeyEvent,
    QMouseEvent, QPaintEvent, QResizeEvent
)
from PySide6.QtCore import Qt, QRect, QPoint


class SonProcLabel(QLabel):
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
        self.pixmap_original = None

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """
        Store the pixmap and show it in the label.

        Args:
            pixmap (QPixmap): Pixmap to set.
        """
        self.pixmap_original = pixmap
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        super().setPixmap(scaled_pixmap)

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
        if self.pixmap_original and not self._start_point.isNull() and not self._end_point.isNull():
            rect = self.get_selection_rect()
            scaled_rect = self._scale_rect_to_pixmap(rect)
            return self.pixmap_original.copy(scaled_rect)
        return QPixmap()

    def _scale_rect_to_pixmap(self, rect: QRect) -> QRect:
        """
        Convert the selection rect from label coordinates to pixmap coordinates.

        Args:
            rect (QRect): Rectangle in label

        Returns:
            QRect: Rectangle in pixmap coordinates.
        """
        if not self.pixmap_original:
            return rect
        pixmap_size = self.pixmap_original.size()
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
            pixmap = self.pixmap_original.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(pixmap)
        super().resizeEvent(event)
