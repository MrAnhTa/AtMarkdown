import re
from typing import List, Dict, Tuple, Any
import markdown
from pygments.formatters import HtmlFormatter


# Standard CSS styling for preview HTML
GITHUB_DARK_CSS = """
:root {
    --bg-color: #0d1117;
    --text-color: #c9d1d9;
    --heading-color: #58a6ff;
    --link-color: #58a6ff;
    --code-bg: #161b22;
    --border-color: #30363d;
    --table-header-bg: #161b22;
    --table-alt-bg: #161b22;
    --quote-border: #30363d;
    --quote-color: #8b949e;
}
"""

GITHUB_LIGHT_CSS = """
:root {
    --bg-color: #ffffff;
    --text-color: #24292f;
    --heading-color: #0969da;
    --link-color: #0969da;
    --code-bg: #f6f8fa;
    --border-color: #d0d7de;
    --table-header-bg: #f6f8fa;
    --table-alt-bg: #f6f8fa;
    --quote-border: #d0d7de;
    --quote-color: #57606a;
}
"""

SEPIA_CSS = """
:root {
    --bg-color: #fbf0d9;
    --text-color: #5f4b32;
    --heading-color: #924500;
    --link-color: #924500;
    --code-bg: #f2e3c6;
    --border-color: #e0d0b0;
    --table-header-bg: #f2e3c6;
    --table-alt-bg: #f2e3c6;
    --quote-border: #d5c3a3;
    --quote-color: #7f6a4e;
}
"""

BASE_PREVIEW_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{theme_variables}

* {{
    box-sizing: border-box;
}}

body {{
    background-color: var(--bg-color);
    color: var(--text-color);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.65;
    padding: 24px 36px;
    margin: 0 auto;
    max-width: 960px;
    word-wrap: break-word;
}}

h1, h2, h3, h4, h5, h6 {{
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
    color: var(--heading-color);
}}

h1 {{ font-size: 2em; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3em; }}
h2 {{ font-size: 1.5em; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3em; }}
h3 {{ font-size: 1.25em; }}
h4 {{ font-size: 1em; }}

a {{
    color: var(--link-color);
    text-decoration: none;
}}
a:hover {{
    text-decoration: underline;
}}

p, ul, ol, dl, table, pre, blockquote {{
    margin-top: 0;
    margin-bottom: 16px;
}}

code {{
    font-family: "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace;
    font-size: 85%;
    background-color: var(--code-bg);
    padding: 0.2em 0.4em;
    border-radius: 6px;
}}

pre {{
    font-family: "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace;
    background-color: var(--code-bg);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 16px;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
}}

pre code {{
    background-color: transparent;
    padding: 0;
    font-size: 100%;
    border-radius: 0;
}}

blockquote {{
    padding: 0 1em;
    color: var(--quote-color);
    border-left: 0.25em solid var(--quote-border);
    margin-left: 0;
}}

hr {{
    height: 0.25em;
    padding: 0;
    margin: 24px 0;
    background-color: var(--border-color);
    border: 0;
}}

table {{
    border-spacing: 0;
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 16px;
}}

table th, table td {{
    padding: 8px 13px;
    border: 1px solid var(--border-color);
}}

table th {{
    font-weight: 600;
    background-color: var(--table-header-bg);
}}

table tr:nth-child(2n) {{
    background-color: var(--table-alt-bg);
}}

img {{
    max-width: 100%;
    box-sizing: content-box;
    border-radius: 6px;
}}

input[type="checkbox"] {{
    margin-right: 0.5em;
}}

{pygments_css}
</style>
</head>
<body>
{content}
</body>
</html>
"""


class MarkdownEngine:
    def __init__(self):
        self.formatter_dark = HtmlFormatter(style="monokai")
        self.formatter_light = HtmlFormatter(style="default")
        self.pygments_css_dark = self.formatter_dark.get_style_defs('.codehilite')
        self.pygments_css_light = self.formatter_light.get_style_defs('.codehilite')

    def render(self, md_text: str, theme: str = "dark") -> str:
        """Converts Markdown text to full HTML string with theme styles."""
        if theme == "light":
            theme_vars = GITHUB_LIGHT_CSS
            pygments_css = self.pygments_css_light
        elif theme == "sepia":
            theme_vars = SEPIA_CSS
            pygments_css = self.pygments_css_light
        else:
            theme_vars = GITHUB_DARK_CSS
            pygments_css = self.pygments_css_dark

        md = markdown.Markdown(
            extensions=[
                'fenced_code',
                'codehilite',
                'tables',
                'toc',
                'nl2br',
                'sane_lists'
            ]
        )
        
        body_html = md.convert(md_text)

        full_html = BASE_PREVIEW_TEMPLATE.format(
            theme_variables=theme_vars,
            pygments_css=pygments_css,
            content=body_html
        )
        return full_html

    def extract_toc(self, md_text: str) -> List[Dict[str, Any]]:
        """
        Extracts headings (#, ##, ###) for the Table of Contents tree view.
        Returns list of dicts with 'level', 'title', and 'id'.
        """
        headings = []
        heading_re = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        for match in heading_re.finditer(md_text):
            hashes, title = match.groups()
            level = len(hashes)
            # Create URL-friendly anchor ID
            anchor_id = re.sub(r'[^\w\- ]', '', title).strip().lower().replace(' ', '-')
            headings.append({
                "level": level,
                "title": title.strip(),
                "id": anchor_id
            })
        return headings

    def calculate_stats(self, text: str) -> Dict[str, int]:
        """Calculates document statistics: lines, words, chars, reading time."""
        lines = len(text.splitlines()) if text else 0
        words = len(re.findall(r'\b\w+\b', text))
        chars = len(text)
        # Average reading speed: 200 words per minute
        reading_time_min = max(1, round(words / 200)) if words > 0 else 0
        return {
            "lines": lines,
            "words": words,
            "chars": chars,
            "reading_time": reading_time_min
        }
