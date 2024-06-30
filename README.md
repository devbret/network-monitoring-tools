# Network Monitoring Tools

![Organized YouTube playlists with counters for the next video to watch.](https://hosting.photobucket.com/images/i/bernhoftbret/network-monitoring-tools-ui-minor-improvements.png)

Monitor six vital network metrics with displays that update every second. Those measurements include bandwidth usage, CPU usage and network latency.

## Set Up

### Programs Needed

-   [Git](https://git-scm.com/downloads)
-   [Python](https://www.python.org/downloads/) (When installing on Windows, make sure you check the ["Add python 3.xx to PATH"](https://hosting.photobucket.com/images/i/bernhoftbret/python.png) box.)

### Steps

1. Install the above programs.
2. Open a shell window (For Windows open PowerShell, for MacOS open Terminal and for Linux open your distro's terminal emulator).
3. Clone this repository using `git` by running the following command; `git clone https://github.com/devbret/network-monitoring-tools`.
4. Navigate to the repo's directory by running; `cd network-monitoring-tools`.
5. Install the needed dependencies for running the script by running; `pip install -r requirements.txt`.
6. Run the script with the command `python3 app.py`. After the Flask server has started, I typically start a second web server for the frontend, by using the Live Server Visual Studio Code extension.
7. After doing so, visit `http://127.0.0.1:5500/` in a browser, and you will be brought to the application.
