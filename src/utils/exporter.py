from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
from src.ui.viewer import MarkdownViewer


class PdfExportJob(QObject):
    finished = Signal(bool, str)

    def __init__(self, html_content, output_path, parent=None):
        super().__init__(parent)
        self.output_path = output_path
        self.viewer = MarkdownViewer()
        self.viewer.resize(900, 1000)
        self.viewer.ready.connect(self._print)
        self.viewer.render_failed.connect(lambda error: self._finish(False, error))
        self.viewer.page().pdfPrintingFinished.connect(self._printed)
        self._done = False
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(lambda: self._finish(False, "PDF export timed out."))
        self._timeout.start(60000)
        self.viewer.set_html_content(html_content)

    def _print(self):
        layout = QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait,
                             QMarginsF(15, 12, 15, 15), QPageLayout.Unit.Millimeter)
        self.viewer.page().printToPdf(str(Path(self.output_path).resolve()), layout)

    def _printed(self, path, success):
        self._finish(success, path if success else f"Could not write PDF: {path}")

    def _finish(self, success, message):
        if self._done:
            return
        self._done = True
        self._timeout.stop()
        self.finished.emit(success, message)
        self.viewer.deleteLater()
        self.deleteLater()


class DocumentExporter:
    @staticmethod
    def export_html(html_content, output_path):
        Path(output_path).write_text(html_content, encoding="utf-8")
        return True

    @staticmethod
    def export_pdf(html_content, output_path, parent=None):
        """Return an asynchronous job; keep it alive until finished."""
        return PdfExportJob(html_content, output_path, parent)
