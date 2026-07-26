import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.config import ConfigManager
from src.ui.main_window import MainWindow


def main():
    # Enable High DPI scaling on Windows
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("AtMd Reader & Editor")
    app.setOrganizationName("ToolsBuilt")

    config = ConfigManager()
    window = MainWindow(config)
    
    # Check if file path passed via command line
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        window.open_file(sys.argv[1])

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
