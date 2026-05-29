#!/usr/bin/env python3
"""Serve the built _site with an explicit charset=utf-8 on text responses.

`quarto preview` serves raw .md / .txt files without a charset, so browsers
mis-decode UTF-8 (e.g. "André" shows as "AndrÃ©"). This is purely a display
quirk of the dev server — the files on disk are valid UTF-8. Use this server
to confirm the manuscripts and llms.txt render correctly in a browser.

    python scripts/preview-utf8.py [port]   # default 4322

Run a full `quarto render` first so _site is up to date. This server does NOT
auto-reload; use `quarto preview` for the live HTML pages.
"""
import functools
import http.server
import mimetypes
import socketserver
import sys
from pathlib import Path

mimetypes.add_type("text/markdown", ".md")


class Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        ctype = super().guess_type(path)
        if isinstance(ctype, tuple):  # older Python returns (type, encoding)
            ctype = ctype[0] or "application/octet-stream"
        if ctype.startswith("text/") and "charset" not in ctype:
            ctype += "; charset=utf-8"
        return ctype


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4322
    root = Path(__file__).resolve().parent.parent / "_site"
    if not root.is_dir():
        print(f"_site not found at {root}. Run `quarto render` first.", file=sys.stderr)
        return 1
    handler = functools.partial(Handler, directory=str(root))
    with socketserver.ThreadingTCPServer(("localhost", port), handler) as httpd:
        print(f"Serving {root} at http://localhost:{port}/ (charset=utf-8)")
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
