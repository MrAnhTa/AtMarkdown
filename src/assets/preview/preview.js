
document.addEventListener("DOMContentLoaded", async function() {
    window.atMarkdownReady = false;
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
        mermaid.initialize({ startOnLoad: false, theme: isLight ? "default" : "dark", securityLevel: "strict" });
        const mermaidBlocks = document.querySelectorAll("pre code.language-mermaid");
        if (mermaidBlocks.length > 0) {
            mermaidBlocks.forEach(function(code) {
                const pre = code.parentElement;
                const container = document.createElement("div");
                container.className = "mermaid";
                container.textContent = code.textContent;
                pre.parentNode.replaceChild(container, pre);
            });
            try { await mermaid.run(); }
            catch (error) { console.warn("Mermaid:", error); }
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

    // 7. Post the native browser scroll position to Split View.
    // Wheel/touchpad input is intentionally not handled here: WebView2 already
    // provides native scrolling, and manually calling scrollBy would apply every
    // gesture twice.
    let isPosting = false;
    window.addEventListener("scroll", function() {
        if (window.__atMarkdownProgrammaticScroll) return;
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
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map(img => img.complete ? Promise.resolve() :
        new Promise(resolve => { img.onload = resolve; img.onerror = resolve; })));
    window.atMarkdownReady = true;
});
