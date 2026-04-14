import http.server
import socketserver
import os
import sys

# Get port from environment or argument or default
PORT = int(os.environ.get("PORT", 8000))
DIRECTORY = os.environ.get("DIRECTORY", ".")

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Strip query parameters for file existence check
        parts = self.path.split('?', 1)
        path_only = parts[0]
        query = '?' + parts[1] if len(parts) > 1 else ''
        
        # Ensure we are checking within the correct DIRECTORY
        rel_path = path_only.lstrip('/')
        if not rel_path:
            rel_path = "index.html"
            
        actual_fs_path = os.path.join(DIRECTORY, rel_path)
        
        # If file doesn't exist and has no extension, try adding .html
        if not os.path.exists(actual_fs_path) and not os.path.splitext(path_only)[1]:
            html_path = actual_fs_path + ".html"
            if os.path.exists(html_path):
                # Map internally to the .html file
                self.path = path_only + ".html" + query
                
        return super().do_GET()

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
            pass
