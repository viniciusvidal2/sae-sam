from PySide6.QtWidgets import (
    QLabel, QLineEdit, QWidget, QSizePolicy
)
from PySide6.QtGui import (
    QPixmap, QPainter, QFont, QMouseEvent, QResizeEvent
)
from PySide6.QtCore import Qt, QPoint, QPointF


DEFAULT_FONT = QFont("Arial", 11)


class DraggableTextLabel(QLabel):
    def __init__(self, text: str, parent: QWidget = None) -> None:
        """Initialize the DraggableTextLabel with the given text and parent widget.

        Args:
            text (str): The text to display on the label.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(text, parent)
        # Make sure the parent is followed to access variables
        self.parent = parent
        self.label_key = text
        # Set the label's font and style
        self.setStyleSheet("color: white; background-color: transparent;")
        self.setFont(DEFAULT_FONT)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFixedSize(self.sizeHint())
        self._drag_active = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start dragging the label when the left mouse button is pressed, delete it on right click.

        Args:
            event (QMouseEvent): The mouse press event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Start dragging the label
            self._drag_active = True
            self._drag_position = event.globalPosition().toPoint() - self.pos()
        elif event.button() == Qt.MouseButton.RightButton:
            # Delete the label on right click
            if self.parent and hasattr(self.parent, "text_labels"):
                self.parent.text_labels.pop(self.label_key, None)
            self.deleteLater()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Move the label when the mouse is dragged.

        Args:
            event (QMouseEvent): The mouse move event.
        """
        if self._drag_active:
            self.move(event.globalPosition().toPoint() - self._drag_position)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop dragging the label when the mouse button is released.

        Args:
            event (QMouseEvent): The mouse release event.
        """
        if self._drag_active:
            # Save the relative position to the image size
            relative_x = self.pos().x() / self.parent.size().width()
            relative_y = self.pos().y() / self.parent.size().height()
            self.relative_pos = (relative_x, relative_y)
            self._drag_active = False


class EditableImageLabel(QLabel):
    def __init__(self, parent: QWidget = None) -> None:
        """Initialize the EditableImageLabel with the given parent widget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # Image data
        self.image_original_pixmap = None
        self.image_segmented_pixmap = None
        # Font and style settings
        self.setStyleSheet(
            "border: 1px solid white; background-color: rgba(0,0,0,50);")
        self.setAlignment(Qt.AlignCenter)
        self.resize(parent.width() // 2, parent.height() // 2)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setScaledContents(True)
        # Text labels dictionary to store text labels
        self.text_labels_original = dict()
        self.text_labels_segmented = dict()
        # The image we are displaying depending on the state
        self.image_state = "None"  # None, original, segmented

    def set_image(self, image: QPixmap, state: str) -> None:
        """Set the image for the label and clear any existing text labels.

        Args:
            image (QPixmap): The image to set.
            state (str): The state of the image ("original" or "segmented").
        """
        # Define the image based on the state
        image_scaled = image.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if state == "original":
            self.image_original_pixmap = image_scaled
        elif state == "segmented":
            self.image_segmented_pixmap = image_scaled
        self.setPixmap(image_scaled)
        # Update the image state
        self.set_image_state(state)

    def set_image_state(self, state: str) -> None:
        """Set the image state to either "original" or "segmented".

        Args:
            state (str): The state of the image ("original" or "segmented").
        """
        if state == "original":
            self.image_state = "original"
            for label in self.text_labels_original.values():
                label.show()
            for label in self.text_labels_segmented.values():
                label.hide()
        elif state == "segmented":
            self.image_state = "segmented"
            for label in self.text_labels_segmented.values():
                label.show()
            for label in self.text_labels_original.values():
                label.hide()

    def create_text_input(self, position: QPoint) -> None:
        """Create a text input field at the specified position.

        Args:
            position (QPoint): The position to place the text input field.
        """
        # Create a QLineEdit for text input
        input_field = QLineEdit(self)
        input_field.setFont(DEFAULT_FONT)
        input_field.setStyleSheet("color: black; background-color: white;")
        input_field.move(position)
        input_field.resize(120, 30)
        input_field.setFocus()
        # Internal function to finalize the text input and create a label
        # when the user presses Enter

        def finalize():
            text = input_field.text().strip()
            if text:
                label = DraggableTextLabel(text, self)
                label.move(input_field.pos())
                # Save relative position of the label
                label_pos = input_field.pos()
                parent_size = self.size()
                relative_x = label_pos.x() / parent_size.width()
                relative_y = label_pos.y() / parent_size.height()
                label.relative_pos = (relative_x, relative_y)
                label.show()
                # Store the label in the appropriate dictionary based on the image state
                if self.image_state == "original":
                    self.text_labels_original[text] = label
                elif self.image_state == "segmented":
                    self.text_labels_segmented[text] = label
            input_field.deleteLater()
        # Connect the returnPressed signal to finalize the input
        input_field.returnPressed.connect(finalize)
        input_field.show()

    def get_painted_image(self, state: str) -> QPixmap:
        """Export the image with text labels to a file.

        Args:
            state (str): The state of the image ("original" or "segmented").

        Returns:
            QPixmap: The painted image with text labels.
        """
        # Choose the image and labels based on the state
        if state == "original":
            if not self.image_original_pixmap:
                return
            painted_image = self.image_original_pixmap.copy()
            text_labels = self.text_labels_original
        elif state == "segmented":
            if not self.image_segmented_pixmap:
                return
            painted_image = self.image_segmented_pixmap.copy()
            text_labels = self.text_labels_segmented
        # Get the copy of the desired panel image and paint the text labels in it
        painter = QPainter(painted_image)
        for label in text_labels.values():
            image_pos = QPointF(
                label.relative_pos[0] * painted_image.width(), label.relative_pos[1] * painted_image.height())
            painter.setFont(label.font())
            painter.setPen("white")
            painter.drawText(image_pos, label.text())
        painter.end()
        return painted_image

    def rescaleEvent(self, event: QResizeEvent) -> None:
        """Handle resize events to adjust the label size.

        Args:
            event (QResizeEvent): The resize event.
        """
        super().resizeEvent(event)
        if self.image_original_pixmap:
            # Resize the label to fit the image
            self.image_original_pixmap = self.image_original_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_segmented_pixmap = self.image_segmented_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        # Update the label's pixmap to the resized image
        if self.image_state == "original":
            self.setPixmap(self.image_original_pixmap)
        elif self.image_state == "segmented":
            self.setPixmap(self.image_segmented_pixmap)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Handle double-click events to create a text input field.

        Args:
            event (QMouseEvent): The mouse double-click event.
        """
        if not self.image_original_pixmap:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            # Create a text input field at the clicked position
            position = event.position().toPoint()
            self.create_text_input(position)
