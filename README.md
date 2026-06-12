# Network Monitoring Tools

![Organized YouTube playlists with counters for the next video to watch.](https://hosting.photobucket.com/bbcfb0d4-be20-44a0-94dc-65bff8947cf2/5374cd8c-55fe-431a-8451-0693e2e59fef.png)

Monitor six vital network metrics including bandwidth usage, CPU usage and network latency with displays which update every second.

## Application Overview

A local network and system monitoring dashboard which collects recent performance metrics from your machine using Python and `psutil`, stores a set of samples in a JSON file and visualizes the data in the browser using D3.js.

Every second, the application records bytes sent and received, CPU utilization, memory usage, active network connection count and TCP connection latency to Google over port 443. It serves the frontend and data file through a lightweight local HTTP server, allowing the browser interface to render continuously updating line charts and readouts for recent system and network activity.

## Basic Setup Instructions

Below are the software programs and installation steps needed for this application to function properly on a Linux machine.

### Required Software

- [Git](https://git-scm.com/downloads)

- [Python](https://www.python.org/downloads/)

### Installation Steps

1. Install the above programs

2. Open a terminal

3. Clone this repository: `git clone git@github.com:devbret/network-monitoring-tools.git`

4. Navigate to the repo's directory: `cd network-monitoring-tools`

5. Create a virtual environment: `python3 -m venv venv`

6. Activate the virtual environment: `source venv/bin/activate`

7. Install the needed dependencies: `pip install -r requirements.txt`

8. Run the script: `python3 app.py`

9. View the frontend in a browser: `http://localhost:8500/`

10. When finished, shutdown the HTTP server: `CTRL + C`

11. Exit the virtual environment: `deactivate`

## Other Considerations

This project repo is intended to demonstrate an ability to do the following:

- Monitor network activity, system resource usage, active connections and latency in real time

- Collect network metrics every second and save the most recent samples to a JSON file

- Serve live network performance data through a local web server for browser-based visualization

- Use D3.js to display real-time charts for bandwidth, CPU usage, memory usage, connections and latency

If you have any questions or would like to collaborate, please reach out either on GitHub or via [my website](https://bretbernhoft.com/).
