"""Python Markdown engine with offline presentation assets ported from main."""
import base64
import html
import mimetypes
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import bleach
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.texmath import texmath_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.deflist import deflist_plugin

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "preview"


def math_environment(state, silent):
    match = re.match(r"\\begin\{(equation\*?|align\*?|alignat\*?|gather\*?|CD)\}.*?\\end\{\1\}",
                     state.src[state.pos:], re.DOTALL)
    if not match:
        return False
    if not silent:
        token = state.push("math_environment", "span", 0)
        token.content = match[0]
    state.pos += len(match[0])
    return True


@lru_cache(maxsize=32)
def asset(name):
    return (ASSETS / name).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def katex_css():
    def embed(match):
        path = ASSETS / "vendor/katex" / match[1]
        if path.exists():
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            return f'url(data:font/woff2;base64,{data})'
        return match[0]
    css = asset("vendor/katex/katex.min.css")
    css = re.sub(r',url\([^)]*\) format\("(?:woff|truetype)"\)', '', css)
    return re.sub(r'url\((fonts/[^)]+)\)', embed, css)


class MarkdownEngine:
    def __init__(self):
        self.parser = MarkdownIt("commonmark", {"html": True, "breaks": True})
        self.parser.enable(["table", "strikethrough"])
        self.parser.use(dollarmath_plugin, allow_space=True, allow_digits=True, double_inline=True)
        self.parser.use(texmath_plugin, delimiters="brackets")
        self.parser.use(tasklists_plugin, enabled=True)
        self.parser.use(footnote_plugin)
        self.parser.use(deflist_plugin)
        self.parser.inline.ruler.before("escape", "math_environment", math_environment)
        for kind, display in (("math_inline", False), ("math_block", True),
                              ("math_block_eqno", True), ("math_environment", True),
                              ("math_inline_double", True)):
            def render_math(tokens, idx, options, env, is_display=display):
                cls = "math-display" if is_display else "math-inline"
                return f'<span class="{cls}">{html.escape(tokens[idx].content)}</span>'
            self.parser.renderer.rules[kind] = render_math

    def _parse(self, text):
        tokens = self.parser.parse(text)
        headings = []
        used_ids = set()
        for index, token in enumerate(tokens):
            if token.type != "heading_open":
                continue
            inline = tokens[index + 1]
            attributes = re.search(r'\s+\{([#.][^{}]*)\}\s*$', inline.content)
            custom_id = None
            if attributes:
                classes = []
                for item in attributes[1].split():
                    if item.startswith('#'):
                        custom_id = item[1:]
                    elif item.startswith('.'):
                        classes.append(item[1:])
                if classes:
                    token.attrSet('class', ' '.join(classes))
                inline.content = inline.content[:attributes.start()]
                inline.children = self.parser.parseInline(inline.content)[0].children
            title = "".join(t.content for t in inline.children or []
                            if t.type in ("text", "code_inline", "math_inline", "image"))
            anchor = custom_id or f"toc-heading-{len(headings)}"
            original_anchor = anchor
            suffix = 1
            while anchor in used_ids:
                anchor = f"{original_anchor}-{suffix}"
                suffix += 1
            used_ids.add(anchor)
            token.attrSet("id", anchor)
            headings.append({"level": int(token.tag[1]), "title": title,
                             "id": anchor, "line_number": token.map[0] + 1})
        return tokens, headings

    def extract_toc(self, md_text):
        return self._parse(md_text)[1]

    def render(self, md_text, theme="dark", base_url_path=None, standalone=False):
        tokens, _ = self._parse(md_text)
        body = self.parser.renderer.render(tokens, self.parser.options, {})
        body = re.sub(r'style="text-align:(left|center|right)"', r'align="\1"', body)
        body = bleach.clean(body, tags={
            "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "a", "img",
            "strong", "em", "del", "s", "code", "pre", "blockquote", "ul", "ol", "li",
            "table", "thead", "tbody", "tr", "th", "td", "input", "span", "div", "kbd",
            "details", "summary", "sup", "sub", "dl", "dt", "dd", "mark", "section",
        }, attributes={"*": ["id", "class", "title"], "a": ["href"],
                       "img": ["src", "alt", "width", "height"],
                       "input": ["type", "checked", "disabled"],
                       "ol": ["start"], "th": ["align"], "td": ["align"]},
            protocols={"http", "https", "mailto", "file", "data"}, strip=True)
        base = Path(base_url_path).resolve().parent if base_url_path else Path.cwd()
        soup = BeautifulSoup(body, "html.parser")
        for element in soup.select("img[src], a[href]"):
            attr = "src" if element.name == "img" else "href"
            value = element[attr]
            if value.startswith("#"):
                continue
            resolved = urljoin(base.as_uri() + "/", value.replace("\\", "/"))
            parsed = urlparse(resolved)
            if standalone and element.name == "img" and parsed.scheme == "file":
                local = unquote(parsed.path)
                if re.match(r"^/[A-Za-z]:", local):
                    local = local[1:]
                path = Path(local)
                if path.is_file():
                    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                    resolved = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
            element[attr] = resolved
        theme = theme if theme in ("dark", "light", "sepia") else "dark"
        highlight = "github-dark" if theme == "dark" else "github"
        styles = asset("preview.css")
        scripts = ""
        if standalone:
            styles += katex_css() + asset(f"vendor/highlight/{highlight}.min.css")
            for name in ("katex/katex.min.js", "katex/auto-render.min.js",
                         "highlight/highlight.min.js", "mermaid/mermaid.min.js"):
                scripts += "<script>" + asset("vendor/" + name).replace("</script", "<\\/script") + "</script>"
        else:
            for name in ("katex/katex.min.css", f"highlight/{highlight}.min.css"):
                scripts += f'<link rel="stylesheet" href="{(ASSETS / "vendor" / name).as_uri()}">'
            for name in ("katex/katex.min.js", "katex/auto-render.min.js",
                         "highlight/highlight.min.js", "mermaid/mermaid.min.js"):
                scripts += f'<script src="{(ASSETS / "vendor" / name).as_uri()}"></script>'
        return (f'<!DOCTYPE html><html><head><meta charset="utf-8">{scripts}'
                f'<style>{styles}</style></head><body class="theme-{theme}">'
                f'<div class="markdown-body">{soup}</div>'
                f'<div class="pdf-footer"><span class="pdf-page-number"></span></div>'
                f'<script>{asset("preview.js")}</script></body></html>')

    def calculate_stats(self, text):
        words = len(re.findall(r"\b\w+\b", text))
        return {"lines": len(text.splitlines()) if text else 0, "words": words,
                "chars": len(text), "reading_time": max(1, round(words / 200)) if words else 0}
