import json
import os
from pathlib import Path
from typing import List, Dict, Any

APP_NAME = "AtMd Reader & Editor"
ORGANIZATION_NAME = "ToolsBuilt"

CONFIG_DIR = Path.home() / ".atmd"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "theme": "dark",  # "dark", "light", "sepia"
    "view_mode": "split",  # "reader", "editor", "split"
    "sidebar_visible": True,
    "recent_files": [],
    "max_recent_files": 10,
    "font_family": "Consolas",
    "font_size": 13,
    "auto_save": False,
    "wrap_lines": True
}


class ConfigManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.settings: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        self.settings[key] = value
        self.save_settings()

    def get_recent_files(self) -> List[str]:
        # Filter existing files
        files = [f for f in self.settings.get("recent_files", []) if os.path.exists(f)]
        return files

    def add_recent_file(self, file_path: str):
        abs_path = os.path.abspath(file_path)
        recent = [f for f in self.settings.get("recent_files", []) if os.path.abspath(f) != abs_path]
        recent.insert(0, abs_path)
        max_items = self.settings.get("max_recent_files", 10)
        self.settings["recent_files"] = recent[:max_items]
        self.save_settings()

    def clear_recent_files(self):
        self.settings["recent_files"] = []
        self.save_settings()
