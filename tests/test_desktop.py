"""Real Chromium rendering, PDF export and native editor regression tests."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'windows' if os.name == 'nt' else 'offscreen')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--disable-gpu')
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QEventLoop
from src.ui.viewer import MarkdownViewer
from src.ui.main_window import MainWindow
from src.utils.md_parser import MarkdownEngine
from src.utils.exporter import DocumentExporter
from src.config import ConfigManager

APP = QApplication.instance() or QApplication([])


def wait_until(predicate, timeout=35):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        APP.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        if predicate():
            return
        time.sleep(.01)
    raise AssertionError('Timed out waiting for Qt/Chromium')


def javascript(viewer, script):
    result = []
    viewer.page().runJavaScript(script, result.append)
    wait_until(lambda: bool(result))
    return result[0]


class DesktopTests(unittest.TestCase):
    def test_real_rendering_and_pdf(self):
        engine = MarkdownEngine()
        md = '# Preview\n\n$\\frac{a}{b}$\n\n> [!TIP]\n> Helpful\n\n```python\nprint(42)\n```\n\n```mermaid\ngraph TD; A-->B;\n```\n\n- [x] Done\n'
        viewer = MarkdownViewer()
        viewer.resize(1000, 800)
        ready = []
        viewer.ready.connect(lambda: ready.append(True))
        try:
            viewer.set_html_content(engine.render(md))
            wait_until(lambda: ready)
            result = javascript(viewer, "JSON.stringify({math:document.querySelectorAll('.katex').length,diagram:document.querySelectorAll('.mermaid svg').length,alert:document.querySelectorAll('.markdown-alert-tip').length,code:document.querySelectorAll('.hljs').length,copy:document.querySelectorAll('.copy-code-btn').length,task:document.querySelectorAll('input:checked').length})")
            import json
            self.assertEqual(json.loads(result), dict(math=1, diagram=1, alert=1, code=1, copy=1, task=1))
            # A standalone document exceeds setHtml's 2 MB limit and must still load.
            ready.clear()
            viewer.set_html_content(engine.render(md, standalone=True))
            wait_until(lambda: ready)
            self.assertEqual(javascript(viewer, "document.querySelectorAll('.mermaid svg').length"), 1)
            self.assertEqual(javascript(viewer, "document.querySelectorAll('.katex').length"), 1)
            # Invalid diagrams should display an error without blocking the rest.
            ready.clear()
            viewer.set_html_content(engine.render('```mermaid\nnot a diagram\n```\n\n$y$'))
            wait_until(lambda: ready)
            self.assertEqual(javascript(viewer, "document.querySelectorAll('.katex').length"), 1)
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'test.pdf'
                finished = []
                job = DocumentExporter.export_pdf(engine.render(md, theme='light'), str(output))
                job.finished.connect(lambda ok, message: finished.append((ok, message)))
                wait_until(lambda: finished)
                self.assertTrue(finished[0][0], finished)
                self.assertTrue(output.read_bytes().startswith(b'%PDF'))
                self.assertGreater(output.stat().st_size, 10000)
                artifacts = Path('test-output')
                artifacts.mkdir(exist_ok=True)
                (artifacts / 'feature-preview.pdf').write_bytes(output.read_bytes())
                from PySide6.QtPdf import QPdfDocument
                from PySide6.QtCore import QSize
                pdf = QPdfDocument()
                pdf.load(str(artifacts / 'feature-preview.pdf'))
                self.assertEqual(pdf.pageCount(), 1)
                self.assertIn('Preview', pdf.getAllText(0).text())
                pdf.render(0, QSize(900, 1200)).save(str(artifacts / 'feature-preview-pdf.png'))
                pdf.close()
                del pdf
        finally:
            viewer.deleteLater()
            APP.processEvents()

    def test_window_editing_files_modes_and_search(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch('src.config.CONFIG_DIR', Path(directory)), \
             patch('src.config.SETTINGS_FILE', Path(directory) / 'settings.json'):
            window = MainWindow(ConfigManager())
            try:
                self.assertFalse(window.is_modified)
                doc = Path(directory) / 'doc.md'
                doc.write_text('# Heading\n\nneedle\nneedle', encoding='utf-8')
                window.open_file(str(doc))
                self.assertFalse(window.is_modified)
                window._apply_view_mode('editor')
                self.assertTrue(window.viewer.isHidden())
                window._apply_view_mode('reader')
                self.assertTrue(window.editor_container.isHidden())
                window._show_search()
                self.assertEqual(window.config.get('view_mode'), 'split')
                window.search_panel.search_input.setText('needle')
                window.search_panel.search_prev()
                self.assertEqual(window.editor.textCursor().selectedText(), 'needle')
                window.editor.insertPlainText('changed')
                self.assertTrue(window.is_modified)
                with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Cancel):
                    window.open_file(str(doc))
                    self.assertIn('changed', window.editor.toPlainText())
                self.assertTrue(window.save_file())
                self.assertIn('changed', doc.read_text())
                self.assertFalse(window.is_modified)
                window._on_toc_heading_selected('toc-heading-0')
                self.assertEqual(window.editor.textCursor().blockNumber(), 0)
                for theme in ('light', 'sepia', 'dark'):
                    window._apply_theme(theme)
                    self.assertEqual(window.config.get('theme'), theme)
                from PySide6.QtCore import Qt
                window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
                window.show()
                window._load_sample_welcome_doc()
                window._perform_live_render()
                wait_until(lambda: not window.viewer._loading)
                artifacts = Path('test-output')
                artifacts.mkdir(exist_ok=True)
                window.grab().save(str(artifacts / 'desktop-dark.png'))
                # Both panes must actually scroll, including the editor viewport.
                window.editor.setPlainText('\n\n'.join(f'## Section {i}\n\nParagraph {i}' for i in range(100)))
                window.render_timer.stop()
                window._perform_live_render()
                wait_until(lambda: not window.viewer._loading)
                javascript(window.viewer, 'window.scrollTo(0, (document.documentElement.scrollHeight-innerHeight)*0.5)')
                bar = window.editor.verticalScrollBar()
                wait_until(lambda: .45 < bar.value() / max(1, bar.maximum()) < .55)
                self.assertGreater(window.editor.firstVisibleBlock().blockNumber(), 0)
                bar.setValue(bar.maximum())
                wait_until(lambda: window.viewer.page().scrollPosition().y() > .9 * (window.viewer.page().contentsSize().height() - window.viewer.height()))
                self.assertGreater(javascript(window.viewer, 'scrollY / (document.documentElement.scrollHeight-innerHeight)'), .9)
            finally:
                window.is_modified = False
                window.close()
                window.deleteLater()
                APP.processEvents()
