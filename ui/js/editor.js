// Editor Line Numbers & Find Search Logic
document.addEventListener("DOMContentLoaded", () => {
    const editor = document.getElementById("code-editor");
    const lineNumbers = document.getElementById("line-numbers");
    const searchPanel = document.getElementById("search-panel");
    const searchInput = document.getElementById("search-input");
    const btnSearchPrev = document.getElementById("search-prev");
    const btnSearchNext = document.getElementById("search-next");
    const btnSearchClose = document.getElementById("search-close");

    // Update Line Numbers on input & scroll
    function updateLineNumbers() {
        const text = editor.value;
        const lineCount = text.split("\n").length;
        let numStr = "";
        for (let i = 1; i <= lineCount; i++) {
            numStr += i + "\n";
        }
        lineNumbers.textContent = numStr;
    }

    let isSyncingGutter = false;
    function syncScroll() {
        if (!isSyncingGutter) {
            isSyncingGutter = true;
            requestAnimationFrame(() => {
                lineNumbers.scrollTop = editor.scrollTop;
                isSyncingGutter = false;
            });
        }
    }

    // Forward mouse wheel events from line numbers gutter to editor textarea
    if (lineNumbers) {
        lineNumbers.addEventListener("wheel", (e) => {
            if (editor) {
                editor.scrollTop += e.deltaY;
                syncScroll();
                if (window.onEditorScrollSync) {
                    window.onEditorScrollSync();
                }
            }
            e.preventDefault();
        }, { passive: false });
    }

    editor.addEventListener("input", () => {
        updateLineNumbers();
        syncScroll();
    });
    editor.addEventListener("scroll", () => {
        syncScroll();
        if (window.onEditorScrollSync) {
            window.onEditorScrollSync();
        }
    });
    updateLineNumbers();

    // Tab key support in Editor
    editor.addEventListener("keydown", (e) => {
        if (e.key === "Tab") {
            e.preventDefault();
            const start = editor.selectionStart;
            const end = editor.selectionEnd;
            editor.value = editor.value.substring(0, start) + "    " + editor.value.substring(end);
            editor.selectionStart = editor.selectionEnd = start + 4;
            editor.dispatchEvent(new Event("input"));
        }
    });

    // Formatting insertion helper
    window.insertFormatting = function(prefix, suffix) {
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        const selected = editor.value.substring(start, end);
        const replacement = prefix + selected + suffix;

        editor.value = editor.value.substring(0, start) + replacement + editor.value.substring(end);
        
        if (selected.length > 0) {
            editor.selectionStart = start;
            editor.selectionEnd = start + replacement.length;
        } else if (suffix.length > 0) {
            editor.selectionStart = editor.selectionEnd = start + prefix.length;
        } else {
            editor.selectionStart = editor.selectionEnd = start + replacement.length;
        }
        
        editor.focus();
        editor.dispatchEvent(new Event("input"));
    };

    // Find / Search Panel (Ctrl+F)
    window.toggleSearchPanel = function(show) {
        if (show === undefined) {
            show = searchPanel.style.display === "none";
        }
        searchPanel.style.display = show ? "flex" : "none";
        if (show) {
            searchInput.focus();
            searchInput.select();
        }
    };

    let lastSearchIndex = -1;

    function findText(forward = true) {
        const query = searchInput.value;
        if (!query) return;

        const content = editor.value;
        let startIndex = forward ? editor.selectionEnd : editor.selectionStart - 1;

        if (startIndex < 0) startIndex = content.length;

        let index = forward
            ? content.toLowerCase().indexOf(query.toLowerCase(), startIndex)
            : content.toLowerCase().lastIndexOf(query.toLowerCase(), startIndex);

        // Wrap around
        if (index === -1) {
            index = forward
                ? content.toLowerCase().indexOf(query.toLowerCase(), 0)
                : content.toLowerCase().lastIndexOf(query.toLowerCase(), content.length);
        }

        if (index !== -1) {
            editor.selectionStart = index;
            editor.selectionEnd = index + query.length;
            editor.focus();
            lastSearchIndex = index;
        }
    }

    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            findText(!e.shiftKey);
        } else if (e.key === "Escape") {
            toggleSearchPanel(false);
        }
    });

    btnSearchNext.addEventListener("click", () => findText(true));
    btnSearchPrev.addEventListener("click", () => findText(false));
    btnSearchClose.addEventListener("click", () => toggleSearchPanel(false));
});
