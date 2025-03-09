#!/bin/bash

# Add this line to /etc/systemd/systemc/octoprint.service without the '#', modify path if required
#    ExecStartPre=+/home/pi/.octoprint/plugins/OctoPrint-Drybox_sensor/octoprint_drybox_sensor/libs/mktmpfile.sh

mkdir -p /run/plugins
touch /run/plugins/drybox.rrd
chown pi:pi /run/plugins/drybox.rrd

