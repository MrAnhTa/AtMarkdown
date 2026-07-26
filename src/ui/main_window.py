import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QToolBar, QComboBox, QToolButton,
    QStackedWidget, QStyle, QApplication
)
from PySide6.QtGui import QAction, QIcon, QKeySequence, QDragEnterEvent, QDropEvent
from PySide6.QtCore import Qt, QTimer

from src.config import ConfigManager
from src.utils.md_parser import MarkdownEngine
from src.utils.exporter import DocumentExporter
from src.ui.editor import MarkdownEditor, EditorSearchPanel
from src.ui.viewer import MarkdownViewer
from src.ui.sidebar import SidebarWidget
from src.ui.formatting_bar import FormattingToolbar
from src.ui.stats_bar import DocumentStatsBar


class MainWindow(QMainWindow):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.md_engine = MarkdownEngine()

        self.current_file_path = None
        self.is_modified = False

        # Live render timer to prevent excessive re-rendering on keypresses
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.setInterval(150)
        self.render_timer.timeout.connect(self._perform_live_render)

        self.setAcceptDrops(True)
        self.setWindowTitle("AtMd Reader & Editor")
        self.resize(1200, 800)

        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "app_icon.png"))
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "src", "assets", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()
        self._load_initial_state()

    def _init_ui(self):
        # 1. Main Central Widget & Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 2. Formatting Toolbar (visible in editor/split mode)
        self.format_toolbar = FormattingToolbar(self)
        self.format_toolbar.format_requested.connect(self._on_format_requested)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.format_toolbar)

        # 3. Splitter Container
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #30363d;
            }
        """)

        # 3a. Sidebar Widget
        self.sidebar = SidebarWidget()
        self.sidebar.heading_selected.connect(self._on_toc_heading_selected)
        self.sidebar.recent_file_selected.connect(self.open_file)

        # 3b. Editor Container Widget
        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        self.editor = MarkdownEditor()
        self.editor.textChanged.connect(self._on_editor_text_changed)

        self.search_panel = EditorSearchPanel(self.editor)

        editor_layout.addWidget(self.editor)
        editor_layout.addWidget(self.search_panel)

        # 3c. Viewer Widget
        self.viewer = MarkdownViewer()

        # Add to splitter
        self.main_splitter.addWidget(self.sidebar)
        self.main_splitter.addWidget(self.editor_container)
        self.main_splitter.addWidget(self.viewer)

        # Set default splitter proportions (20% sidebar, 40% editor, 40% viewer)
        self.main_splitter.setSizes([220, 480, 480])

        main_layout.addWidget(self.main_splitter)

        # 4. Status Bar
        self.stats_bar = DocumentStatsBar(self)
        self.setStatusBar(self.stats_bar)

        # 5. Menus & Toolbars
        self._setup_menus()
        self._apply_theme(self.config.get("theme", "dark"))
        self._apply_view_mode(self.config.get("view_mode", "split"))

    def _setup_menus(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #161b22;
                color: #c9d1d9;
                border-bottom: 1px solid #30363d;
            }
            QMenuBar::item:selected {
                background-color: #21262d;
                color: #58a6ff;
            }
            QMenu {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 36px 6px 28px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #21262d;
                color: #58a6ff;
            }
        """)

        # File Menu
        file_menu = menubar.addMenu("&File")

        new_act = QAction("📄 New File", self)
        new_act.setShortcut(QKeySequence.StandardKey.New)
        new_act.triggered.connect(self.new_file)
        file_menu.addAction(new_act)

        open_act = QAction("📂 Open File...", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self.choose_file_dialog)
        file_menu.addAction(open_act)

        save_act = QAction("💾 Save", self)
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self.save_file)
        file_menu.addAction(save_act)

        save_as_act = QAction("💾 Save As...", self)
        save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_act.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        export_html_act = QAction("🌐 Export to HTML...", self)
        export_html_act.triggered.connect(self.export_html)
        file_menu.addAction(export_html_act)

        export_pdf_act = QAction("📕 Export to PDF...", self)
        export_pdf_act.triggered.connect(self.export_pdf)
        file_menu.addAction(export_pdf_act)

        file_menu.addSeparator()

        exit_act = QAction("✕ Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        undo_act = QAction("↩️ Undo", self)
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        undo_act.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_act)

        redo_act = QAction("↪️ Redo", self)
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        redo_act.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_act)

        edit_menu.addSeparator()

        cut_act = QAction("✂️ Cut", self)
        cut_act.setShortcut(QKeySequence.StandardKey.Cut)
        cut_act.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_act)

        copy_act = QAction("📋 Copy", self)
        copy_act.setShortcut(QKeySequence.StandardKey.Copy)
        copy_act.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_act)

        paste_act = QAction("📌 Paste", self)
        paste_act.setShortcut(QKeySequence.StandardKey.Paste)
        paste_act.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_act)

        edit_menu.addSeparator()

        find_act = QAction("🔍 Find in Editor...", self)
        find_act.setShortcut(QKeySequence.StandardKey.Find)
        find_act.triggered.connect(lambda: self.search_panel.show() or self.search_panel.search_input.setFocus())
        edit_menu.addAction(find_act)

        # View Menu
        view_menu = menubar.addMenu("&View")

        mode_reader = QAction("📖 Reader Mode", self)
        mode_reader.triggered.connect(lambda: self._apply_view_mode("reader"))
        view_menu.addAction(mode_reader)

        mode_editor = QAction("✏️ Editor Mode", self)
        mode_editor.triggered.connect(lambda: self._apply_view_mode("editor"))
        view_menu.addAction(mode_editor)

        mode_split = QAction("⚡ Split Live Preview", self)
        mode_split.triggered.connect(lambda: self._apply_view_mode("split"))
        view_menu.addAction(mode_split)

        view_menu.addSeparator()

        toggle_sidebar_act = QAction("📌 Toggle Sidebar", self)
        toggle_sidebar_act.setShortcut(QKeySequence("Ctrl+B"))
        toggle_sidebar_act.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(toggle_sidebar_act)

        view_menu.addSeparator()

        # Theme Submenu
        theme_menu = view_menu.addMenu("🎨 Themes")
        theme_dark = QAction("🌙 Dark Mode", self)
        theme_dark.triggered.connect(lambda: self._apply_theme("dark"))
        theme_light = QAction("☀️ Light Mode", self)
        theme_light.triggered.connect(lambda: self._apply_theme("light"))
        theme_sepia = QAction("📜 Sepia Mode", self)
        theme_sepia.triggered.connect(lambda: self._apply_theme("sepia"))

        theme_menu.addAction(theme_dark)
        theme_menu.addAction(theme_light)
        theme_menu.addAction(theme_sepia)

        # Top Control Bar Action Items
        top_bar = QToolBar("Quick Access", self)
        top_bar.setStyleSheet("""
            QToolBar {
                background-color: #161b22;
                border-bottom: 1px solid #30363d;
                spacing: 8px;
                padding: 4px;
            }
            QToolButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QToolButton:hover {
                background-color: #30363d;
                color: #58a6ff;
            }
        """)

        btn_open = QToolButton()
        btn_open.setText("📂 Open")
        btn_open.setToolTip("Browse & Open Markdown File (Ctrl+O)")
        btn_open.clicked.connect(self.choose_file_dialog)
        top_bar.addWidget(btn_open)

        btn_save = QToolButton()
        btn_save.setText("💾 Save")
        btn_save.setToolTip("Save Document (Ctrl+S)")
        btn_save.clicked.connect(self.save_file)
        top_bar.addWidget(btn_save)

        top_bar.addSeparator()

        # View Mode Dropdown
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["📖 Reader View", "✏️ Editor View", "⚡ Split Live Preview"])
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_combo_changed)
        top_bar.addWidget(self.mode_combo)

        # Theme Dropdown
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["🌙 Dark", "☀️ Light", "📜 Sepia"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        top_bar.addWidget(self.theme_combo)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, top_bar)

    def _load_initial_state(self):
        recent_files = self.config.get_recent_files()
        self.sidebar.update_recent_files(recent_files)

        # Load last opened file if valid
        if recent_files and os.path.exists(recent_files[0]):
            self.open_file(recent_files[0])
        else:
            self._load_sample_welcome_doc()

    def _load_sample_welcome_doc(self):
        welcome_md = """# Welcome to AtMd Reader & Editor 🚀

AtMd là ứng dụng đọc và chỉnh sửa file **Markdown** hiện đại, nhẹ và mượt mà trên Windows.

## 🌟 Key Features

- **📖 Reader Mode**: Hiển thị Markdown theo phong cách GitHub cực đẹp.
- **✏️ Editor Mode**: Chỉnh sửa Plain Text với dòng số, phím tắt nhanh và tìm kiếm `Ctrl+F`.
- **⚡ Split Live Preview**: Chỉnh sửa ở bảng bên trái và xem trực tiếp kết quả bên phải.
- **📌 Auto Outline**: Tự động trích xuất tiêu đề thành cây mục lục bên trái.
- **🎨 Custom Themes**: Chuyển đổi linh hoạt giữa **Dark Mode**, **Light Mode** và **Sepia Mode**.
- **📂 Drag & Drop**: Kéo thả trực tiếp file `.md` từ máy tính vào ứng dụng để mở nhanh.

---

## 🛠️ Code Highlight Example

```python
def greet(name: str) -> str:
    # Python 3.13 Markdown Engine
    return f"Hello, {name}! Enjoy writing Markdown."

print(greet("Developer"))
```

## 📋 Task List & Tables

- [x] Chọn file Markdown từ máy tính
- [x] Bật bảng chỉnh sửa Plain Text
- [x] Tự động cập nhật Live Preview
- [ ] Export sang HTML & PDF

| Feature | Reader Mode | Editor Mode | Split View |
| :--- | :---: | :---: | :---: |
| Preview | ✅ | ❌ | ✅ |
| Editing | ❌ | ✅ | ✅ |
| Speed | ⚡⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡ |

---
*Bắt đầu bằng cách bấm vào nút **📂 Open** trên thanh công cụ hoặc kéo thả file `.md` vào đây!*
"""
        self.editor.setPlainText(welcome_md)
        self._update_window_title()
        self._trigger_render()

    def choose_file_dialog(self):
        if not self._maybe_save_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md *.markdown *.txt);;All Files (*.*)"
        )
        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path: str):
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Error", f"File not found:\n{file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            self.current_file_path = file_path
            self.editor.setPlainText(content)
            self.is_modified = False

            self.config.add_recent_file(file_path)
            self.sidebar.update_recent_files(self.config.get_recent_files())

            self._update_window_title()
            self._trigger_render()
        except Exception as e:
            QMessageBox.critical(self, "Error Opening File", f"Could not read file:\n{e}")

    def save_file(self) -> bool:
        if not self.current_file_path:
            return self.save_file_as()

        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.is_modified = False
            self._update_window_title()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{e}")
            return False

    def save_file_as(self) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown File As",
            self.current_file_path or "untitled.md",
            "Markdown Files (*.md *.markdown);;Text Files (*.txt);;All Files (*.*)"
        )
        if file_path:
            self.current_file_path = file_path
            return self.save_file()
        return False

    def new_file(self):
        if not self._maybe_save_changes():
            return
        self.current_file_path = None
        self.editor.setPlainText("")
        self.is_modified = False
        self._update_window_title()
        self._trigger_render()

    def export_html(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to HTML", "document.html", "HTML Files (*.html)"
        )
        if file_path:
            md_text = self.editor.toPlainText()
            html = self.md_engine.render(md_text, theme=self.config.get("theme", "dark"))
            if DocumentExporter.export_html(html, file_path):
                QMessageBox.information(self, "Export Success", f"Exported successfully to:\n{file_path}")

    def export_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to PDF", "document.pdf", "PDF Files (*.pdf)"
        )
        if file_path:
            md_text = self.editor.toPlainText()
            html = self.md_engine.render(md_text, theme=self.config.get("theme", "dark"))
            if DocumentExporter.export_pdf(html, file_path):
                QMessageBox.information(self, "Export Success", f"Exported successfully to:\n{file_path}")

    def _maybe_save_changes(self) -> bool:
        if not self.is_modified:
            return True
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "The current document has unsaved changes. Would you like to save them?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Save:
            return self.save_file()
        elif reply == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def _on_editor_text_changed(self):
        self.is_modified = True
        self._update_window_title()
        self.render_timer.start()

    def _trigger_render(self):
        self.render_timer.start()

    def _perform_live_render(self):
        text = self.editor.toPlainText()
        theme = self.config.get("theme", "dark")

        # Render preview HTML
        html = self.md_engine.render(text, theme=theme)
        self.viewer.set_html_content(html, base_url_path=self.current_file_path)

        # Update Outline TOC
        headings = self.md_engine.extract_toc(text)
        self.sidebar.update_toc(headings)

        # Update Document Stats
        stats = self.md_engine.calculate_stats(text)
        self.stats_bar.update_stats(stats)

    def _on_toc_heading_selected(self, anchor_id: str):
        self.viewer.scroll_to_heading(anchor_id)

    def _on_format_requested(self, prefix: str, suffix: str):
        self.editor.insert_formatting(prefix, suffix)

    def _apply_theme(self, theme: str):
        self.config.set("theme", theme)
        self.editor.apply_theme(theme)
        self.viewer.apply_theme(theme)
        self._trigger_render()

        # Sync combo index
        idx_map = {"dark": 0, "light": 1, "sepia": 2}
        if theme in idx_map:
            self.theme_combo.setCurrentIndex(idx_map[theme])

    def _apply_view_mode(self, mode: str):
        self.config.set("view_mode", mode)
        if mode == "reader":
            self.editor_container.hide()
            self.viewer.show()
            self.format_toolbar.hide()
            self.stats_bar.set_mode("Reader View")
            self.mode_combo.setCurrentIndex(0)
        elif mode == "editor":
            self.editor_container.show()
            self.viewer.hide()
            self.format_toolbar.show()
            self.stats_bar.set_mode("Editor View")
            self.mode_combo.setCurrentIndex(1)
        else:  # split mode
            self.editor_container.show()
            self.viewer.show()
            self.format_toolbar.show()
            self.stats_bar.set_mode("Split Live Preview")
            self.mode_combo.setCurrentIndex(2)

    def _on_mode_combo_changed(self, index: int):
        modes = ["reader", "editor", "split"]
        if 0 <= index < len(modes):
            self._apply_view_mode(modes[index])

    def _on_theme_combo_changed(self, index: int):
        themes = ["dark", "light", "sepia"]
        if 0 <= index < len(themes):
            self._apply_theme(themes[index])

    def _toggle_sidebar(self):
        visible = not self.sidebar.isVisible()
        self.sidebar.setVisible(visible)
        self.config.set("sidebar_visible", visible)

    def _update_window_title(self):
        filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled.md"
        dirty = " *" if self.is_modified else ""
        self.setWindowTitle(f"{filename}{dirty} - AtMd Reader & Editor")

    # Drag and Drop support for Markdown files
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith(('.md', '.markdown', '.txt')):
                if self._maybe_save_changes():
                    self.open_file(file_path)

    def closeEvent(self, event):
        if self._maybe_save_changes():
            event.accept()
        else:
            event.ignore()
