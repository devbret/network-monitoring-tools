import ipaddress
import json
import logging
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
CONNECTION_SCAN_INTERVAL_SECONDS = 1
LATENCY_HOST = "google.com"
LATENCY_PORT = 443
LATENCY_TIMEOUT_SECONDS = 1.0

BASE_DIR = Path(__file__).resolve().parent
METRICS_PATH = "/api/metrics"

STATIC_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/main.css": ("main.css", "text/css; charset=utf-8"),
    "/main.js": ("main.js", "text/javascript; charset=utf-8"),
}

log = logging.getLogger("network_monitor")

network_data = []
network_data_lock = threading.Lock()


def is_loopback_address(address: str) -> bool:
    try:
        return ipaddress.ip_address(address.split("%", 1)[0]).is_loopback
    except ValueError:
        return False


def loopback_interfaces() -> frozenset[str]:
    names = set()
    for nic, addresses in psutil.net_if_addrs().items():
        for addr in addresses:
            if addr.family in (socket.AF_INET, socket.AF_INET6) and is_loopback_address(addr.address):
                names.add(nic)
                break
    return frozenset(names)


def external_io_counters(exclude: frozenset[str]) -> tuple[int, int]:
    sent = recv = 0
    for nic, counters in psutil.net_io_counters(pernic=True).items():
        if nic in exclude:
            continue
        sent += counters.bytes_sent
        recv += counters.bytes_recv
    return sent, recv


class LatencyProbe:
    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._target: tuple[int, tuple] | None = None

    @property
    def remote(self) -> tuple[str, int] | None:
        target = self._target
        if target is None:
            return None
        sockaddr = target[1]
        return sockaddr[0], sockaddr[1]

    def _resolve(self) -> tuple[int, tuple] | None:
        try:
            infos = socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM)
        except OSError:
            return None
        if not infos:
            return None
        family, _socktype, _proto, _canonname, sockaddr = infos[0]
        return family, sockaddr

    def measure(self) -> float | None:
        if self._target is None:
            self._target = self._resolve()
            if self._target is None:
                return None

        family, sockaddr = self._target
        start = time.perf_counter()
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect(sockaddr)
        except OSError:
            self._target = None
            return None
        return (time.perf_counter() - start) * 1000.0


class ConnectionCounter:
    def __init__(self, interval: float, probe: LatencyProbe | None = None) -> None:
        self.interval = interval
        self.probe = probe
        self._count: int | None = None
        self._lock = threading.Lock()
        self._access_warned = False

    @property
    def count(self) -> int | None:
        with self._lock:
            return self._count

    def scan(self) -> int | None:
        try:
            connections = psutil.net_connections(kind="tcp")
        except psutil.AccessDenied:
            if not self._access_warned:
                log.warning("Cannot list connections without elevated privileges; reporting none")
                self._access_warned = True
            return None

        ignored = self.probe.remote if self.probe is not None else None
        total = 0
        for conn in connections:
            if conn.status != psutil.CONN_ESTABLISHED or not conn.raddr:
                continue
            if is_loopback_address(conn.raddr.ip):
                continue
            if ignored is not None and (conn.raddr.ip, conn.raddr.port) == ignored:
                continue
            total += 1
        return total

    def run(self) -> None:
        while True:
            try:
                count = self.scan()
            except Exception:
                log.exception("Connection scan failed")
                count = None
            with self._lock:
                self._count = count
            time.sleep(self.interval)


def monitor_network(
    interval: float,
    probe: LatencyProbe,
    connections: ConnectionCounter,
) -> None:
    loopback = loopback_interfaces()
    previous_sent, previous_recv = external_io_counters(loopback)
    previous_time = time.monotonic()
    psutil.cpu_percent(interval=None)

    while True:
        time.sleep(interval)

        try:
            sent, recv = external_io_counters(loopback)
            now = time.monotonic()
            elapsed = now - previous_time

            metrics: dict[str, object] = {
                "timestamp": time.time(),
                "bytes_sent": round(max(0, sent - previous_sent) / elapsed, 1),
                "bytes_recv": round(max(0, recv - previous_recv) / elapsed, 1),
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "active_connections": connections.count,
                "latency_ms": probe.measure(),
            }
            previous_sent, previous_recv, previous_time = sent, recv, now
        except Exception:
            log.exception("Metric collection failed; skipping this sample")
            continue

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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    probe = LatencyProbe(LATENCY_HOST, LATENCY_PORT, LATENCY_TIMEOUT_SECONDS)
    connections = ConnectionCounter(CONNECTION_SCAN_INTERVAL_SECONDS, probe)

    threading.Thread(target=connections.run, daemon=True).start()
    threading.Thread(
        target=monitor_network,
        args=(MONITOR_INTERVAL_SECONDS, probe, connections),
        daemon=True,
    ).start()
    run_server()
