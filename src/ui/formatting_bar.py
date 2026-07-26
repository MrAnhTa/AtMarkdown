from PySide6.QtWidgets import QToolBar, QToolButton
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Signal, Qt


class FormattingToolbar(QToolBar):
    # Signals for editor insertion
    format_requested = Signal(str, str)  # prefix, suffix

    def __init__(self, parent=None):
        super().__init__("Formatting", parent)
        self.setMovable(False)
        self.setStyleSheet("""
            QToolBar {
                background-color: #161b22;
                border-bottom: 1px solid #30363d;
                padding: 2px 4px;
                spacing: 4px;
            }
            QToolButton {
                background-color: transparent;
                color: #c9d1d9;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QToolButton:hover {
                background-color: #21262d;
                border-color: #30363d;
                color: #58a6ff;
            }
            QToolButton:pressed {
                background-color: #30363d;
            }
        """)

        self._create_actions()

    def _create_actions(self):
        items = [
            ("B", "Bold (Ctrl+B)", "**", "**"),
            ("I", "Italic (Ctrl+I)", "*", "*"),
            ("H1", "Heading 1", "# ", ""),
            ("H2", "Heading 2", "## ", ""),
            ("H3", "Heading 3", "### ", ""),
            ("Code", "Inline Code", "`", "`"),
            ("``` Block", "Code Block", "```python\n", "\n```"),
            ("Link", "Insert Link", "[", "](https://)"),
            ("Image", "Insert Image", "![alt](", ")"),
            ("Quote", "Blockquote", "> ", ""),
            ("List", "Unordered List", "- ", ""),
            ("Task", "Checklist", "- [ ] ", ""),
            ("Table", "Insert Table", "| Header 1 | Header 2 |\n| --- | --- |\n| Cell 1 | Cell 2 |", "")
        ]

        for label, tooltip, prefix, suffix in items:
            btn = QToolButton(self)
            btn.setText(label)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Bind closure
            btn.clicked.connect(lambda checked=False, p=prefix, s=suffix: self.format_requested.emit(p, s))
            self.addWidget(btn)
