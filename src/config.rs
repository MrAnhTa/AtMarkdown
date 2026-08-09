use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub theme: String,
    pub view_mode: String,
    pub sidebar_visible: bool,
    pub recent_files: Vec<String>,
    pub max_recent_files: usize,
    pub font_family: String,
    pub font_size: usize,
    pub auto_save: bool,
    pub wrap_lines: bool,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            theme: "dark".to_string(),
            view_mode: "split".to_string(),
            sidebar_visible: true,
            recent_files: Vec::new(),
            max_recent_files: 10,
            font_family: "Consolas".to_string(),
            font_size: 13,
            auto_save: false,
            wrap_lines: true,
        }
    }
}

pub struct ConfigManager {
    config_dir: PathBuf,
    settings_file: PathBuf,
}

impl ConfigManager {
    pub fn new() -> Self {
        let config_dir = dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join(".AtMarkdown");
        let settings_file = config_dir.join("settings.json");

        if !config_dir.exists() {
            let _ = fs::create_dir_all(&config_dir);
        }

        Self {
            config_dir,
            settings_file,
        }
    }

    pub fn load_settings(&self) -> AppSettings {
        if self.settings_file.exists() {
            if let Ok(content) = fs::read_to_string(&self.settings_file) {
                if let Ok(settings) = serde_json::from_str::<AppSettings>(&content) {
                    return settings;
                }
            }
        }
        let default_settings = AppSettings::default();
        self.save_settings(&default_settings);
        default_settings
    }

    pub fn save_settings(&self, settings: &AppSettings) {
        if let Ok(json) = serde_json::to_string_pretty(settings) {
            let _ = fs::write(&self.settings_file, json);
        }
    }

    pub fn add_recent_file(&self, file_path: &str) -> AppSettings {
        let mut settings = self.load_settings();
        let path = Path::new(file_path);
        let abs_path = path.canonicalize()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|_| file_path.to_string());

        // Retain only valid existing files and remove duplicate
        let mut recent: Vec<String> = settings
            .recent_files
            .into_iter()
            .filter(|f| f != &abs_path && Path::new(f).exists())
            .collect();

        recent.insert(0, abs_path);
        recent.truncate(settings.max_recent_files);

        settings.recent_files = recent;
        self.save_settings(&settings);
        settings
    }
}
