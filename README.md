# Network Monitoring Tools

![Organized YouTube playlists with counters for the next video to watch.](https://hosting.photobucket.com/bbcfb0d4-be20-44a0-94dc-65bff8947cf2/5374cd8c-55fe-431a-8451-0693e2e59fef.png)

Monitor six vital network metrics with displays that update every second. Those measurements include bandwidth usage, CPU usage and network latency.

## Overview

A real-time local network and system monitoring dashboard which collects live performance metrics from your machine using Python and psutil, stores the most recent data samples in a rolling JSON file and visualizes them in the browser using D3.js.

Every second this application measures bandwidth usage, CPU utilization, memory usage, active network connections and internet latency, then serves the data through a lightweight HTTP server to a stylized web interface which renders dynamic, continuously updating line charts with readouts. The result is a self-hosted, real-time performance observatory for monitoring system and network health.

## Set Up

Below are the software programs and installation steps needed for this application to function properly.

### Required Software

- [Git](https://git-scm.com/downloads)

- [Python](https://www.python.org/downloads/)

### Installation Steps

1. Install the above programs

2. Open a terminal

3. Clone this repository using `git` by running the following command: `git clone git@github.com:devbret/network-monitoring-tools.git`

4. Navigate to the repo's directory by running: `cd network-monitoring-tools`

5. Install the needed dependencies for running the script by running: `pip install -r requirements.txt`

6. Run the script with the command `python3 app.py`

7. Start a second web server for the frontend, by using the Live Server Visual Studio Code extension
