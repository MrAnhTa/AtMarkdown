// Main App IPC & Event Handler Script
document.addEventListener("DOMContentLoaded", async () => {
    // DOM Elements
    const editor = document.getElementById("code-editor");
    const previewFrame = document.getElementById("preview-frame");
    const modeSelect = document.getElementById("mode-select");
    const themeSelect = document.getElementById("theme-select");
    const sidebar = document.getElementById("sidebar");
    const editorContainer = document.getElementById("editor-container");
    const viewerContainer = document.getElementById("viewer-container");
    const formattingBar = document.getElementById("formatting-bar");
    const filePathIndicator = document.getElementById("file-path-indicator");

    const statLines = document.getElementById("stat-lines");
    const statWords = document.getElementById("stat-words");
    const statChars = document.getElementById("stat-chars");
    const statRead = document.getElementById("stat-read");
    const statMode = document.getElementById("stat-mode");

    const tocTree = document.getElementById("toc-tree");
    const recentList = document.getElementById("recent-list");

    // Buttons
    const btnNew = document.getElementById("btn-new");
    const btnOpen = document.getElementById("btn-open");
    const btnSave = document.getElementById("btn-save");
    const btnSaveAs = document.getElementById("btn-save-as");
    const btnExportHtml = document.getElementById("btn-export-html");
    const btnExportPdf = document.getElementById("btn-export-pdf");
    const btnToggleSidebar = document.getElementById("btn-toggle-sidebar");

    // Application State
    let currentFilePath = null;
    let isModified = false;
    let renderTimer = null;

    // Helper: Tauri Invoke wrapper
    async function invokeCmd(cmd, args = {}) {
        if (window.__TAURI__ && window.__TAURI__.core) {
            return await window.__TAURI__.core.invoke(cmd, args);
        } else {
            console.warn("Tauri IPC unavailable, command:", cmd);
            return null;
        }
    }

    let isSyncScrolling = false;

    // Synchronized Scroll: Editor to Reader
    function syncEditorToReader() {
        if (modeSelect.value !== "split" || isSyncScrolling) return;
        isSyncScrolling = true;

        const maxEditorScroll = editor.scrollHeight - editor.clientHeight;
        if (maxEditorScroll > 0) {
            const ratio = editor.scrollTop / maxEditorScroll;
            const win = previewFrame.contentWindow;
            if (win && win.document && win.document.documentElement) {
                const doc = win.document.documentElement;
                const maxReaderScroll = doc.scrollHeight - win.innerHeight;
                if (maxReaderScroll > 0) {
                    win.scrollTo({ top: ratio * maxReaderScroll, behavior: "auto" });
                }
            }
        }

        setTimeout(() => { isSyncScrolling = false; }, 50);
    }

    window.onEditorScrollSync = syncEditorToReader;

    // Synchronized Scroll: Reader to Editor via postMessage from iframe
    window.addEventListener("message", (e) => {
        if (e.data && e.data.type === "READER_SCROLL" && modeSelect.value === "split") {
            if (isSyncScrolling) return;
            isSyncScrolling = true;

            const ratio = e.data.ratio;
            const maxEditorScroll = editor.scrollHeight - editor.clientHeight;
            if (maxEditorScroll > 0) {
                editor.scrollTop = ratio * maxEditorScroll;
                const lineNumbers = document.getElementById("line-numbers");
                if (lineNumbers) lineNumbers.scrollTop = editor.scrollTop;
            }

            setTimeout(() => { isSyncScrolling = false; }, 50);
        }
    });

    // Forward mouse wheel events over viewer container to preview iframe
    viewerContainer.addEventListener("wheel", (e) => {
        const win = previewFrame.contentWindow;
        if (win && e.deltaY) {
            win.scrollBy(0, e.deltaY);
        }
    }, { passive: true });

    // Live Render Function
    async function performRender() {
        const text = editor.value;
        const theme = themeSelect.value;
        const result = await invokeCmd("render_markdown", { mdText: text, theme: theme });

        if (result) {
            // Save scroll ratio before update
            let scrollRatio = 0;
            const win = previewFrame.contentWindow;
            if (win && win.document && win.document.documentElement) {
                const doc = win.document.documentElement;
                const maxScroll = doc.scrollHeight - win.innerHeight;
                if (maxScroll > 0) scrollRatio = win.scrollY / maxScroll;
            }

            // Update preview frame HTML
            const doc = previewFrame.contentDocument || previewFrame.contentWindow.document;
            doc.open();
            doc.write(result.html);
            doc.close();

            // Restore scroll position after render
            if (scrollRatio > 0 && previewFrame.contentWindow) {
                setTimeout(() => {
                    const win = previewFrame.contentWindow;
                    if (win && win.document && win.document.documentElement) {
                        const maxScroll = win.document.documentElement.scrollHeight - win.innerHeight;
                        win.scrollTo(0, scrollRatio * maxScroll);
                    }
                }, 50);
            }

            // Update Outline TOC
            updateTocTree(result.headings);

            // Update Stats Bar
            statLines.textContent = `Lines: ${result.stats.lines}`;
            statWords.textContent = `Words: ${result.stats.words}`;
            statChars.textContent = `Chars: ${result.stats.chars}`;
            statRead.textContent = `Read: ~${result.stats.reading_time} min`;
        }
    }

    function triggerRender() {
        clearTimeout(renderTimer);
        renderTimer = setTimeout(performRender, 150);
    }

    // Outline Navigation Seek (Reader & Editor Scroll)
    function updateTocTree(headings) {
        tocTree.innerHTML = "";
        if (!headings || headings.length === 0) {
            tocTree.innerHTML = '<li class="empty-msg">(No headings found)</li>';
            return;
        }

        headings.forEach(h => {
            const li = document.createElement("li");
            const indent = "&nbsp;&nbsp;".repeat(Math.max(0, h.level - 1));
            li.innerHTML = `${indent}• ${escapeHtml(h.title)}`;

            li.addEventListener("click", () => {
                // 1. Scroll in Reader View / Preview Iframe
                const doc = previewFrame.contentDocument || previewFrame.contentWindow.document;
                if (doc) {
                    const targetEl = doc.getElementById(h.id);
                    if (targetEl) {
                        targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
                    } else {
                        // Fallback by heading text
                        const allHeadings = Array.from(doc.querySelectorAll("h1, h2, h3, h4, h5, h6"));
                        const found = allHeadings.find(el => el.textContent.trim().includes(h.title));
                        if (found) found.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                }

                // 2. Scroll in Editor View
                if (editor.value && h.line_number) {
                    const lines = editor.value.split("\n");
                    const totalLines = lines.length || 1;
                    const targetIdx = Math.min(lines.length - 1, Math.max(0, h.line_number - 1));

                    // Calculate character offset for selection
                    let charOffset = 0;
                    for (let i = 0; i < targetIdx; i++) {
                        charOffset += lines[i].length + 1;
                    }

                    // Scroll editor to exact line ratio
                    const lineRatio = targetIdx / totalLines;
                    editor.scrollTop = Math.max(0, lineRatio * editor.scrollHeight - 20);

                    // Sync line numbers gutter
                    const lineNumbers = document.getElementById("line-numbers");
                    if (lineNumbers) {
                        lineNumbers.scrollTop = editor.scrollTop;
                    }

                    // Highlight line in editor
                    const lineLen = lines[targetIdx] ? lines[targetIdx].length : 0;
                    editor.setSelectionRange(charOffset, charOffset + lineLen);
                    editor.focus();
                }
            });
            tocTree.appendChild(li);
        });
    }

    function updateRecentList(files) {
        recentList.innerHTML = "";
        if (!files || files.length === 0) {
            recentList.innerHTML = '<li class="empty-msg">(No recent files)</li>';
            return;
        }

        files.forEach(path => {
            const filename = path.split(/[/\\]/).pop();
            const li = document.createElement("li");
            li.innerHTML = `📄 <strong>${escapeHtml(filename)}</strong><br><small style="opacity:0.7">${escapeHtml(path)}</small>`;
            li.title = path;
            li.addEventListener("click", () => openFileByPath(path));
            recentList.appendChild(li);
        });
    }

    function escapeHtml(str) {
        return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[m]);
    }

    function updateWindowTitle() {
        const name = currentFilePath ? currentFilePath.split(/[/\\]/).pop() : "Untitled.md";
        const dirty = isModified ? " *" : "";
        filePathIndicator.textContent = `${name}${dirty}`;
        document.title = `${name}${dirty} - AtMarkdown Reader & Editor`;
    }

    // File Operations via Rust Native Dialogs
    async function openFile() {
        try {
            const res = await invokeCmd("dialog_open_file");
            if (res) {
                currentFilePath = res[0];
                editor.value = res[1];
                isModified = false;
                editor.dispatchEvent(new Event("input"));
                updateWindowTitle();
                triggerRender();
                loadRecentFiles();
            }
        } catch (e) {
            alert("Error opening file: " + e);
        }
    }

    async function openFileByPath(filePath) {
        if (!filePath) return;
        try {
            const res = await invokeCmd("open_file_content", { path: filePath });
            if (res) {
                currentFilePath = res[0];
                editor.value = res[1];
                isModified = false;
                editor.dispatchEvent(new Event("input"));
                updateWindowTitle();
                triggerRender();
                loadRecentFiles();
            }
        } catch (e) {
            alert("Error opening file: " + e);
        }
    }

    async function saveFile() {
        if (!currentFilePath) {
            return await saveFileAs();
        }

        try {
            await invokeCmd("save_file_content", { path: currentFilePath, content: editor.value });
            isModified = false;
            updateWindowTitle();
            return true;
        } catch (e) {
            alert("Error saving file: " + e);
            return false;
        }
    }

    async function saveFileAs() {
        const defaultName = currentFilePath ? currentFilePath.split(/[/\\]/).pop() : "untitled.md";
        const chosen = await invokeCmd("dialog_save_file", { defaultName: defaultName });
        if (chosen) {
            currentFilePath = chosen;
            return await saveFile();
        }
        return false;
    }

    function newFile() {
        currentFilePath = null;
        editor.value = "";
        isModified = false;
        editor.dispatchEvent(new Event("input"));
        updateWindowTitle();
        triggerRender();
    }

    async function loadRecentFiles() {
        const settings = await invokeCmd("get_settings");
        if (settings) {
            updateRecentList(settings.recent_files);
        }
    }

    // View Mode & Theme Switchers
    function applyViewMode(mode) {
        modeSelect.value = mode;
        if (mode === "reader") {
            editorContainer.style.display = "none";
            viewerContainer.style.display = "block";
            formattingBar.style.display = "none";
            statMode.textContent = "Mode: Reader View";
        } else if (mode === "editor") {
            editorContainer.style.display = "flex";
            viewerContainer.style.display = "none";
            formattingBar.style.display = "flex";
            statMode.textContent = "Mode: Editor View";
        } else { // split
            editorContainer.style.display = "flex";
            viewerContainer.style.display = "block";
            formattingBar.style.display = "flex";
            statMode.textContent = "Mode: Split Live Preview";
        }
    }

    function applyTheme(theme) {
        themeSelect.value = theme;
        document.body.className = `theme-${theme}`;
        triggerRender();
    }

    // Event Listeners
    editor.addEventListener("input", () => {
        isModified = true;
        updateWindowTitle();
        triggerRender();
    });

    modeSelect.addEventListener("change", (e) => applyViewMode(e.target.value));
    themeSelect.addEventListener("change", (e) => applyTheme(e.target.value));

    btnNew.addEventListener("click", newFile);
    btnOpen.addEventListener("click", openFile);
    btnSave.addEventListener("click", saveFile);
    btnSaveAs.addEventListener("click", saveFileAs);

    btnExportHtml.addEventListener("click", async () => {
        const path = await invokeCmd("dialog_export_html_path");
        if (path) {
            const html = await invokeCmd("render_markdown", { mdText: editor.value, theme: themeSelect.value });
            if (html) {
                await invokeCmd("export_html", { htmlContent: html.html, path: path });
                alert("Exported to HTML successfully!");
            }
        }
    });

    btnExportPdf.addEventListener("click", () => {
        const frameWindow = previewFrame.contentWindow;
        if (frameWindow) {
            frameWindow.focus();
            frameWindow.print();
        }
    });

    btnToggleSidebar.addEventListener("click", () => {
        sidebar.style.display = sidebar.style.display === "none" ? "flex" : "none";
    });

    // Sidebar Tabs
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
            const targetPane = document.getElementById(`pane-${btn.dataset.tab}`);
            if (targetPane) targetPane.classList.add("active");
        });
    });

    // Splitter Dragging Logic (Sidebar & Editor/Viewer Panels)
    function setupSplitter(handleId, getLeftEl, resizeCallback) {
        const handle = document.getElementById(handleId);
        if (!handle) return;

        let isDragging = false;
        let startX = 0;
        let startLeftWidth = 0;

        handle.addEventListener("mousedown", (e) => {
            isDragging = true;
            startX = e.clientX;
            const leftEl = getLeftEl();
            startLeftWidth = leftEl.getBoundingClientRect().width;

            handle.classList.add("dragging");
            document.body.style.cursor = "col-resize";
            document.body.style.userSelect = "none";
            previewFrame.style.pointerEvents = "none"; // Disable iframe mouse capture during drag
            e.preventDefault();
        });

        document.addEventListener("mousemove", (e) => {
            if (!isDragging) return;
            const deltaX = e.clientX - startX;
            const newWidth = startLeftWidth + deltaX;
            resizeCallback(newWidth);
        });

        const stopDrag = () => {
            if (isDragging) {
                isDragging = false;
                handle.classList.remove("dragging");
                document.body.style.cursor = "default";
                document.body.style.userSelect = "";
                previewFrame.style.pointerEvents = "auto";
            }
        };

        document.addEventListener("mouseup", stopDrag);
        document.addEventListener("mouseleave", stopDrag);
        window.addEventListener("blur", stopDrag);
    }

    // 1. Sidebar Splitter
    setupSplitter("handle-sidebar", () => sidebar, (newWidth) => {
        const clamped = Math.max(120, Math.min(500, newWidth));
        sidebar.style.width = `${clamped}px`;
    });

    // 2. Editor vs Viewer Splitter
    setupSplitter("handle-editor", () => editorContainer, (newWidth) => {
        const containerWidth = document.getElementById("main-splitter").getBoundingClientRect().width;
        const sidebarWidth = sidebar.style.display !== "none" ? sidebar.getBoundingClientRect().width : 0;
        const availableWidth = containerWidth - sidebarWidth - 12;

        const clamped = Math.max(150, Math.min(availableWidth - 150, newWidth));
        editorContainer.style.flex = "none";
        editorContainer.style.width = `${clamped}px`;
        viewerContainer.style.flex = "1";
    });

    // Keyboard Shortcuts
    document.addEventListener("keydown", (e) => {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === "o" || e.key === "O") {
                e.preventDefault();
                openFile();
            } else if (e.key === "s" || e.key === "S") {
                e.preventDefault();
                if (e.shiftKey) {
                    saveFileAs();
                } else {
                    saveFile();
                }
            } else if (e.key === "n" || e.key === "N") {
                e.preventDefault();
                newFile();
            } else if (e.key === "f" || e.key === "F") {
                e.preventDefault();
                if (window.toggleSearchPanel) window.toggleSearchPanel();
            } else if (e.key === "b" || e.key === "B") {
                e.preventDefault();
                sidebar.style.display = sidebar.style.display === "none" ? "flex" : "none";
            }
        }
    });

    // Initial Loading
    const welcomeDoc = await invokeCmd("get_welcome_doc");
    if (welcomeDoc) {
        editor.value = welcomeDoc;
        editor.dispatchEvent(new Event("input"));
    }

    loadRecentFiles();
    applyViewMode("split");
    applyTheme("dark");
});
