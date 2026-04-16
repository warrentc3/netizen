#!/usr/bin/env python3
"""Serve the Swagger UI locally and open a browser. Downloads Swagger UI assets on first run if missing.
Auto-shuts down when the browser tab closes (no requests for 10 seconds after initial load)."""
import argparse
import http.server
import os
import sys
import threading
import time
import urllib.request
import webbrowser

parser = argparse.ArgumentParser(description="Serve Swagger UI locally.")
parser.add_argument("-p", "--port", type=int, default=8080, help="Port to serve on (default: 8080)")
parser.add_argument("-k", "--keep-alive", action="store_true", help="Disable auto-shutdown on inactivity")
args = parser.parse_args()

PORT = args.port
DIR = os.path.dirname(os.path.abspath(__file__))
IDLE_TIMEOUT = 120

ASSETS = {
    "swagger-ui.css": "https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    "swagger-ui-bundle.js": "https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
    "swagger-ui-standalone-preset.js": "https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js",
}

last_request = time.time()
initial_load = False


def ensure_assets():
    for filename, url in ASSETS.items():
        path = os.path.join(DIR, filename)
        if not os.path.exists(path):
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, path)
            print(f"  Saved {filename} ({os.path.getsize(path):,} bytes)")


API_BASE = "https://api.tvmaze.com"


class TrackedHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_request, initial_load
        last_request = time.time()
        if self.path.startswith("/api/"):
            return self._proxy()
        if self.path == "/" or self.path.startswith("/index.html"):
            initial_load = True
        return super().do_GET()

    def do_POST(self):
        global last_request
        last_request = time.time()
        if self.path.startswith("/api/"):
            return self._proxy()
        self.send_error(405)

    def do_PUT(self):
        global last_request
        last_request = time.time()
        if self.path.startswith("/api/"):
            return self._proxy()
        self.send_error(405)

    def do_DELETE(self):
        global last_request
        last_request = time.time()
        if self.path.startswith("/api/"):
            return self._proxy()
        self.send_error(405)

    def _proxy(self):
        sd_path = self.path[4:]  # strip /api
        url = API_BASE + sd_path

        body = None
        content_length = self.headers.get("Content-Length")
        if content_length:
            body = self.rfile.read(int(content_length))

        req = urllib.request.Request(url, data=body, method=self.command)
        for key, val in self.headers.items():
            if key.lower() in ("host", "connection", "accept-encoding"):
                continue
            req.add_header(key, val)

        try:
            with urllib.request.urlopen(req) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                ct = resp.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            resp_body = e.read()
            self.send_response(e.code)
            ct = e.headers.get("Content-Type", "application/json")
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as e:
            msg = f"Proxy error: {e}".encode()
            self.send_response(502)
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def log_message(self, format, *args):
        pass  # quiet


def idle_watcher(server):
    if args.keep_alive:
        return
    while True:
        time.sleep(1)
        if initial_load and (time.time() - last_request) >= IDLE_TIMEOUT:
            print(f"\nNo activity for {IDLE_TIMEOUT}s — shutting down.")
            server.shutdown()
            break


os.chdir(DIR)
ensure_assets()

server = None
for port in range(PORT, PORT + 11):
    try:
        server = http.server.HTTPServer(("127.0.0.1", port), TrackedHandler)
        PORT = port
        break
    except OSError:
        continue

if server is None:
    print(f"Could not bind to any port in range 8080-{PORT + 10}.", file=sys.stderr)
    sys.exit(1)

url = f"http://127.0.0.1:{PORT}/index.html"
print(f"\nServing {DIR}")
print(f"Open: {url}")
if args.keep_alive:
    print("KeepAlive enabled — Ctrl+C to stop.")
else:
    print(f"Auto-stops after {IDLE_TIMEOUT}s of inactivity. Use -k/--keep-alive to disable. Ctrl+C to stop manually.")

threading.Timer(0.5, lambda: webbrowser.open(url)).start()
threading.Thread(target=idle_watcher, args=(server,), daemon=True).start()

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    print("Stopped.")
    server.server_close()
