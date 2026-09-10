import re
import tempfile
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from src.utils.md_parser import MarkdownEngine, ASSETS, katex_css


class FeatureParityTests(unittest.TestCase):
    def setUp(self):
        self.engine = MarkdownEngine()

    def test_outline_uses_rendered_headings_and_source_lines(self):
        text = '# **One**\n\n```md\n# Not a heading\n```\n\n# One\n\nSetext\n------\n'
        headings = self.engine.extract_toc(text)
        self.assertEqual([h['title'] for h in headings], ['One', 'One', 'Setext'])
        self.assertEqual([h['line_number'] for h in headings], [1, 7, 9])
        soup = BeautifulSoup(self.engine.render(text), 'html.parser')
        self.assertEqual([h['id'] for h in headings], [h['id'] for h in soup.select('h1,h2')])

    def test_math_nested_contexts_and_code_are_preserved(self):
        text = r'''Inline $x_1^2$ and \(y^2\).

- Formula $\frac{a}{b}$

> $$x+y$$

| Equation |
| --- |
| $z_1$ |

```python
cost = "$20"
```

```mermaid
graph TD; A-->B;
```
'''
        soup = BeautifulSoup(self.engine.render(text), 'html.parser')
        self.assertEqual(len(soup.select('.math-inline')), 4)
        self.assertTrue(soup.select('blockquote .math-display'))
        self.assertIn('cost = "$20"', soup.select_one('code.language-python').text)
        self.assertIn('A-->B', soup.select_one('code.language-mermaid').text)

    def test_gfm_and_raw_html(self):
        soup = BeautifulSoup(self.engine.render('- [x] Done\n- [ ] Todo\n\n~~removed~~ <kbd>Ctrl</kbd>\n\n> [!TIP]\n> Tip\n\n<script>bad()</script><img src="x" onerror="bad()">'), 'html.parser')
        body = soup.select_one('.markdown-body')
        self.assertEqual(len(body.select('input[type=checkbox]')), 2)
        self.assertIsNotNone(body.select_one('input[checked]'))
        self.assertIsNotNone(body.select_one('s,kbd'))
        self.assertFalse(body.select('script,[onerror]'))

    def test_main_welcome_display_math_in_list(self):
        welcome = (ASSETS.parent / 'welcome.md').read_text(encoding='utf-8')
        soup = BeautifulSoup(self.engine.render(welcome), 'html.parser')
        equations = soup.select('li .math-display')
        self.assertEqual(len(equations), 2)
        self.assertTrue(all('$' not in equation.text for equation in equations))

    def test_heading_attributes_and_footnotes(self):
        text = '# **Title** {#custom .accent}\n\nA note[^1].\n\n[^1]: Footnote text\n\n# Another {#custom}'
        headings = self.engine.extract_toc(text)
        self.assertEqual([h['id'] for h in headings], ['custom', 'custom-1'])
        self.assertEqual(headings[0]['title'], 'Title')
        soup = BeautifulSoup(self.engine.render(text), 'html.parser')
        self.assertIsNotNone(soup.select_one('h1#custom.accent'))
        self.assertIn('Footnote text', soup.select_one('.footnotes').text)

    def test_standalone_has_no_external_library_or_font_files(self):
        soup = BeautifulSoup(self.engine.render('$x$', standalone=True), 'html.parser')
        self.assertFalse(soup.select('script[src],link[href]'))
        self.assertNotIn('url(fonts/', katex_css())
        self.assertIn('data:font/woff2;base64,', str(soup))

    def test_local_image_paths_and_embedded_export(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'image space.png').write_bytes(b'fake image')
            md = '![test](image%20space.png)'
            preview = self.engine.render(md, base_url_path=str(folder / 'doc.md'))
            self.assertIn((folder / 'image space.png').as_uri(), preview)
            exported = self.engine.render(md, base_url_path=str(folder / 'doc.md'), standalone=True)
            self.assertIn('data:image/png;base64,', exported)

    def test_all_css_fonts_exist(self):
        css = (ASSETS / 'vendor/katex/katex.min.css').read_text()
        fonts = re.findall(r'url\((fonts/[^)]+\.woff2)\)', css)
        self.assertTrue(fonts)
        self.assertEqual([], [font for font in fonts if not (ASSETS / 'vendor/katex' / font).exists()])
