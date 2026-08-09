use crate::config::{AppSettings, ConfigManager};
use crate::markdown::{HeadingItem, MarkdownEngine};
use crate::stats::{DocumentStats, StatsCalculator};
use serde::{Deserialize, Serialize};
use std::fs;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct RenderResult {
    pub html: String,
    pub headings: Vec<HeadingItem>,
    pub stats: DocumentStats,
}

pub struct AppState {
    pub config: ConfigManager,
}

#[tauri::command]
pub fn get_settings(state: State<'_, AppState>) -> Result<AppSettings, String> {
    Ok(state.config.load_settings())
}

#[tauri::command]
pub fn save_settings(settings: AppSettings, state: State<'_, AppState>) -> Result<(), String> {
    state.config.save_settings(&settings);
    Ok(())
}

#[tauri::command]
pub fn open_file_content(path: String, state: State<'_, AppState>) -> Result<(String, String), String> {
    match fs::read_to_string(&path) {
        Ok(content) => {
            state.config.add_recent_file(&path);
            Ok((path, content))
        }
        Err(e) => Err(format!("Failed to open file: {}", e)),
    }
}

#[tauri::command]
pub fn save_file_content(path: String, content: String, state: State<'_, AppState>) -> Result<(), String> {
    match fs::write(&path, content) {
        Ok(_) => {
            state.config.add_recent_file(&path);
            Ok(())
        }
        Err(e) => Err(format!("Failed to save file: {}", e)),
    }
}

#[tauri::command]
pub fn dialog_open_file(state: State<'_, AppState>) -> Result<Option<(String, String)>, String> {
    let file = rfd::FileDialog::new()
        .add_filter("Markdown Files", &["md", "markdown", "txt"])
        .add_filter("All Files", &["*"])
        .set_title("Open Markdown File")
        .pick_file();

    if let Some(path_buf) = file {
        let path_str = path_buf.to_string_lossy().to_string();
        match fs::read_to_string(&path_buf) {
            Ok(content) => {
                state.config.add_recent_file(&path_str);
                Ok(Some((path_str, content)))
            }
            Err(e) => Err(format!("Could not read file: {}", e)),
        }
    } else {
        Ok(None)
    }
}

#[tauri::command]
pub fn dialog_save_file(default_name: Option<String>) -> Result<Option<String>, String> {
    let mut dialog = rfd::FileDialog::new()
        .add_filter("Markdown Files", &["md", "markdown"])
        .add_filter("All Files", &["*"])
        .set_title("Save Markdown File As");

    if let Some(name) = default_name {
        dialog = dialog.set_file_name(&name);
    }

    if let Some(path_buf) = dialog.save_file() {
        Ok(Some(path_buf.to_string_lossy().to_string()))
    } else {
        Ok(None)
    }
}

#[tauri::command]
pub fn dialog_export_html_path() -> Result<Option<String>, String> {
    let file = rfd::FileDialog::new()
        .add_filter("HTML Files", &["html", "htm"])
        .set_title("Export to HTML")
        .set_file_name("document.html")
        .save_file();

    if let Some(path_buf) = file {
        Ok(Some(path_buf.to_string_lossy().to_string()))
    } else {
        Ok(None)
    }
}

#[tauri::command]
pub fn add_recent_file(path: String, state: State<'_, AppState>) -> Result<AppSettings, String> {
    Ok(state.config.add_recent_file(&path))
}

#[tauri::command]
pub fn render_markdown(md_text: String, theme: String) -> RenderResult {
    let html = MarkdownEngine::render(&md_text, &theme);
    let headings = MarkdownEngine::extract_toc(&md_text);
    let stats = StatsCalculator::calculate(&md_text);

    RenderResult {
        html,
        headings,
        stats,
    }
}

#[tauri::command]
pub fn export_html(html_content: String, path: String) -> Result<(), String> {
    fs::write(path, html_content).map_err(|e| format!("Failed to export HTML: {}", e))
}

#[tauri::command]
pub fn get_welcome_doc() -> String {
    r#"# Welcome to AtMarkdown Reader & Editor 🚀 (Rust Edition)

AtMarkdown là ứng dụng đọc và chỉnh sửa file **Markdown** hiện đại, siêu nhẹ và phản hồi tức thì được phát triển bằng **Rust**.

## 🌟 Key Features

- **📖 Reader Mode**: Hiển thị Markdown theo phong cách GitHub cực đẹp.
- **✏️ Editor Mode**: Chỉnh sửa Plain Text với dòng số, phím tắt nhanh và tìm kiếm `Ctrl+F`.
- **⚡ Split Live Preview**: Chỉnh sửa ở bảng bên trái và xem trực tiếp kết quả bên phải.
- **📌 Auto Outline**: Tự động trích xuất tiêu đề thành cây mục lục bên trái.
- **🎨 Custom Themes**: Chuyển đổi linh hoạt giữa **Dark Mode**, **Light Mode** và **Sepia Mode**.
- **📂 Drag & Drop**: Kéo thả trực tiếp file `.md` từ máy tính vào ứng dụng để mở nhanh.

---

## 🛠️ Code Highlight Example

```rust
fn greet(name: &str) -> String {
    // Rust Markdown Engine
    format!("Hello, {}! Enjoy blazing-fast Markdown editing.", name)
}

fn main() {
    println!("{}", greet("Developer"));
}
```

## 📋 Task List & Tables

- [x] Chuyển đổi toàn bộ sang ngôn ngữ Rust
- [x] Kích thước file `.exe` cực nhẹ (< 8MB)
- [x] Tốc độ khởi động tức thì (< 100ms)
- [x] Khôi phục toàn bộ giao diện và phím tắt của bản Python

| Feature | Reader Mode | Editor Mode | Split View |
| :--- | :---: | :---: | :---: |
| Preview | ✅ | ❌ | ✅ |
| Editing | ❌ | ✅ | ✅ |
| Speed | ⚡⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡ |

---
*Bắt đầu bằng cách bấm vào nút **📂 Open** trên thanh công cụ hoặc kéo thả file `.md` vào đây!*
"#.to_string()
}
