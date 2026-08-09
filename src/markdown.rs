use pulldown_cmark::{html, Options, Parser};
use regex::Regex;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HeadingItem {
    pub level: usize,
    pub title: String,
    pub id: String,
    pub line_number: usize,
}

pub struct MarkdownEngine;

impl MarkdownEngine {
    pub fn render(md_text: &str, theme: &str) -> String {
        let mut options = Options::empty();
        options.insert(Options::ENABLE_TABLES);
        options.insert(Options::ENABLE_FOOTNOTES);
        options.insert(Options::ENABLE_STRIKETHROUGH);
        options.insert(Options::ENABLE_TASKLISTS);
        options.insert(Options::ENABLE_HEADING_ATTRIBUTES);

        let parser = Parser::new_ext(md_text, options);
        let mut body_html = String::new();
        html::push_html(&mut body_html, parser);

        // Inject unique id="toc-heading-N" to all <h1..6> tags in HTML output
        let re_tag = Regex::new(r"(?i)<(h[1-6])([^>]*)>").unwrap();
        let mut heading_count = 0;
        let body_html_with_ids = re_tag.replace_all(&body_html, |caps: &regex::Captures| {
            let tag = &caps[1];
            let attrs = &caps[2];
            let id = format!("toc-heading-{}", heading_count);
            heading_count += 1;
            format!("<{} id=\"{}\"{}>", tag, id, attrs)
        }).to_string();

        let theme_class = match theme {
            "light" => "theme-light",
            "sepia" => "theme-sepia",
            _ => "theme-dark",
        };

        format!(
            "<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n<style>\n{}\n</style>\n</head>\n<body class=\"{}\">\n<div class=\"markdown-body\">\n{}\n</div>\n<div class=\"pdf-footer\"><span class=\"pdf-page-number\"></span></div>\n<script>\ndocument.addEventListener(\"DOMContentLoaded\", function() {{\n    const codeBlocks = document.querySelectorAll(\"pre\");\n    codeBlocks.forEach(function(pre) {{\n        const wrapper = document.createElement(\"div\");\n        wrapper.className = \"code-block-wrapper\";\n        pre.parentNode.insertBefore(wrapper, pre);\n        wrapper.appendChild(pre);\n\n        const btn = document.createElement(\"button\");\n        btn.className = \"copy-code-btn\";\n        btn.innerHTML = `<svg width=\"14\" height=\"14\" viewBox=\"0 0 16 16\" fill=\"currentColor\"><path fill-rule=\"evenodd\" d=\"M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z\"></path><path fill-rule=\"evenodd\" d=\"M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z\"></path></svg> Copy`;\n        \n        btn.addEventListener(\"click\", function() {{\n            const codeText = pre.innerText || pre.textContent;\n            navigator.clipboard.writeText(codeText).then(function() {{\n                btn.innerHTML = `<svg width=\"14\" height=\"14\" viewBox=\"0 0 16 16\" fill=\"#3fb950\"><path fill-rule=\"evenodd\" d=\"M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z\"></path></svg> Copied!`;\n                setTimeout(function() {{\n                    btn.innerHTML = `<svg width=\"14\" height=\"14\" viewBox=\"0 0 16 16\" fill=\"currentColor\"><path fill-rule=\"evenodd\" d=\"M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z\"></path><path fill-rule=\"evenodd\" d=\"M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z\"></path></svg> Copy`;\n                }}, 2000);\n            }});\n        }});\n        wrapper.appendChild(btn);\n    }});\n\n    // Ensure mouse wheel scrolling works reliably inside preview iframe\n    window.addEventListener(\"wheel\", function(e) {{\n        if (e.deltaY) {{\n            window.scrollBy(0, e.deltaY);\n        }}\n    }}, {{ passive: true }});\n\n    // Report scroll position to parent window for synchronized scrolling\n    let isPosting = false;\n    window.addEventListener(\"scroll\", function() {{\n        if (!isPosting) {{\n            isPosting = true;\n            requestAnimationFrame(function() {{\n                try {{\n                    if (window.parent && window.parent !== window) {{\n                        const doc = document.documentElement;\n                        const maxScroll = doc.scrollHeight - window.innerHeight;\n                        const ratio = maxScroll > 0 ? window.scrollY / maxScroll : 0;\n                        window.parent.postMessage({{ type: \"READER_SCROLL\", ratio: ratio }}, \"*\");\n                    }}\n                }} catch(e) {{}}\n                isPosting = false;\n            }});\n        }}\n    }});\n}});\n</script>\n</body>\n</html>",
            Self::get_theme_css(),
            theme_class,
            body_html_with_ids
        )
    }

    pub fn extract_toc(md_text: &str) -> Vec<HeadingItem> {
        let mut headings = Vec::new();
        let re_clean_md = Regex::new(r"[*_`\[\]]|https?://\S+").unwrap();
        let mut heading_count = 0;

        let mut in_code_block = false;
        for (idx, line) in md_text.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.starts_with("```") || trimmed.starts_with("~~~") {
                in_code_block = !in_code_block;
                continue;
            }
            if in_code_block {
                continue;
            }

            if trimmed.starts_with('#') {
                let mut hashes = 0;
                for ch in trimmed.chars() {
                    if ch == '#' {
                        hashes += 1;
                    } else {
                        break;
                    }
                }

                if hashes >= 1 && hashes <= 6 {
                    let rest = trimmed[hashes..].trim();
                    if !rest.is_empty() {
                        let clean_title = re_clean_md.replace_all(rest, "").trim().to_string();
                        let display_title = if clean_title.is_empty() { rest.to_string() } else { clean_title };

                        headings.push(HeadingItem {
                            level: hashes,
                            title: display_title,
                            id: format!("toc-heading-{}", heading_count),
                            line_number: idx + 1,
                        });
                        heading_count += 1;
                    }
                }
            }
        }

