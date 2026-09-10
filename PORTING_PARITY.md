# Feature mapping from Rust main

Source: `main` at `d75bd43`. Target: `python-version`, originally `ffdad4d`.

| Main implementation | Python implementation |
| --- | --- |
| `src/commands.rs`: file dialogs, reading/writing, welcome document | `src/ui/main_window.py`, `src/assets/welcome.md` |
| `src/config.rs`: theme and recent files | `src/config.py`, native theme controls |
| `src/markdown.rs`: Markdown parsing, heading IDs/attributes, footnotes and source lines | `src/utils/md_parser.py`, markdown-it-py and mdit-py-plugins |
| `src/markdown.rs`: preview CSS, math, highlighting, Mermaid, alerts, copy buttons | `src/assets/preview/preview.css`, `preview.js`, `vendor/`; hosted by `src/ui/viewer.py` |
| `src/stats.rs`: document statistics | `MarkdownEngine.calculate_stats`, `src/ui/stats_bar.py` |
| `ui/js/app.js`: new/open/save/save as, recent files, export | Native menus and dialogs in `src/ui/main_window.py` |
| `ui/js/app.js`: modes, sidebar, splitters, scroll synchronization | Native QSplitter and paired editor/WebEngine scrolling |
| `ui/js/editor.js`: gutter, find, tab insertion | `src/ui/editor.py` |
| `ui/js/formatting.js` and `ui/index.html`: formatting toolbar | `src/ui/formatting_bar.py` |
| Main's browser print/PDF flow | `src/utils/exporter.py`: asynchronous Chromium printToPdf with render readiness |
| Release packaging | `AtMd.spec`, `build_release.ps1`: unsigned PyInstaller executable |

The Python implementation keeps native Qt widgets for editing and application controls. Only document presentation uses browser JavaScript, just as in the Rust/Tauri version; there is no Rust backend or Tauri runtime dependency.

Corrections made while porting: complete offline KaTeX fonts, embedded HTML assets/images, duplicate and setext outline headings, recent-file unsaved-change handling, failed Save As path restoration, backward search, full-shell themes, and PDF pagination/readability. No signing scripts, certificates, publisher installation or signing instructions are included.

Preview checkboxes are transient browser controls, matching main; they do not write back to Markdown. Search is find-only, matching main. Large/complex documents and diagrams take longer to render; PDF export reports a timeout rather than silently producing an incomplete file.
