from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QLabel, QPushButton
)
from PySide6.QtCore import Signal, Qt
from typing import List, Dict, Any


class SidebarWidget(QWidget):
    heading_selected = Signal(str)  # anchor id
    recent_file_selected = Signal(str)  # file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #0d1117;
            }
            QTabBar::tab {
                background-color: #161b22;
                color: #8b949e;
                padding: 8px 16px;
                border: 1px solid #30363d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0d1117;
                color: #58a6ff;
                font-weight: bold;
                border-bottom: 2px solid #58a6ff;
            }
            QTreeWidget, QListWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                border: none;
            }
            QTreeWidget::item, QListWidget::item {
                padding: 6px 4px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover, QListWidget::item:hover {
                background-color: #161b22;
                color: #58a6ff;
            }
            QTreeWidget::item:selected, QListWidget::item:selected {
                background-color: #21262d;
                color: #58a6ff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        
        # 1. Outline Tab
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderHidden(True)
        self.toc_tree.itemClicked.connect(self._on_toc_clicked)

        # 2. Recent Files Tab
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self._on_recent_clicked)

        self.tabs.addTab(self.toc_tree, "📌 Outline")
        self.tabs.addTab(self.recent_list, "🕒 Recent")

        layout.addWidget(self.tabs)

    def update_toc(self, headings: List[Dict[str, Any]]):
        self.toc_tree.clear()
        if not headings:
            item = QTreeWidgetItem(["(No headings found)"])
            item.setDisabled(True)
            self.toc_tree.addTopLevelItem(item)
            return

        # Stack to keep track of tree hierarchy
        stack = [(0, self.toc_tree)]

        for h in headings:
            level = h["level"]
            title = h["title"]
            anchor_id = h["id"]

            item = QTreeWidgetItem([f"{'  ' * (level - 1)}• {title}"])
            item.setData(0, Qt.ItemDataRole.UserRole, anchor_id)

            # Find parent level
            while stack and stack[-1][0] >= level:
                stack.pop()

            parent = stack[-1][1]
            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)

            stack.append((level, item))

        self.toc_tree.expandAll()

    def update_recent_files(self, file_paths: List[str]):
        self.recent_list.clear()
        if not file_paths:
            item = QListWidgetItem("(No recent files)")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.recent_list.addItem(item)
            return

        for path in file_paths:
            import os
            filename = os.path.basename(path)
            item = QListWidgetItem(f"📄 {filename}\n   {path}")
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.recent_list.addItem(item)

    def _on_toc_clicked(self, item: QTreeWidgetItem, column: int):
        anchor_id = item.data(0, Qt.ItemDataRole.UserRole)
        if anchor_id:
            self.heading_selected.emit(anchor_id)

    def _on_recent_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.recent_file_selected.emit(path)
