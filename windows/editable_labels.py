from PySide6.QtWidgets import (
    QApplication, QLabel, QPushButton, QLineEdit, QWidget,
    QVBoxLayout, QFileDialog, QSizePolicy
)
from PySide6.QtGui import (
    QPixmap, QPainter, QImage, QColor, QFont, QMouseEvent, QResizeEvent
)
from PySide6.QtCore import Qt, QPoint, QPointF, QSize


DEFAULT_FONT = QFont("Arial", 14)


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
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
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
            self._drag_active = False
            if hasattr(self.parent, "scale_factor") and self.parent.scale_factor:
                # Save the relative position based on the scale factor for saving the label afterwards
                self.relative_pos = QPointF(self.pos()) / self.parent().scale_factor


class EditableImageLabel(QLabel):
    def __init__(self, parent: QWidget = None) -> None:
        """Initialize the EditableImageLabel with the given parent widget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # Image data
        self.image = None
        self.image_original_pixmap = None
        # Font and style settings
        self.setStyleSheet(
            "border: 1px solid white; background-color: rgba(0,0,0,50);")
        self.setAlignment(Qt.AlignCenter)
        self.resize(self.width() // 2, self.height() // 2)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setScaledContents(True)
        # Text labels dictionary to store text labels
        self.text_labels = dict()

    def set_image(self, image: QPixmap) -> None:
        """Set the image for the label and clear any existing text labels.

        Args:
            image (QPixmap): The image to set.
        """
        self.image_original_pixmap = image
        self.setPixmap(self.image_original_pixmap)
        self.setFixedSize(self.image_original_pixmap.size())

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
        input_field.resize(150, 30)
        input_field.setFocus()
        # Internal function to finalize the text input and create a label
        # when the user presses Enter
        def finalize():
            text = input_field.text().strip()
            if text:
                label = DraggableTextLabel(text, self)
                label.move(input_field.pos())
                label.relative_pos = input_field.pos()
                label.show()
                self.text_labels[text] = label
            input_field.deleteLater()
        # Connect the returnPressed signal to finalize the input
        input_field.returnPressed.connect(finalize)
        input_field.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_original_pixmap:
            scaled = self.image_original_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled)

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
