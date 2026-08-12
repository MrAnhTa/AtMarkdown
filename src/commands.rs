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
    fs::write(&path, html_content).map_err(|e| format!("Failed to export HTML: {}", e))
}

#[tauri::command]
pub fn get_welcome_doc() -> String {
    r#"# Welcome to AtMarkdown Reader & Editor 🚀

AtMarkdown là ứng dụng đọc và chỉnh sửa file **Markdown** hiện đại, hỗ trợ công thức Toán LaTeX, Sơ đồ Mermaid, Highlight code và GFM Callouts.

---

## 📐 Công thức Toán học (LaTeX / KaTeX Math)

* **Chỉ số Kỳ vọng (Expectancy)**:
      $$\text{Expectancy} = (\text{Win Rate} \times \text{Average Win R}) - (\text{Loss Rate} \times \text{Average Loss R})$$
* **Chỉ số Yếu tố Lợi nhuận (Profit Factor)**:
      $$\text{Profit Factor} = \frac{\sum \text{Gross Profits (in R)}}{\sum \text{Gross Losses (in R)}}$$

* **Công thức Chuẩn hoá (Inline Math)**: Phương trình $E = mc^2$ và căn bậc hai $\sqrt{x^2 + y^2} = r$.

---

## 💡 GFM Callouts & Alerts

> [!NOTE]
> Ghi chú quan trọng cho tài liệu hoặc hướng dẫn nhanh.

> [!TIP]
> Bấm phím <kbd>Ctrl</kbd> + <kbd>S</kbd> để lưu tài liệu hoặc <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> để Save As.

> [!WARNING]
> Cảnh báo trước khi thay đổi cấu hình hoặc xuất dữ liệu!

---

## 📊 Sơ đồ Mermaid (Diagrams)

```mermaid
graph TD;
    A[Nhập Markdown] --> B{Parse Engine};
    B -- Math LaTeX --> C[KaTeX Renderer];
    B -- Code Block --> D[Highlight.js];
    B -- Diagram --> E[Mermaid.js];
    C --> F[Preview Visual HTML];
    D --> F;
    E --> F;
```

---

## 🛠️ Code Syntax Highlighting

```python
def calculate_expectancy(win_rate, avg_win_r, loss_rate, avg_loss_r):
    """Tính toán chỉ số Expectancy chuẩn trong Trading"""
    return (win_rate * avg_win_r) - (loss_rate * avg_loss_r)

print("Expectancy:", calculate_expectancy(0.55, 2.0, 0.45, 1.0))
```

```rust
fn greet(name: &str) -> String {
    format!("Hello, {}! Enjoy blazing-fast Markdown editing.", name)
}
```

---

## 📋 Task List & Tables

- [x] Tích hợp KaTeX rendering công thức toán block `$$` và inline `$`
- [x] Hỗ trợ GFM Callouts `[!NOTE]`, `[!TIP]`, `[!WARNING]`
- [x] Tích hợp Highlight.js cho 180+ ngôn ngữ lập trình
- [x] Sơ đồ Mermaid.js tự động thay đổi theo Theme
- [x] Phím bấm `<kbd>` styling

| Feature | Reader View | Split Preview | Export HTML / PDF |
| :--- | :---: | :---: | :---: |
| Math LaTeX | ✅ | ✅ | ✅ |
| Syntax Highlighting | ✅ | ✅ | ✅ |
| Mermaid Diagrams | ✅ | ✅ | ✅ |
| Custom Themes | ✅ | ✅ | ✅ |

---
*Bắt đầu bằng cách bấm nút **📂 Open** trên thanh công cụ hoặc kéo thả file `.md` vào đây!*
"#.to_string()
}
