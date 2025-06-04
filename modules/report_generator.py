from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QBuffer, QIODevice
from io import BytesIO
from datetime import datetime


class ReportGenerator:
    def __init__(self) -> None:
        """Constructor for the ReportGenerator class.
        """
        self.styles = getSampleStyleSheet()
        self.story = []

    def set_data(self, data: dict) -> None:
        """Set the data for the report.

        Args:
            data (dict): The data to be included in the report.
        """
        self.data = data

    def set_output_path(self, output_path: str) -> None:
        """Set the output path for the report.

        Args:
            output_path (str): The path where the report will be saved.
        """
        self.output_path = output_path

    def build_report(self) -> str:
        """Build the report using the provided data and output path.

        Returns:
            str: The message with the process result.
        """
        try:
            # Adding the header information
            self.add_title(
                "Relatório de análises métricas de imagem do sonar Apex")
            self.add_paragraph(
                f"Imagem de inferência: {self.data.get('image_name', 'N/A')}")
            self.add_paragraph(
                f"Data de execução: {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
            self.add_paragraph(
                f"Modelo utilizado: {self.data.get('model_name', 'N/A')}")
            # Adding images section
            self.add_subtitle("Imagem original", level=1)
            self.add_image(self.qpixmap_to_bytesio(
                self.data.get("original_image")))
            self.add_subtitle("Imagem segmentada")
            self.add_image(self.qpixmap_to_bytesio(
                self.data.get("segmented_image")))
            # Adding the metrics
            self.add_subtitle("Valores de métricas por detecção", level=1)
            metrics = self.data.get("metrics", ())
            metrics_per_detection = metrics[0]
            for i, detection in enumerate(metrics_per_detection):
                self.add_item(f"Número: {i}")
                self.add_item(
                    f"Tipo de detecção: {detection.get('class', 'N/A')}")
                self.add_item(f"Área: {detection.get('area', 'N/A')}")
                self.add_item(f"Volume: {detection.get('volume', 'N/A')}")
                self.story.append(Spacer(1, 0.2 * inch))
            self.add_subtitle("Valores de métricas por classe", level=1)
            metrics_per_class = metrics[1]
            for class_key, class_metrics in metrics_per_class.items():
                self.add_item(f"Classe de detecção: {class_key}")
                self.add_item(f"Área: {class_metrics.get('area', 'N/A')}")
                self.add_item(f"Volume: {class_metrics.get('volume', 'N/A')}")
                self.story.append(Spacer(1, 0.2 * inch))
            # Saving the report
            self.save_pdf()
            return f"Report saved to {self.output_path}"
        except Exception as e:
            return f"Error generating report: {str(e)}"

    def add_title(self, text: str) -> None:
        """Add a title to the report.

        Args:
            text (str): The title text.
        """
        self.story.append(
            Paragraph(f"<b><font size=18>{text}</font></b>", self.styles["Title"]))
        self.story.append(Spacer(1, 0.2 * inch))

    def add_subtitle(self, text: str, level: int = 1) -> None:
        """Add a subtitle to the report.

        Args:
            text (str): The subtitle text.
            level (int): The level of the subtitle (1 for Heading2, 2 for Heading3).
        """
        if level == 1:
            self.story.append(
                Paragraph(f"<b><font size=16>{text}</font></b>", self.styles["Heading2"]))
        elif level == 2:
            self.story.append(
                Paragraph(f"<b><font size=14>{text}</font></b>", self.styles["Heading3"]))
        self.story.append(Spacer(1, 0.2 * inch))

    def add_paragraph(self, text: str) -> None:
        """Add a paragraph to the report.

        Args:
            text (str): The paragraph text.
        """
        self.story.append(Paragraph(text, self.styles["BodyText"]))
        self.story.append(Spacer(1, 0.1 * inch))

    def add_item(self, text: str) -> None:
        """Add an item to the report.

        Args:
            text (str): The item text.
        """
        self.story.append(Paragraph(text, self.styles["BodyText"]))
        self.story.append(Spacer(1, 0.01 * inch))

    def add_image(self, image_bytes: BytesIO) -> None:
        """Add an image to the report.

        Args:
            image_bytes (BytesIO): The image data in bytes.
        """
        self.story.append(Image(image_bytes, width=4*inch, height=3*inch))
        self.story.append(Spacer(1, 0.2 * inch))

    def save_pdf(self) -> None:
        """Save the report as a PDF file.
        """
        doc = SimpleDocTemplate(self.output_path, pagesize=A4)
        doc.build(self.story)

    def qpixmap_to_bytesio(self, pixmap: QPixmap) -> BytesIO:
        """Convert a QPixmap to a BytesIO object.

        Args:
            pixmap (QPixmap): The QPixmap to convert.

        Returns:
            BytesIO: The converted image data.
        """
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        data = buffer.data()
        return BytesIO(data)
