import http.server
import socketserver
import os
import sys

# Get port from environment or argument or default
PORT = int(os.environ.get("PORT", 8000))
DIRECTORY = os.path.abspath(os.environ.get("DIRECTORY", "."))

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Strip query parameters for file existence check
        parts = self.path.split('?', 1)
        path_only = parts[0]
        query = '?' + parts[1] if len(parts) > 1 else ''
        
        # SECURITY FIX: Sanitize the path to prevent path traversal (CWE-22)
        # 1. Normalize the path (resolves .. and //)
        normalized_path = os.path.normpath(path_only)
        
        # 2. Prevent accessing files outside of the DIRECTORY
        # normpath on an absolute-looking path like '/../../etc/passwd' returns '../../etc/passwd'
        if normalized_path.startswith('..') or os.path.isabs(normalized_path):
            # If it's absolute or tries to go up, we treat it as relative to root
            # or just reject it. SimpleHTTPRequestHandler handles this usually, 
            # but since we are doing manual path construction below, we must be careful.
            rel_path = normalized_path.lstrip(os.path.sep).lstrip('/')
        else:
            rel_path = normalized_path.lstrip('/')

        if not rel_path or rel_path == '.':
            rel_path = "index.html"
            
        # Construct the actual filesystem path securely
        actual_fs_path = os.path.abspath(os.path.join(DIRECTORY, rel_path))
        
        # 3. Final safety check: Ensure the resulting path is still inside DIRECTORY
        if not actual_fs_path.startswith(DIRECTORY):
            self.send_error(403, "Forbidden: Access denied")
            return

        # If file doesn't exist and has no extension, try adding .html
        if not os.path.exists(actual_fs_path) and not os.path.splitext(rel_path)[1]:
            html_path = actual_fs_path + ".html"
            if os.path.exists(html_path):
                # Map internally to the .html file
                # SimpleHTTPRequestHandler will handle the actual serving securely 
                # based on this modified self.path
                self.path = normalized_path + ".html" + query
                
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
