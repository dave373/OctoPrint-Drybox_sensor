# OctoPrint-Drybox_sensor

This plugin takes formatted temperature and humidity data from a sensor unit on a serial port to show on the navbar.

I have used a RP2040_zero and AHT10 sensor with micropython to provide the sensor data.

See the extras/sensor/ directory for hardware and micropython code


## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/dave373/OctoPrint-Drybox_sensor/archive/master.zip


## Configuration

Port. The serial port to listen on. Defaults to /dev/ACM0. It is assumed that the port will be an ACM port and the baud rate does not matter.

Set humidity and temperature warning and error levels. These levels will cause the displayed values to change color to orange and red respectively.

The history length will set how many historical values to hold and show in the list when the navbar area is clicked.

The history delay is the time delay between storing values. Use XXs for seconds, XXm for minutes and XXh for hours between values.



