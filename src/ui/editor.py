from PySide6.QtWidgets import (
    QWidget, QPlainTextEdit, QTextEdit, QHBoxLayout, QVBoxLayout,
    QLineEdit, QPushButton, QLabel
)
from PySide6.QtGui import (
    QPainter, QColor, QTextFormat, QKeySequence, QTextCursor,
    QFont, QIcon, QShortcut
)
from PySide6.QtCore import QSize, Qt, Signal, QRect


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class MarkdownEditor(QPlainTextEdit):
    text_modified = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        font = QFont("Cascadia Code", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setTabStopDistance(20)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.apply_theme("dark")
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def apply_theme(self, theme: str = "dark"):
        if theme == "light":
            self.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #ffffff;
                    color: #24292f;
                    selection-background-color: #0969da;
                    selection-color: #ffffff;
                    border: none;
                }
            """)
            self.line_bg = QColor("#f6f8fa")
            self.line_fg = QColor("#57606a")
            self.active_line_bg = QColor("#f0f4f8")
        elif theme == "sepia":
            self.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #fbf0d9;
                    color: #5f4b32;
                    selection-background-color: #924500;
                    selection-color: #ffffff;
                    border: none;
                }
            """)
            self.line_bg = QColor("#f2e3c6")
            self.line_fg = QColor("#7f6a4e")
            self.active_line_bg = QColor("#e8d9bc")
        else:
            self.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #0d1117;
                    color: #c9d1d9;
                    selection-background-color: #1f6feb;
                    selection-color: #ffffff;
                    border: none;
                }
            """)
            self.line_bg = QColor("#161b22")
            self.line_fg = QColor("#8b949e")
            self.active_line_bg = QColor("#1c2128")
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        if not hasattr(self, 'active_line_bg'):
            return
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.active_line_bg)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), self.line_bg)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(self.line_fg)
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def insert_formatting(self, prefix: str, suffix: str):
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            # Move cursor back inside if suffix exists
            if suffix:
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(suffix))
                self.setTextCursor(cursor)
        self.setFocus()


class EditorSearchPanel(QWidget):
    def __init__(self, editor: MarkdownEditor, parent=None):
        super().__init__(parent)
        self.editor = editor

        self.setStyleSheet("""
            QWidget {
                background-color: #161b22;
                color: #c9d1d9;
                border-top: 1px solid #30363d;
            }
            QLineEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.search_text)
        self.search_input.returnPressed.connect(self.search_next)

        self.prev_btn = QPushButton("▲ Prev")
        self.prev_btn.clicked.connect(self.search_prev)

        self.next_btn = QPushButton("▼ Next")
        self.next_btn.clicked.connect(self.search_next)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedWidth(24)
        self.close_btn.clicked.connect(self.hide)

        layout.addWidget(QLabel("Find:"))
        layout.addWidget(self.search_input)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.close_btn)

        self.hide()

    def search_text(self, text: str):
        if not text:
            return
        cursor = self.editor.textCursor()
        cursor.setPosition(0)
        self.editor.setTextCursor(cursor)
        self.search_next()

    def search_next(self):
        text = self.search_input.text()
        if not text:
            return
        found = self.editor.find(text)
        if not found:
            # Wrap around to start
            cursor = self.editor.textCursor()
            cursor.setPosition(0)
            self.editor.setTextCursor(cursor)
            self.editor.find(text)

    def search_prev(self):
        text = self.search_input.text()
        if not text:
            return
        found = self.editor.find(text, QPlainTextEdit.FindFlag.FindBackward)
        if not found:
            # Wrap around to end
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.editor.setTextCursor(cursor)
            self.editor.find(text, QPlainTextEdit.FindFlag.FindBackward)
