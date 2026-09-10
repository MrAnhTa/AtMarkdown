# Bundled presentation libraries

Preview JavaScript and CSS were ported from AtMarkdown main at d75bd43.

- KaTeX 0.16.11: MIT; see `vendor/katex/LICENSE`. The complete woff2 font set comes from the official npm package `katex@0.16.11`. Unused woff/ttf CSS fallbacks were removed.
- Highlight.js 11.9.0: BSD-3-Clause; see `vendor/highlight/LICENSE`.
- Mermaid: vendored bundle from main; MIT; see `vendor/mermaid/LICENSE`.

All libraries and fonts are loaded locally. Standalone HTML embeds these assets.
