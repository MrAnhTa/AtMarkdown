# AtMd - Modern Windows Markdown Reader & Editor

**AtMd** is a modern, lightweight, high-performance Markdown reader and editor for Windows built with **Python 3.13** and **PySide6 (Qt 6)**. It offers GitHub-flavored Markdown rendering, real-time live preview, document outline navigation, theme customization, document statistics, and export features.

![Python Version](https://img.shields.io/badge/Python-3.13-blue.svg)
![UI Framework](https://img.shields.io/badge/GUI-PySide6-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

- 📂 **File Picker & Drag-and-Drop**: Easily browse files from your computer or drag `.md` files directly into the window.
- ⚡ **Triple View Modes**:
  - 📖 **Reader Mode**: Distraction-free GitHub-style rendered preview.
  - ✏️ **Editor Mode**: Plain-text editor with line numbers, code font, and search/replace (`Ctrl+F`).
  - ⚡ **Split Live Preview**: Real-time side-by-side editing and instant rendering.
- 🎨 **Multiple Themes**: Seamlessly switch between **Dark Mode**, **Light Mode**, and **Sepia Mode**.
- 📌 **Auto Table of Contents (Outline)**: Automatically extracts `#`, `##`, `###` headings into an interactive sidebar outline. Click any heading to jump to that section.
- 🛠️ **Quick Formatting Toolbar**: 1-click insertion for Bold, Italic, Headings, Code Blocks, Links, Images, Quotes, Lists, Checklists, and Tables.
- 📊 **Real-Time Document Statistics**: Bottom status bar tracking line count, word count, character count, and estimated reading time.
- 🕒 **Recent Files History**: Quick sidebar access to reopen your recent Markdown documents.
- 🌐 **Export Options**: Export rendered Markdown documents to standalone **HTML** or **PDF** files.

---

## 🛠️ Prerequisites

- **Python 3.13** or higher installed on your Windows machine.
- Git (optional, for cloning).

---

## 📥 Installation

1. **Clone or Navigate to the Repository Directory**:
   ```bash
   cd d:\Working\ToolsBuilt\Repo\MarkdownReader
   ```

2. **Create a Virtual Environment (Python 3.13)**:
   ```powershell
   py -3.13 -m venv venv
   ```

3. **Activate Virtual Environment & Install Dependencies**:
   ```powershell
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1

   # Install required packages
   pip install -r requirements.txt
   ```

---

## 🚀 Running the Application

### Launch the GUI App:
```powershell
.\venv\Scripts\python run.py
```

### Open a Specific Markdown File Directly:
```powershell
.\venv\Scripts\python run.py "C:\path\to\your\document.md"
```

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
| `Ctrl + Shift + H` | Export to HTML |
| `Ctrl + Shift + P` | Export to PDF |

---

## 📁 Project Structure

```
MarkdownReader/
├── venv/                  # Python 3.13 virtual environment
├── requirements.txt       # Project dependencies
├── run.py                 # Application entrypoint launcher
├── README.md              # Project documentation
├── tests/
│   └── test_md_engine.py  # Unit tests for Markdown parser
└── src/
    ├── app.py             # QApplication initialization
    ├── config.py          # Settings and recent files persistence
    ├── ui/
    │   ├── main_window.py # Main window layout & splitters
    │   ├── viewer.py      # HTML preview panel
    │   ├── editor.py      # Line-numbered code editor & search bar
    │   ├── sidebar.py     # Outline TOC & Recent files sidebar
    │   ├── formatting_bar.py # Quick Markdown formatting toolbar
    │   └── stats_bar.py   # Document statistics status bar
    └── utils/
        ├── md_parser.py   # Markdown parsing engine & syntax highlighter
        └── exporter.py    # HTML & PDF export utilities
```

---

## 📄 License

This project is licensed under the MIT License - feel free to use and customize it!
