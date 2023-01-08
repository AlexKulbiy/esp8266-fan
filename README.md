# ESP8266 Fan Control

Based on [this](https://github.com/stefanthoss/esp8266-fan-control).

This is a simple solution to have a fan, managed by a ESP8266.
By default, the speed of fan is automatically set based on the
temperature reported by the sensor.

This app is written in [micropython](https://micropython.org/).

## Usage

Before first upload, create two files on the device:
`wifi_SSID` and `wifi_pass`. You can use [`ampy`](https://github.com/scientifichackers/ampy)
for this.  Files should contain the SSID and password
of the WiFi network ESP8266 will connect to respectively.

Then upload `boot.py` and `main.py`. This also can be done using `ampy`.

Once connected to the WiFi, the controller will start a simple webserver with the following endpoints:

| Endpoint | Description |
| -------- | ----------- |
| `/` | Reports metrics in Prometheus format |
| `/setspeed/<number>` | Manually sets fan speed for `<number>`% of max RPM |
| `/auto` | Switches fan to automatic RPM mode (see below) |

The webserver only accepts GET requests. Any other verb will result
in HTTP 400 response.

## Modes

The device can operate in two modes: automatic (default) and manual.
In the automatic mode, the speed is set based on the temperature as
follows:

* < 21°C - the fan is off
* 21°C - 27
