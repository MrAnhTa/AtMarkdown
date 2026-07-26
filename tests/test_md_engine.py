import unittest
from src.utils.md_parser import MarkdownEngine


class TestMarkdownEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MarkdownEngine()

    def test_markdown_rendering(self):
        md_text = "# Header 1\n\nThis is **bold** text and `code`."
        html_dark = self.engine.render(md_text, theme="dark")
        html_light = self.engine.render(md_text, theme="light")
        
        self.assertIn("Header 1", html_dark)
        self.assertIn("<strong>bold</strong>", html_dark)
        self.assertIn("code", html_dark)
        self.assertIn("var(--bg-color)", html_dark)

    def test_toc_extraction(self):
        md_text = "# Main Title\n\n## Sub Section 1\n\n### Detail A\n\n## Sub Section 2"
        headings = self.engine.extract_toc(md_text)
        
        self.assertEqual(len(headings), 4)
        self.assertEqual(headings[0]["title"], "Main Title")
        self.assertEqual(headings[0]["level"], 1)
        self.assertEqual(headings[1]["title"], "Sub Section 1")
        self.assertEqual(headings[1]["level"], 2)

    def test_stats_calculation(self):
        md_text = "Line 1\nLine 2\nLine 3 word word"
        stats = self.engine.calculate_stats(md_text)
        
        self.assertEqual(stats["lines"], 3)
        self.assertEqual(stats["words"], 8)
        self.assertGreater(stats["chars"], 10)


if __name__ == "__main__":
    unittest.main()
