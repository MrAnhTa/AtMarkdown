import os
from pathlib import Path
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter


class DocumentExporter:
    @staticmethod
    def export_html(html_content: str, output_path: str) -> bool:
        """Exports HTML string to a standalone file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return True
        except Exception as e:
            print(f"Failed to export HTML: {e}")
            return False

    @staticmethod
    def export_pdf(html_content: str, output_path: str) -> bool:
        """Exports rendered HTML to PDF using Qt document printing."""
        try:
            doc = QTextDocument()
            doc.setHtml(html_content)
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(output_path)
            
            doc.print_(printer)
            return True
        except Exception as e:
            print(f"Failed to export PDF: {e}")
            return False
