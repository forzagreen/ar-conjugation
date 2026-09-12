#!/usr/bin/env python3
"""Serve the site locally the way GitHub Pages lays it out: site/ at /, data/ at /data/.

    python3 scripts/serve.py [port]
"""
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        if path.startswith("/data/"):
            return os.path.join(ROOT, path.lstrip("/"))
        return os.path.join(ROOT, "site", path.lstrip("/") or "index.html")


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
print("http://localhost:%d/" % port)
http.server.ThreadingHTTPServer(("", port), Handler).serve_forever()
