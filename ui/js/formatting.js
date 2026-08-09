// Quick Formatting Toolbar Click Handlers
document.addEventListener("DOMContentLoaded", () => {
    const formattingBar = document.getElementById("formatting-bar");

    if (formattingBar) {
        formattingBar.addEventListener("click", (e) => {
            const btn = e.target.closest("button");
            if (btn) {
                const prefix = btn.getAttribute("data-prefix") || "";
                const suffix = btn.getAttribute("data-suffix") || "";
                if (window.insertFormatting) {
                    window.insertFormatting(prefix, suffix);
                }
            }
        });
    }
});
