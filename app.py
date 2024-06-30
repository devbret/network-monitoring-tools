import psutil
import time
import json
import threading
from ping3 import ping
from http.server import SimpleHTTPRequestHandler, HTTPServer

network_data = []

def monitor_network(interval=1):
    previous_net_io = psutil.net_io_counters()
    while True:
        time.sleep(interval)
        current_net_io = psutil.net_io_counters()
        metrics = {}
        metrics['timestamp'] = time.time()

        metrics['bytes_sent'] = current_net_io.bytes_sent - previous_net_io.bytes_sent
        metrics['bytes_recv'] = current_net_io.bytes_recv - previous_net_io.bytes_recv
        previous_net_io = current_net_io

        metrics['cpu_percent'] = psutil.cpu_percent()
        metrics['memory_percent'] = psutil.virtual_memory().percent

        metrics['active_connections'] = len(psutil.net_connections())

        metrics['latency'] = ping('google.com')

        network_data.append(metrics)
        if len(network_data) > 60:  
            network_data.pop(0)

def run_server(port=8000):
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(('localhost', port), handler)
    httpd.serve_forever()

def save_network_data():
    while True:
        with open("network_data.json", "w") as f:
            json.dump(network_data, f)
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=monitor_network).start()
    threading.Thread(target=save_network_data).start()
    run_server()
