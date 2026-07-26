import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from src.config import ConfigManager
from src.ui.main_window import MainWindow


def get_asset_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, "..", relative_path))


def main():
    # Fix taskbar icon on Windows by setting explicit AppUserModelID
    if sys.platform == "win32":
        try:
            myappid = "ToolsBuilt.AtMd.MarkdownEditor.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Could not set AppUserModelID: {e}")

    # Enable High DPI scaling on Windows
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("AtMd Reader & Editor")
    app.setOrganizationName("ToolsBuilt")

    # Set Application Icon
    icon_path = get_asset_path(os.path.join("src", "assets", "app_icon.png"))
    if not os.path.exists(icon_path):
        icon_path = get_asset_path(os.path.join("src", "assets", "app_icon.ico"))

    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)

    config = ConfigManager()
    window = MainWindow(config)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    
    # Check if file path passed via command line
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        window.open_file(sys.argv[1])

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
