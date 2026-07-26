from PySide6.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt


class DocumentStatsBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QStatusBar {
                background-color: #161b22;
                color: #8b949e;
                font-size: 12px;
                border-top: 1px solid #30363d;
            }
            QLabel {
                color: #8b949e;
                padding: 0 8px;
            }
        """)

        self.lines_label = QLabel("Lines: 0")
        self.words_label = QLabel("Words: 0")
        self.chars_label = QLabel("Chars: 0")
        self.reading_time_label = QLabel("Read: 0 min")
        self.file_info_label = QLabel("UTF-8 | Markdown")
        self.mode_label = QLabel("Mode: Reader")

        self.addPermanentWidget(self.lines_label)
        self.addPermanentWidget(self.words_label)
        self.addPermanentWidget(self.chars_label)
        self.addPermanentWidget(self.reading_time_label)
        self.addPermanentWidget(self.file_info_label)
        self.addPermanentWidget(self.mode_label)

    def update_stats(self, stats: dict):
        self.lines_label.setText(f"Lines: {stats.get('lines', 0)}")
        self.words_label.setText(f"Words: {stats.get('words', 0)}")
        self.chars_label.setText(f"Chars: {stats.get('chars', 0)}")
        self.reading_time_label.setText(f"Read: ~{stats.get('reading_time', 0)} min")

    def set_mode(self, mode_name: str):
        self.mode_label.setText(f"Mode: {mode_name}")
