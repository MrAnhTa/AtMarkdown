# AtMarkdown — Python desktop app

This branch implements the AtMarkdown reader and editor in Python with PySide6 and Qt WebEngine. Feature parity is based on Rust `main` at `d75bd43`; application signing is intentionally excluded. Rust and Tauri are not required to run or build this branch.

## Run on Windows

Python 3.10+ is required (tested with Python 3.12.10 and PySide6 6.11.2).

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
# Or open a document directly:
.\.venv\Scripts\python.exe run.py "C:\Documents\notes.md"
```

With uv, use `uv venv .venv` and `uv pip install --python .venv/Scripts/python.exe -r requirements.txt` instead of the first two commands.

## Features

- Reader, editor and split preview; 150 ms debounce and two-way proportional scroll synchronization.
- Native file dialogs, new/open/save/save as, drag and drop, recent files and protection for unsaved changes.
- Line numbers, undo/redo, clipboard operations, wrapping, forward/backward find, and the complete formatting toolbar from main.
- Dark, light and sepia themes across the application and rendered content.
- Outline navigation in both preview and editor, including duplicate titles and correct source lines; headings inside code fences are excluded.
- LaTeX through KaTeX: `$...$`, `$$...$$`, `\(...\)`, `\[...\]`, supported equation environments and math/latex/katex fences. Math also works inside lists, quotes and tables.
- Mermaid diagrams, Highlight.js syntax highlighting and copy-code buttons.
- All five GitHub alerts: NOTE, TIP, IMPORTANT, WARNING and CAUTION.
- Tables, strikethrough, task checkboxes, keyboard caps, images, links, footnotes and definition lists. Task checkboxes in the preview are temporary; edit the Markdown to save their state, as on main.
- Live line, word and character counts and estimated reading time.
- Standalone HTML with embedded scripts, CSS, fonts and existing local images. Remote image URLs still require a connection.
- Asynchronous PDF export waits for diagrams, math, fonts and images, uses a readable light palette and A4 margins, and reports completion/errors. Export uses the current editor text even before live preview catches up.

Rendering libraries and the full KaTeX woff2 font set are bundled locally. Preview content is loaded from temporary files so large documents are not limited by Qt's `setHtml` data URL size. Raw HTML is sanitized before loading; external web links open in the default browser, and local Markdown links open in the editor.

Settings and recent files are stored in `%USERPROFILE%\.atmd\settings.json`.

## Shortcuts

| Shortcut | Action |
| --- | --- |
| Ctrl+O | Open |
| Ctrl+N | New |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save as |
| Ctrl+F | Toggle editor search; reveals the editor when in reader mode |
| Ctrl+B | Toggle sidebar |
| Ctrl+Z / Ctrl+Y | Undo / redo |
| Enter in search | Find next |
| Escape in search | Close search |

## Build the unsigned Windows executable

```powershell
.\build_release.ps1
```

The script installs dependencies, runs the test suite, and builds `dist/AtMd.exe` with PyInstaller. The executable bundles Python, Qt WebEngine, its helper process and local rendering assets; no Python installation is needed on the destination Windows computer. This package is substantially larger than the Rust build because it includes Python and Chromium.

Manual packaging:

```powershell
.\.venv\Scripts\python.exe -m pip install "pyinstaller>=6.10,<7"
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm AtMd.spec
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests exercise the parser, actual Chromium DOM rendering, standalone HTML, malformed diagrams, PDF generation and text extraction, native editing, search, view modes, themes, and unsaved-change protection. Desktop tests use an isolated settings directory and hidden windows. Review artifacts are written to ignored `test-output/`.

To verify the packaged runtime, without opening a visible window or changing personal settings:

```powershell
.\dist\AtMd.exe --smoke-test test-output\release-check.json
```

The check writes a JSON result, screenshot and PDF, and exits with code 0 on success.

See [PORTING_PARITY.md](PORTING_PARITY.md) for the source-to-Python feature mapping.
