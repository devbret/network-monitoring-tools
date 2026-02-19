import json
import socket
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

import psutil

MAX_SAMPLES = 60
SAVE_INTERVAL_SECONDS = 1
MONITOR_INTERVAL_SECONDS = 1

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


def save_network_data() -> None:
    while True:
        with network_data_lock:
            snapshot = list(network_data)

        tmp_path = "network_data.json.tmp"
        final_path = "network_data.json"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f)
        try:
            import os
            os.replace(tmp_path, final_path)
        except Exception:
            with open(final_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f)

        time.sleep(SAVE_INTERVAL_SECONDS)


def run_server(port: int = 8000) -> None:
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(("localhost", port), handler)
    httpd.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=monitor_network, daemon=True).start()
    threading.Thread(target=save_network_data, daemon=True).start()
    run_server()