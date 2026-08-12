# AtMarkdown - Ultra-Fast & Lightweight Windows Markdown Reader

**AtMarkdown** is a modern, high-performance, ultra-lightweight Markdown reader and editor for Windows built with **Rust** and **Tauri v2 (WebView2)**.

Rebuilt from the ground up, this Rust application achieves an **ultra-lightweight footprint (~5-8 MB)** and **instant cold startup (< 100 ms)**.

![Rust Version](https://img.shields.io/badge/Rust-1.97%2B-orange.svg)
![Framework](https://img.shields.io/badge/Framework-Tauri_v2-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ⚡ Performance Comparison

| Metric | Legacy Python (PySide6) | Modern Rust (AtMarkdown) | Improvement |
| :--- | :---: | :---: | :---: |
| **Executable Size** | ~200 MB | **~5 - 8 MB** | **~96% smaller** |
| **Cold Startup Time** | ~3.5 s | **< 100 ms** | **~35x faster** |
| **Memory Footprint (RAM)** | ~300 MB | **~35 - 50 MB** | **~6x lighter** |

---

## ✨ Key Features

- 📐 **LaTeX Math Support (KaTeX)**: Full rendering for display math `$$...$$` and inline math `$ ... $` (fractions, summations, matrices, symbols). Works inside lists, blockquotes, and tables.
- 💡 **GFM Callouts & Alerts**: Support for GitHub-style alerts `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]` with custom SVG icons and theme borders.
- 🛠️ **Syntax Highlighting (Highlight.js)**: Automatic multi-language code block highlighting for Rust, Python, JS/TS, HTML, CSS, C++, JSON, SQL, Bash, etc.
- 📊 **Mermaid Diagrams**: Render flowcharts, sequence diagrams, Gantt charts, and class diagrams directly from ` ```mermaid ` code blocks.
- 📂 **File Operations & Drag-and-Drop**: Open, Save, Save As, and drag `.md` files directly into the app window.
- ⚡ **Triple View Modes**:
  - 📖 **Reader Mode**: Clean GitHub-style Markdown rendering.
  - ✏️ **Editor Mode**: Plain-text editor with line numbers, code font, search/find (`Ctrl+F`).
  - ⚡ **Split Live Preview**: Real-time side-by-side editing and instant debounced rendering.
- 🎨 **Multiple Themes**: Seamlessly switch between **Dark Mode**, **Light Mode**, and **Sepia Mode**.
- 📌 **Auto Table of Contents (Outline)**: Heading tree (`#`, `##`, `###`) with smooth scroll to heading.
- 📋 **Task Lists & Checklists**: Interactive task item checkboxes (`- [x]` / `- [ ]`) with custom styled checkmarks.
- ⌨️ **Keyboard Cap Styling**: Custom `<kbd>` styling for hotkey shortcuts.
- 📊 **Real-Time Document Statistics**: Status bar tracking line count, word count, char count, and estimated reading time.
- 🕒 **Recent Files History**: Sidebar access to quickly reopen recent Markdown files.
- 🌐 **Export Options**: Export rendered Markdown to standalone **HTML** or **PDF**.

---

## 🚀 Running & Building

### Development Mode:
```powershell
cargo run
```

### Build Release Executable:
Run the PowerShell build script:
```powershell
cargo build --release
```
The compiled binary will be placed inside `target/release/atmarkdown.exe`.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + O` | Open Markdown File |
| `Ctrl + S` | Save Current Document |
| `Ctrl + Shift + S` | Save As... |
| `Ctrl + N` | Create New File |
| `Ctrl + F` | Search / Find in Editor |
| `Ctrl + B` | Toggle Left Sidebar |

---

## 📄 License

Licensed under the MIT License.
