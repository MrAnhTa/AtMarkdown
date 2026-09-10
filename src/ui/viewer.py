import json
import tempfile
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView


class PreviewPage(QWebEnginePage):
    link_clicked = Signal(str)

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if navigation_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            if url.hasFragment() and url.adjusted(QUrl.UrlFormattingOption.RemoveFragment) == self.url().adjusted(QUrl.UrlFormattingOption.RemoveFragment):
                return True
            if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in (".md", ".markdown", ".txt"):
                self.link_clicked.emit(url.toLocalFile())
            elif url.scheme() in ("https", "http", "mailto"):
                QDesktopServices.openUrl(url)
            return False
        return True


class MarkdownViewer(QWebEngineView):
    link_clicked = Signal(str)
    scroll_ratio_changed = Signal(float)
    ready = Signal()
    render_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPage(PreviewPage(self))
        self.page().link_clicked.connect(self.link_clicked)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        self.setAcceptDrops(False)
        self._temporary = tempfile.TemporaryDirectory(prefix="atmarkdown-preview-")
        self._generation = 0
        self._ratio = 0.0
        self._loading = False
        self._polls = 0
        self._ready_timer = QTimer(self)
        self._ready_timer.setInterval(50)
        self._ready_timer.timeout.connect(self._check_ready)
        self.loadFinished.connect(self._loaded)
        self.page().scrollPositionChanged.connect(self._scroll_changed)
        self.destroyed.connect(lambda: self._temporary.cleanup())

    def set_html_content(self, html_content, base_url_path=None):
        self._generation += 1
        self._loading = True
        self._ready_timer.stop()
        # Loading a file avoids Qt's 2 MB setHtml/data URL limit.
        path = Path(self._temporary.name) / f"preview-{self._generation}.html"
        path.write_text(html_content, encoding="utf-8")
        self.load(QUrl.fromLocalFile(str(path)))
        self._polls = 0
        self._ready_timer.start()

    def _loaded(self, ok):
        if not ok:
            return  # A newer live render may have cancelled this navigation.
        self._polls = 0
        self._ready_timer.start()

    def _check_ready(self):
        self._polls += 1
        if self._polls > 600:
            self._ready_timer.stop()
            self._loading = False
            self.render_failed.emit("Preview assets did not finish loading within 30 seconds.")
            return
        if self.page().isLoading():
            return
        generation = self._generation
        def checked(value):
            if generation != self._generation or not value or not self._loading:
                return
            self._ready_timer.stop()
            self._loading = False
            self.set_scroll_ratio(self._ratio)
            for old in Path(self._temporary.name).glob("preview-*.html"):
                if old.name != f"preview-{generation}.html":
                    try:
                        old.unlink(missing_ok=True)
                    except OSError:
                        pass  # Retry cleanup after the next render or at shutdown.
            self.ready.emit()
        self.page().runJavaScript("window.atMarkdownReady === true", checked)

    def _scroll_changed(self, _position):
        if self._loading:
            return
        generation = self._generation
        def receive(value):
            if generation != self._generation or self._loading or not isinstance(value, (float, int)) or value < 0:
                return
            self._ratio = max(0.0, min(1.0, value))
            self.scroll_ratio_changed.emit(self._ratio)
        self.page().runJavaScript(
            "window.__atMarkdownProgrammaticScroll ? -1 : window.scrollY / Math.max(1, document.documentElement.scrollHeight - innerHeight)", receive)

    def set_scroll_ratio(self, ratio):
        self._ratio = max(0.0, min(1.0, ratio))
        if self._loading:
            return
        self.page().runJavaScript(
            "window.__atMarkdownProgrammaticScroll = true;"
            f"window.scrollTo(0, {self._ratio} * Math.max(0, document.documentElement.scrollHeight - innerHeight));"
            "requestAnimationFrame(() => requestAnimationFrame(() => {window.__atMarkdownProgrammaticScroll = false;}));")

    def scroll_to_heading(self, anchor_id):
        self.page().runJavaScript(
            f"document.getElementById({json.dumps(anchor_id)})?.scrollIntoView({{behavior:'smooth', block:'start'}});")

    def apply_theme(self, theme="dark"):
        self.page().setBackgroundColor(QColor({"light": "#ffffff", "sepia": "#fbf0d9"}.get(theme, "#0d1117")))
