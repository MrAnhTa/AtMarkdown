// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod config;
mod markdown;
mod stats;

use commands::*;
use config::ConfigManager;

fn main() {
    let config_manager = ConfigManager::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .manage(AppState {
            config: config_manager,
        })
        .invoke_handler(tauri::generate_handler![
            get_settings,
            save_settings,
            open_file_content,
            save_file_content,
            dialog_open_file,
            dialog_save_file,
            dialog_export_html_path,
            add_recent_file,
            render_markdown,
            export_html,
            get_welcome_doc,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