        headings
    }

    fn get_theme_css() -> &'static str {
        r#"
html {
    height: 100%;
    overflow-y: auto;
    scroll-behavior: smooth;
}
:root {
    --bg-dark: #0d1117; --text-dark: #e6edf3; --muted-dark: #8b949e; --border-dark: #30363d; --code-dark: #161b22; --link-dark: #2f81f7;
    --bg-light: #ffffff; --text-light: #1f2328; --muted-light: #656d76; --border-light: #d0d7de; --code-light: #f6f8fa; --link-light: #0969da;
    --bg-sepia: #fbf0d9; --text-sepia: #5f4b32; --muted-sepia: #7f6a4e; --border-sepia: #e0d0b0; --code-sepia: #f2e3c6; --link-sepia: #924500;
}
body { margin: 0; padding: 32px 40px; min-height: 100%; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.5; word-wrap: break-word; }
body.theme-dark { background-color: var(--bg-dark); color: var(--text-dark); }
body.theme-light { background-color: var(--bg-light); color: var(--text-light); }
body.theme-sepia { background-color: var(--bg-sepia); color: var(--text-sepia); }

body.theme-dark a { color: var(--link-dark); }
body.theme-light a { color: var(--link-light); }
body.theme-sepia a { color: var(--link-sepia); }

h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; scroll-margin-top: 16px; }
h1 { font-size: 2em; padding-bottom: 0.3em; border-bottom: 1px solid currentColor; opacity: 0.9; }
h2 { font-size: 1.5em; padding-bottom: 0.3em; border-bottom: 1px solid currentColor; opacity: 0.9; }
h3 { font-size: 1.25em; }

/* Inline Code Pill styling */
:not(pre) > code {
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    font-size: 85%;
    padding: 0.2em 0.4em;
    border-radius: 6px;
}
body.theme-dark :not(pre) > code { background-color: rgba(110, 118, 129, 0.4); }
body.theme-light :not(pre) > code { background-color: rgba(175, 184, 193, 0.2); }
body.theme-sepia :not(pre) > code { background-color: rgba(146, 69, 0, 0.12); }

/* Fenced Code Block styling */
pre { padding: 16px; overflow: auto; font-size: 85%; line-height: 1.45; border-radius: 6px; margin: 0 0 16px 0; }
body.theme-dark pre { background-color: var(--code-dark); border: 1px solid var(--border-dark); }
body.theme-light pre { background-color: var(--code-light); border: 1px solid var(--border-light); }
body.theme-sepia pre { background-color: var(--code-sepia); border: 1px solid var(--border-sepia); }

pre code, pre code * {
    background-color: transparent !important;
    padding: 0 !important;
    border-radius: 0 !important;
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    font-size: 100%;
}

.code-block-wrapper { position: relative; margin-bottom: 16px; }
.copy-code-btn { position: absolute; top: 8px; right: 8px; background-color: #21262d; color: #8b949e; border: 1px solid #30363d; border-radius: 6px; padding: 3px 8px; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 4px; opacity: 0.8; }
.copy-code-btn:hover { opacity: 1; color: #ffffff; }

table { border-spacing: 0; border-collapse: collapse; width: 100%; margin-bottom: 16px; }
table th, table td { padding: 6px 13px; border: 1px solid currentColor; opacity: 0.8; }
blockquote { padding: 0 1em; border-left: 0.25em solid currentColor; opacity: 0.8; margin: 0 0 16px 0; }
ul, ol { padding-left: 2em; margin-bottom: 16px; }
img { max-width: 100%; border-radius: 6px; }

@media print {
    @page {
        margin: 12mm 15mm 15mm 15mm;
        @top-left { content: ""; }
        @top-center { content: ""; }
        @top-right { content: ""; }
        @bottom-left { content: ""; }
        @bottom-center { content: ""; }
        @bottom-right {
            content: counter(page);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
            font-size: 10pt;
            color: #555555;
        }
    }

    body {
        margin: 0 !important;
        padding: 0 !important;
        background-color: #ffffff !important;
        color: #1f2328 !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }

    body.theme-dark, body.theme-sepia, body.theme-light {
        background-color: #ffffff !important;
        color: #1f2328 !important;
    }

    body.theme-dark a, body.theme-sepia a, body.theme-light a {
        color: #0969da !important;
    }

    .markdown-body {
        padding: 0 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #1f2328 !important;
        page-break-after: avoid;
        break-after: avoid;
    }

    pre {
        background-color: #f6f8fa !important;
        border: 1px solid #d0d7de !important;
        page-break-inside: avoid;
        break-inside: avoid;
    }

    table, blockquote, img {
        page-break-inside: avoid;
        break-inside: avoid;
    }

    .copy-code-btn, .pdf-footer {
        display: none !important;
    }
}
"#
    }
}



