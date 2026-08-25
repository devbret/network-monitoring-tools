import json
import socket
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import psutil

MAX_SAMPLES = 60
MONITOR_INTERVAL_SECONDS = 1

BASE_DIR = Path(__file__).resolve().parent
METRICS_PATH = "/api/metrics"

STATIC_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/main.css": ("main.css", "text/css; charset=utf-8"),
    "/main.js": ("main.js", "text/javascript; charset=utf-8"),
}

network_data = []
network_data_lock = threading.Lock()


def tcp_latency_ms(host: str = "google.com", port: int = 443, timeout: float = 1.0) -> float | None:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return (time.perf_counter() - start) * 1000.0
    except OSError:
        return None


def monitor_network(interval: float = MONITOR_INTERVAL_SECONDS) -> None:
    previous_net_io = psutil.net_io_counters()
    psutil.cpu_percent(interval=None)

    while True:
        time.sleep(interval)

        current_net_io = psutil.net_io_counters()
        metrics: dict[str, object] = {}
        metrics["timestamp"] = time.time()

        metrics["bytes_sent"] = current_net_io.bytes_sent - previous_net_io.bytes_sent
        metrics["bytes_recv"] = current_net_io.bytes_recv - previous_net_io.bytes_recv
        previous_net_io = current_net_io

        metrics["cpu_percent"] = psutil.cpu_percent(interval=None)
        metrics["memory_percent"] = psutil.virtual_memory().percent

        try:
            metrics["active_connections"] = len(psutil.net_connections())
        except Exception:
            metrics["active_connections"] = None

        metrics["latency_ms"] = tcp_latency_ms("google.com", 443, timeout=1.0)

        with network_data_lock:
            network_data.append(metrics)
            if len(network_data) > MAX_SAMPLES:
                network_data.pop(0)


class DashboardHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "NetworkMonitor/1.0"

    def do_GET(self) -> None:
        path = urlsplit(self.path).path

        if path == METRICS_PATH:
            self._serve_metrics()
        elif path in STATIC_ROUTES:
            self._serve_static(*STATIC_ROUTES[path])
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _serve_metrics(self) -> None:
        with network_data_lock:
            snapshot = list(network_data)

        self._send_bytes(json.dumps(snapshot).encode("utf-8"), "application/json")

    def _serve_static(self, filename: str, content_type: str) -> None:
        try:
            body = (BASE_DIR / filename).read_bytes()
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        self._send_bytes(body, content_type)

    def _send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        try:
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def log_request(self, code="-", size="-") -> None:
        if code == HTTPStatus.OK and urlsplit(self.path).path == METRICS_PATH:
            return
        super().log_request(code, size)


def run_server(host: str = "localhost", port: int = 8500) -> None:
    httpd = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Serving http://{host}:{port}/ (metrics at {METRICS_PATH})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
    finally:
        httpd.server_close()


if __name__ == "__main__":
    threading.Thread(target=monitor_network, daemon=True).start()
    run_server()
