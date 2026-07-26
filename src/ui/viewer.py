from PySide6.QtWidgets import QTextBrowser
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl, Signal, Qt
import os


class MarkdownViewer(QTextBrowser):
    link_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setOpenLinks(True)
        self.setStyleSheet("""
            QTextBrowser {
                background-color: #0d1117;
                color: #c9d1d9;
                border: none;
                padding: 12px;
            }
        """)
        self.anchorClicked.connect(self._on_anchor_clicked)

    def set_html_content(self, html_content: str, base_url_path: str = None):
        """Sets HTML content and resolves relative image/link paths."""
        if base_url_path and os.path.exists(base_url_path):
            base_dir = os.path.dirname(os.path.abspath(base_url_path))
            url = QUrl.fromLocalFile(base_dir + "/")
            self.setSearchPaths([base_dir])
            self.setHtml(html_content)
        else:
            self.setHtml(html_content)

    def _on_anchor_clicked(self, url: QUrl):
        url_str = url.toString()
        if url_str.startswith("#"):
            # Internal TOC anchor scroll
            self.scrollToAnchor(url_str[1:])
        elif url.scheme() in ("http", "https", "mailto"):
            QDesktopServices.openUrl(url)

    def scroll_to_heading(self, anchor_id: str):
        """Scroll preview to matching heading anchor ID."""
        self.scrollToAnchor(anchor_id)

    def apply_theme(self, theme: str = "dark"):
        if theme == "light":
            self.setStyleSheet("""
                QTextBrowser {
                    background-color: #ffffff;
                    color: #24292f;
                    border: none;
                    padding: 12px;
                }
                QScrollBar:vertical {
                    background: #ffffff;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #d0d7de;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #8c959f;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar:horizontal {
                    background: #ffffff;
                    height: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background: #d0d7de;
                    min-width: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #8c959f;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
            """)
        elif theme == "sepia":
            self.setStyleSheet("""
                QTextBrowser {
                    background-color: #fbf0d9;
                    color: #5f4b32;
                    border: none;
                    padding: 12px;
                }
                QScrollBar:vertical {
                    background: #fbf0d9;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #d5c3a3;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #b8a37e;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar:horizontal {
                    background: #fbf0d9;
                    height: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background: #d5c3a3;
                    min-width: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #b8a37e;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QTextBrowser {
                    background-color: #0d1117;
                    color: #c9d1d9;
                    border: none;
                    padding: 12px;
                }
                QScrollBar:vertical {
                    background: #0d1117;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #30363d;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #484f58;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar:horizontal {
                    background: #0d1117;
                    height: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background: #30363d;
                    min-width: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #484f58;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
            """)
