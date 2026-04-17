# ABOUTME: Local development server with support for extensionless URLs.
# ABOUTME: Handles routing for static assets and HTML files without .html suffixes.

import http.server
import socketserver
import os
import sys
import urllib.parse

# Get port from environment or argument or default
PORT = int(os.environ.get("PORT", 8000))
# Default to current working directory
DIRECTORY = os.path.abspath(os.environ.get("DIRECTORY", "."))

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Python 3.7+ supports the directory parameter
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def translate_path(self, path):
        # 1. Parse the URL and get the path component
        parsed = urllib.parse.urlparse(path)
        path_only = parsed.path
        
        # 2. Let the superclass do its standard translation
        # This handles directory mapping and security (preventing path traversal)
        translated = super().translate_path(path_only)
        
        # 3. If the path doesn't exist and has no extension, try adding .html
        if not os.path.exists(translated):
            # Check if it's a "clean URL" for an .html file
            # e.g. /quiz -> quiz.html, /2026-04-12 -> 2026-04-12.html
            base, ext = os.path.splitext(translated)
            if not ext:
                html_path = translated + ".html"
                if os.path.exists(html_path):
                    return html_path
                    
        return translated

if __name__ == "__main__":
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory '{DIRECTORY}' does not exist.")
        sys.exit(1)
        
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CleanURLHandler) as httpd:
        print(f"Serving '{DIRECTORY}' at http://localhost:{PORT}")
        print("Supporting clean URLs (e.g. /2026-04-12 -> /2026-04-12.html)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            pass
