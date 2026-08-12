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

const PREVIEW_SCRIPT: &str = r##"
document.addEventListener("DOMContentLoaded", function() {
    // 1. Un-wrap code blocks that contain math ($$ ... $$, \[ ... \], or math languages)
    document.querySelectorAll("pre code").forEach(function(code) {
        const text = code.textContent.trim();
        const isMathLang = code.classList.contains("language-math") || 
                           code.classList.contains("language-katex") || 
                           code.classList.contains("language-latex");
        if (isMathLang || (text.startsWith("$$") && text.endsWith("$$")) || (text.startsWith("\\[") && text.endsWith("\\]"))) {
            const pre = code.parentElement;
            const div = document.createElement("div");
            div.className = "math-display-block";
            div.textContent = text;
            pre.parentNode.replaceChild(div, pre);
        }
    });

    // 2. Render KaTeX math (direct pulldown_cmark elements + auto-render fallback)
    if (typeof katex !== "undefined") {
        document.querySelectorAll(".math-display, span.math-display").forEach(function(el) {
            if (!el.dataset.katexRendered) {
                const text = el.textContent;
                katex.render(text, el, { displayMode: true, throwOnError: false });
                el.dataset.katexRendered = "true";
            }
        });
        document.querySelectorAll(".math-inline, span.math-inline").forEach(function(el) {
            if (!el.dataset.katexRendered) {
                const text = el.textContent;
                katex.render(text, el, { displayMode: false, throwOnError: false });
                el.dataset.katexRendered = "true";
            }
        });
        document.querySelectorAll(".math-display-block").forEach(function(el) {
            if (!el.dataset.katexRendered) {
                let text = el.textContent.trim();
                if (text.startsWith("$$") && text.endsWith("$$")) {
                    text = text.slice(2, -2).trim();
                } else if (text.startsWith("\\[") && text.endsWith("\\]")) {
                    text = text.slice(2, -2).trim();
                }
                katex.render(text, el, { displayMode: true, throwOnError: false });
                el.dataset.katexRendered = "true";
            }
        });
    }

    if (typeof renderMathInElement === "function") {
        renderMathInElement(document.body, {
            delimiters: [
                {left: "$$", right: "$$", display: true},
                {left: "$", right: "$", display: false},
                {left: "\\(", right: "\\)", display: false},
                {left: "\\[", right: "\\]", display: true},
                {left: "\\begin{equation}", right: "\\end{equation}", display: true},
                {left: "\\begin{align}", right: "\\end{align}", display: true},
                {left: "\\begin{alignat}", right: "\\end{alignat}", display: true},
                {left: "\\begin{gather}", right: "\\end{gather}", display: true},
                {left: "\\begin{CD}", right: "\\end{CD}", display: true}
            ],
            throwOnError: false
        });
    }

    // 3. Highlight.js Code Highlighting
    if (typeof hljs === "object") {
        document.querySelectorAll("pre code").forEach(function(block) {
            if (!block.classList.contains("language-mermaid")) {
                hljs.highlightElement(block);
            }
        });
    }

    // 4. Mermaid Diagrams
    if (typeof mermaid === "object") {
        const isLight = document.body.classList.contains("theme-light") || document.body.classList.contains("theme-sepia");
        mermaid.initialize({ startOnLoad: false, theme: isLight ? "default" : "dark", securityLevel: "loose" });
        const mermaidBlocks = document.querySelectorAll("pre code.language-mermaid");
        if (mermaidBlocks.length > 0) {
            mermaidBlocks.forEach(function(code) {
                const pre = code.parentElement;
                const container = document.createElement("div");
                container.className = "mermaid";
                container.textContent = code.textContent;
                pre.parentNode.replaceChild(container, pre);
            });
            mermaid.run();
        }
    }

    // 5. GFM Callouts / Alerts ([!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION])
    document.querySelectorAll("blockquote").forEach(function(bq) {
        const firstP = bq.querySelector("p");
        if (!firstP) return;
        const text = firstP.innerHTML.trim();
        const match = text.match(/^\[\!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/i);
        if (match) {
            const type = match[1].toUpperCase();
            bq.classList.add("markdown-alert", "markdown-alert-" + type.toLowerCase());
            
            const titles = {
                NOTE: '<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM6.5 7.75A.75.75 0 0 1 7.25 7h1.5a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-1.75a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75ZM8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"/></svg> Note',
                TIP: '<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M8 1.5c-2.363 0-4 1.69-4 3.75 0 .984.424 1.625.984 2.304l.214.253c.223.264.47.556.673.868.309.476.463.968.463 1.575v.25h3.333v-.25c0-.607.155-1.1.464-1.575.203-.312.45-.604.672-.868l.215-.253c.56-.679.984-1.32.984-2.304 0-2.06-1.637-3.75-4-3.75ZM5.5 5.25c0-1.258 1.058-2.25 2.5-2.25s2.5.992 2.5 2.25c0 .542-.234.966-.672 1.5a11.96 11.96 0 0 0-.848 1.1c-.426.657-.647 1.344-.647 2.15H7.667c0-.806-.22-1.493-.647-2.15a11.96 11.96 0 0 0-.848-1.1c-.438-.534-.672-.958-.672-1.5Z"/></svg> Tip',
                IMPORTANT: '<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M0 1.75C0 .784.784 0 1.75 0h12.5C15.216 0 16 .784 16 1.75v12.5A1.75 1.75 0 0 1 14.25 16H1.75A1.75 1.75 0 0 1 0 14.25Zm1.75-.25a.25.25 0 0 0-.25.25v12.5c0 .138.112.25.25.25h12.5a.25.25 0 0 0 .25-.25V1.75a.25.25 0 0 0-.25-.25ZM8 4a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 4Zm0 7a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"/></svg> Important',
                WARNING: '<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M6.457 1.047c.659-1.234 2.427-1.234 3.086 0l6.082 11.378A1.75 1.75 0 0 1 14.082 15H1.918a1.75 1.75 0 0 1-1.543-2.575Zm1.763.707a.25.25 0 0 0-.44 0L1.698 13.132a.25.25 0 0 0 .22.368h12.164a.25.25 0 0 0 .22-.368Zm.53 3.996v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"/></svg> Warning',
                CAUTION: '<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M4.47.22A.749.749 0 0 1 5 0h6c.199 0 .389.079.53.22l4.25 4.25c.141.141.22.331.22.53v6a.749.749 0 0 1-.22.53l-4.25 4.25A.749.749 0 0 1 11 16H5a.749.749 0 0 1-.53-.22L.22 11.53A.749.749 0 0 1 0 11V5c0-.199.079-.389.22-.53Zm.84 1.28L1.5 5.31v5.38l3.81 3.81h5.38l3.81-3.81V5.31L10.69 1.5ZM8 4a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 4Zm0 7a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"/></svg> Caution'
            };
            
            const titleDiv = document.createElement("div");
            titleDiv.className = "markdown-alert-title";
            titleDiv.innerHTML = titles[type] || type;

            firstP.innerHTML = firstP.innerHTML
                .replace(/^\[\!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]<br>?/i, "")
                .replace(/^\[\!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/i, "");
            bq.insertBefore(titleDiv, bq.firstChild);
        }
    });

    // 6. Copy Code Buttons
    const codeBlocks = document.querySelectorAll("pre");
    codeBlocks.forEach(function(pre) {
        if (pre.querySelector(".copy-code-btn")) return;
        const wrapper = document.createElement("div");
        wrapper.className = "code-block-wrapper";
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);

        const btn = document.createElement("button");
        btn.className = "copy-code-btn";
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z"></path><path fill-rule="evenodd" d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z"></path></svg> Copy`;
        
        btn.addEventListener("click", function() {
            const codeText = pre.innerText || pre.textContent;
            navigator.clipboard.writeText(codeText).then(function() {
                btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 16 16" fill="#3fb950"><path fill-rule="evenodd" d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"></path></svg> Copied!`;
                setTimeout(function() {
                    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z"></path><path fill-rule="evenodd" d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z"></path></svg> Copy`;
                }, 2000);
            });
        });
        wrapper.appendChild(btn);
    });

    // 7. Mouse wheel scroll & scroll ratio posting
    window.addEventListener("wheel", function(e) {
        if (e.deltaY) {
            window.scrollBy(0, e.deltaY);
        }
    }, { passive: true });

    let isPosting = false;
    window.addEventListener("scroll", function() {
        if (!isPosting) {
            isPosting = true;
            requestAnimationFrame(function() {
                try {
                    if (window.parent && window.parent !== window) {
                        const doc = document.documentElement;
                        const maxScroll = doc.scrollHeight - window.innerHeight;
                        const ratio = maxScroll > 0 ? window.scrollY / maxScroll : 0;
                        window.parent.postMessage({ type: "READER_SCROLL", ratio: ratio }, "*");
                    }
                } catch(e) {}
                isPosting = false;
            });
        }
    });
});
"##;

impl MarkdownEngine {
    pub fn render(md_text: &str, theme: &str) -> String {
        // Pre-process math blocks that might be indented with spaces inside list items
        let mut processed_lines = Vec::new();
        let mut in_math_block = false;
        for line in md_text.lines() {
            let trimmed = line.trim();

            let is_math_fence = trimmed == "$$" || (trimmed.starts_with("$$") && !trimmed[2..].contains("$$"));
            let is_single_line_math = trimmed.starts_with("$$") && trimmed.ends_with("$$") && trimmed.len() >= 4;

            if is_single_line_math {
                let leading_spaces = line.len() - line.trim_start().len();
                if leading_spaces >= 4 {
                    processed_lines.push(format!("  {}", trimmed));
                    continue;
                }
            } else if is_math_fence {
                in_math_block = !in_math_block;
                let leading_spaces = line.len() - line.trim_start().len();
                if leading_spaces >= 4 {
                    processed_lines.push(format!("  {}", trimmed));
                    continue;
                }
            } else if in_math_block {
                let leading_spaces = line.len() - line.trim_start().len();
                if leading_spaces >= 4 {
                    processed_lines.push(format!("  {}", trimmed));
                    continue;
                }
            }
            processed_lines.push(line.to_string());
        }
        let cleaned_md = processed_lines.join("\n");


        let mut options = Options::empty();
        options.insert(Options::ENABLE_TABLES);
        options.insert(Options::ENABLE_FOOTNOTES);
        options.insert(Options::ENABLE_STRIKETHROUGH);
        options.insert(Options::ENABLE_TASKLISTS);
        options.insert(Options::ENABLE_HEADING_ATTRIBUTES);
        options.insert(Options::ENABLE_MATH);

        let parser = Parser::new_ext(&cleaned_md, options);
        let mut body_html = String::new();
        html::push_html(&mut body_html, parser);

        // Inject unique id="toc-heading-N" to all <h1..6> tags in HTML output
        let re_tag = Regex::new(r"(?i)<(h[1-6])([^>]*)>").unwrap();
        let mut heading_count = 0;
        let body_html_with_ids = re_tag
            .replace_all(&body_html, |caps: &regex::Captures| {
                let tag = &caps[1];
                let attrs = &caps[2];
                let id = format!("toc-heading-{}", heading_count);
                heading_count += 1;
                format!("<{} id=\"{}\"{}>", tag, id, attrs)
            })
            .to_string();

        let theme_class = match theme {
            "light" => "theme-light",
            "sepia" => "theme-sepia",
            _ => "theme-dark",
        };

        let hl_theme_file = match theme {
            "light" | "sepia" => "vendor/highlight/github.min.css",
            _ => "vendor/highlight/github-dark.min.css",
        };

        format!(
            "<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n<base href=\"./\">\n<link rel=\"stylesheet\" href=\"vendor/katex/katex.min.css\">\n<link rel=\"stylesheet\" href=\"{}\" id=\"hljs-theme\">\n<script src=\"vendor/katex/katex.min.js\"></script>\n<script src=\"vendor/katex/auto-render.min.js\"></script>\n<script src=\"vendor/highlight/highlight.min.js\"></script>\n<script src=\"vendor/mermaid/mermaid.min.js\"></script>\n<style>\n{}\n</style>\n</head>\n<body class=\"{}\">\n<div class=\"markdown-body\">\n{}\n</div>\n<div class=\"pdf-footer\"><span class=\"pdf-page-number\"></span></div>\n<script>\n{}\n</script>\n</body>\n</html>",
            hl_theme_file,
            Self::get_theme_css(),
            theme_class,
            body_html_with_ids,
            PREVIEW_SCRIPT
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
                        let display_title = if clean_title.is_empty() {
                            rest.to_string()
                        } else {
                            clean_title
                        };

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
        r##"
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
body { margin: 0; padding: 32px 40px; min-height: 100%; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.6; word-wrap: break-word; }
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

pre code {
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    font-size: 100%;
}

.code-block-wrapper { position: relative; margin-bottom: 16px; }
.copy-code-btn { position: absolute; top: 8px; right: 8px; background-color: #21262d; color: #8b949e; border: 1px solid #30363d; border-radius: 6px; padding: 3px 8px; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 4px; opacity: 0.8; }
.copy-code-btn:hover { opacity: 1; color: #ffffff; }

/* KaTeX Math Styling */
.katex-display {
    margin: 1em 0;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 6px 0;
}
.math-display-block {
    text-align: center;
    margin: 1em 0;
}
body.theme-dark .katex { color: #e6edf3; }
body.theme-light .katex { color: #1f2328; }
body.theme-sepia .katex { color: #5f4b32; }

/* GFM Callouts / Alerts */
blockquote.markdown-alert {
    padding: 0.75em 1em;
    margin-bottom: 16px;
    border-left: 0.25em solid;
    border-radius: 6px;
    opacity: 1;
}
.markdown-alert-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 0.9em;
    margin-bottom: 6px;
}

body.theme-dark blockquote.markdown-alert-note { border-left-color: #2f81f7; background-color: rgba(56, 139, 253, 0.1); color: #e6edf3; }
body.theme-dark .markdown-alert-note .markdown-alert-title { color: #2f81f7; }

body.theme-dark blockquote.markdown-alert-tip { border-left-color: #3fb950; background-color: rgba(46, 160, 67, 0.1); color: #e6edf3; }
body.theme-dark .markdown-alert-tip .markdown-alert-title { color: #3fb950; }

body.theme-dark blockquote.markdown-alert-important { border-left-color: #a371f7; background-color: rgba(163, 113, 247, 0.1); color: #e6edf3; }
body.theme-dark .markdown-alert-important .markdown-alert-title { color: #a371f7; }

body.theme-dark blockquote.markdown-alert-warning { border-left-color: #d29922; background-color: rgba(187, 128, 9, 0.1); color: #e6edf3; }
body.theme-dark .markdown-alert-warning .markdown-alert-title { color: #d29922; }

body.theme-dark blockquote.markdown-alert-caution { border-left-color: #f85149; background-color: rgba(248, 81, 73, 0.1); color: #e6edf3; }
body.theme-dark .markdown-alert-caution .markdown-alert-title { color: #f85149; }

body.theme-light blockquote.markdown-alert-note { border-left-color: #0969da; background-color: #ddf4ff; color: #1f2328; }
body.theme-light .markdown-alert-note .markdown-alert-title { color: #0969da; }

body.theme-light blockquote.markdown-alert-tip { border-left-color: #1a7f37; background-color: #dafbe1; color: #1f2328; }
body.theme-light .markdown-alert-tip .markdown-alert-title { color: #1a7f37; }

body.theme-light blockquote.markdown-alert-important { border-left-color: #8250df; background-color: #fbefff; color: #1f2328; }
body.theme-light .markdown-alert-important .markdown-alert-title { color: #8250df; }

body.theme-light blockquote.markdown-alert-warning { border-left-color: #9a6700; background-color: #fff8c5; color: #1f2328; }
body.theme-light .markdown-alert-warning .markdown-alert-title { color: #9a6700; }

body.theme-light blockquote.markdown-alert-caution { border-left-color: #cf222e; background-color: #ffebe9; color: #1f2328; }
body.theme-light .markdown-alert-caution .markdown-alert-title { color: #cf222e; }

body.theme-sepia blockquote.markdown-alert-note { border-left-color: #924500; background-color: rgba(146, 69, 0, 0.08); color: #5f4b32; }
body.theme-sepia .markdown-alert-note .markdown-alert-title { color: #924500; }

/* Mermaid Diagrams */
.mermaid {
    display: flex;
    justify-content: center;
    margin: 20px 0;
}

/* Styled Keyboard KBD caps */
kbd {
    display: inline-block;
    padding: 3px 6px;
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    font-size: 11px;
    line-height: 10px;
    vertical-align: middle;
    border-radius: 6px;
}
body.theme-dark kbd { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-bottom-color: #484f58; box-shadow: inset 0 -1px 0 #484f58; }
body.theme-light kbd { background-color: #f6f8fa; color: #24292f; border: 1px solid #d0d7de; border-bottom-color: #afb8c1; box-shadow: inset 0 -1px 0 #afb8c1; }
body.theme-sepia kbd { background-color: #f2e3c6; color: #5f4b32; border: 1px solid #e0d0b0; border-bottom-color: #cbb892; }

/* Checklists */
ul.contains-task-list { list-style: none; padding-left: 0; }
li.task-list-item { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
li.task-list-item input[type="checkbox"] {
    appearance: none;
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 4px;
    outline: none;
    cursor: pointer;
    vertical-align: middle;
    position: relative;
    top: 2px;
}
body.theme-dark li.task-list-item input[type="checkbox"] { border: 1.5px solid #484f58; background-color: #161b22; }
body.theme-dark li.task-list-item input[type="checkbox"]:checked { background-color: #238636; border-color: #238636; }

body.theme-light li.task-list-item input[type="checkbox"] { border: 1.5px solid #d0d7de; background-color: #ffffff; }
body.theme-light li.task-list-item input[type="checkbox"]:checked { background-color: #1f883d; border-color: #1f883d; }

body.theme-sepia li.task-list-item input[type="checkbox"] { border: 1.5px solid #e0d0b0; background-color: #fbf0d9; }
body.theme-sepia li.task-list-item input[type="checkbox"]:checked { background-color: #924500; border-color: #924500; }

li.task-list-item input[type="checkbox"]:checked::after {
    content: "✓";
    position: absolute;
    color: white;
    font-size: 12px;
    font-weight: bold;
    left: 2px;
    top: -2px;
}

/* Tables */
table {
    border-spacing: 0;
    border-collapse: separate;
    width: 100%;
    margin-bottom: 16px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid;
}
body.theme-dark table { border-color: var(--border-dark); }
body.theme-light table { border-color: var(--border-light); }
body.theme-sepia table { border-color: var(--border-sepia); }

body.theme-dark table th { background-color: #161b22; color: #f0f6fc; font-weight: 600; }
body.theme-light table th { background-color: #f6f8fa; color: #1f2328; font-weight: 600; }
body.theme-sepia table th { background-color: #f2e3c6; color: #5f4b32; font-weight: 600; }

table th, table td {
    padding: 8px 14px;
    border-right: 1px solid;
    border-bottom: 1px solid;
    opacity: 0.9;
}
body.theme-dark table th, body.theme-dark table td { border-color: var(--border-dark); }
body.theme-light table th, body.theme-light table td { border-color: var(--border-light); }
body.theme-sepia table th, body.theme-sepia table td { border-color: var(--border-sepia); }

table th:last-child, table td:last-child {
    border-right: none;
}

table tr:last-child td {
    border-bottom: none;
}

body.theme-dark table tr:nth-child(even) { background-color: rgba(110, 118, 129, 0.05); }
body.theme-light table tr:nth-child(even) { background-color: rgba(234, 238, 242, 0.5); }
body.theme-sepia table tr:nth-child(even) { background-color: rgba(146, 69, 0, 0.04); }

/* Blockquotes & HR */
blockquote { padding: 0 1em; border-left: 0.25em solid currentColor; opacity: 0.85; margin: 0 0 16px 0; }
ul, ol { padding-left: 2em; margin-bottom: 16px; }
img { max-width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
hr {
    height: 0.25em;
    padding: 0;
    margin: 24px 0;
    background-color: currentColor;
    border: 0;
    opacity: 0.2;
    border-radius: 2px;
}

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
"##
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_render_math() {
        let md = r#"
* **Chỉ số Kỳ vọng (Expectancy)**:
      $$\text{Expectancy} = (\text{Win Rate} \times \text{Average Win R}) - (\text{Loss Rate} \times \text{Average Loss R})$$
* **Công thức Chuẩn hoá (Inline Math)**: Phương trình $E = mc^2$ và căn bậc hai $\sqrt{x^2 + y^2} = r$.
"#;
        let html = MarkdownEngine::render(md, "dark");
        assert!(html.contains("math"));
        assert!(html.contains("katex.render"));
    }

    #[test]
    fn test_render_table() {
        let md = r#"
| Feature | Reader View |
| :--- | :---: |
| Math LaTeX | ✅ |
"#;
        let html = MarkdownEngine::render(md, "dark");
        assert!(html.contains("<table"));
        assert!(html.contains("border-collapse: separate;"));
    }
}
