"""Hidden installation check, also usable from the packaged executable."""
import json
import tempfile
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from src import config as config_module
from src.config import ConfigManager
from src.ui.main_window import MainWindow
from src.utils.exporter import DocumentExporter


def verify_installation(app, report_path):
    report = Path(report_path).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix="atmarkdown-check-")
    config_module.CONFIG_DIR = Path(temporary.name)
    config_module.SETTINGS_FILE = Path(temporary.name) / "settings.json"
    window = MainWindow(ConfigManager())
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.show()
    window.render_timer.stop()
    window.editor.setPlainText('# Installation check\n\n- Math: $$\\frac{a}{b}$$\n\n> [!TIP]\n> Ready\n\n```python\nprint(42)\n```\n\n```mermaid\ngraph TD; A-->B;\n```')
    window.is_modified = False
    window.render_timer.stop()
    window._perform_live_render()
    done = False
    job = None
    timer = QTimer(window)
    timer.setSingleShot(True)

    def finish(success, detail):
        nonlocal done
        if done:
            return
        done = True
        timer.stop()
        if success:
            window.grab().save(str(report.with_suffix('.png')))
        report.write_text(json.dumps({"success": success, "detail": detail}, indent=2), encoding="utf-8")
        window.is_modified = False
        window.close()
        app.exit(0 if success else 1)

    def check_dom(value):
        nonlocal job
        if done:
            return
        counts = json.loads(value or '{}')
        if counts != {"math": 1, "mermaid": 1, "alert": 1, "highlight": 1}:
            finish(False, counts)
            return
        pdf = report.with_suffix('.pdf')
        job = DocumentExporter.export_pdf(window.md_engine.render(window.editor.toPlainText(), theme='light'), str(pdf), window)
        job.finished.connect(lambda ok, message: finish(ok and pdf.exists() and pdf.read_bytes().startswith(b'%PDF'), {"render": counts, "pdf": message}))

    def ready():
        window.viewer.ready.disconnect(ready)
        window.viewer.page().runJavaScript("JSON.stringify({math:document.querySelectorAll('.katex').length,mermaid:document.querySelectorAll('.mermaid svg').length,alert:document.querySelectorAll('.markdown-alert-tip').length,highlight:document.querySelectorAll('.hljs').length})", check_dom)

    window.viewer.ready.connect(ready)
    window.viewer.render_failed.connect(lambda error: finish(False, error))
    timer.timeout.connect(lambda: finish(False, "Installation check timed out"))
    timer.start(90000)
    result = app.exec()
    window.deleteLater()
    app.processEvents()
    temporary.cleanup()
    return result
