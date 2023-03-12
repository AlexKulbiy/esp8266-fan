import machine
import time
import socket
import select

import onewire
import ds18x20

TEMP_PIN = 5  # Pin D1
FAN_PIN = 13  # Pin D7
RPM_PIN = 12  # Pin D6

# Temperature to start/stop fan
TEMP_LOW = 21
TEMP_HIGH = 27

# Minimum fan speed if triggered by temperature
MIN_FAN_SPEED_PERCENT = 20

# PWM fans use a frequency of 25 kHz
# but esp8266 can provide 1000 max
# More, all PWM pins run at the same frequency, so set globally
# https://docs.micropython.org/en/latest/esp8266/quickref.html#pwm-pulse-width-modulation
PWM_FREQUENCY = 1000

# Will be set to false if changed manually
auto_speed = True


def set_fan_speed(p):
    fan_pin = machine.Pin(FAN_PIN, machine.Pin.OUT)
    pwm0 = machine.PWM(fan_pin)

    pwm0.freq(PWM_FREQUENCY)

    duty = 0
    if p != 0:
        duty = (PWM_FREQUENCY // 100) * p

    pwm0.duty(duty)


def set_fan_speed_temp(temp):
    if temp < TEMP_LOW:
        set_fan_speed(0)
    elif temp > TEMP_HIGH:
        set_fan_speed(100)
    else:
        fan_speed_percent = (100 - MIN_FAN_SPEED_PERCENT) * (temp - TEMP_LOW) // (
            TEMP_HIGH - TEMP_LOW
        ) + MIN_FAN_SPEED_PERCENT
        set_fan_speed(int(fan_speed_percent))


def get_fan_rpm():
    rpm_pin = machine.Pin(RPM_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

    # To stabilize measurement:
    # * wait for value to be 1
    # * check time_pulse on 0
    # time_pulse_us will wait for value to get into desired state before
    #  taking a measurement
    while rpm_pin.value() != 1:
        time.sleep_ms(1)
        pass

    time_low = machine.time_pulse_us(rpm_pin, 0)
    time_high = machine.time_pulse_us(rpm_pin, 1)

    if time_low < 0 or time_high < 0:
        return 0

    # Fan output waveform does two high/low cycles per revolution
    freq = (1000000 // (time_low + time_high)) // 2
    return freq * 60


def gen_response(code, body=None):
    code_to_message_map = {
        200: "OK",
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
    }

    response = ""
    response += "HTTP/1.1 {} {}\n".format(code, code_to_message_map[code])
    response += "Content-Type: text/html\n"
    response += "Connection: close\n\n"
    if body is not None:
        response += body
    return response


def handle_prom(temp, rpm):
    global auto_speed
    tpl = """# HELP esp8266_temperature Temperature in Network Closet in C
# TYPE esp8266_temperature gauge
esp8266_temperature{{room="office"}} {0:.2f}
# HELP esp8266_fan_speed Fan speed in RPM
# TYPE esp8266_fan_speed gauge
esp8266_fan_speed{{room="office"}} {1}
# HELP esp8266_fan_mode Fan mode 1 - auto, 0 - manual
# TYPE esp8266_fan_mode gauge
esp8266_fan_mode{{room="office"}} {2}
"""
    return gen_response(200, tpl.format(temp, rpm, int(auto_speed)))


def handle_method_not_allowed():
    return gen_response(405, "Only GET method allowed")


def handle_not_found():
    return gen_response(404)


def handle_setrpm(path):
    global auto_speed
    # Format /setspeed/<percent>
    p_split = path.split("/setspeed/", 1)
    percent = 0
    try:
        percent = int(p_split[1])
    except IndexError:
        return gen_response(400, "Speed value must follow /setspeed/")
    except ValueError:
        return gen_response(400, "Speed value must be a number between 0 and 100")

    if percent < 0 or percent > 100:
        return gen_response(400, "Speed value must be a number between 0 and 100")

    set_fan_speed(percent)
    auto_speed = False
    return gen_response(200)


def handle_to_auto():
    global auto_speed
    auto_speed = True
    return gen_response(200)


def prepare_response(r, temp, rpm):
    response = ""
    lines = r.split("\r\n")
    # We are only interested in the first line
    req_str = lines[0].split(" ")
    if req_str[0] == "GET":
        path = req_str[1]
        if path == "/":
            response = handle_prom(temp, rpm)
        elif path.startswith("/setspeed/"):
            response = handle_setrpm(path)
        elif path.startswith("/auto"):
            response = handle_to_auto()
        else:
            response = handle_not_found()
    else:
        response = handle_method_not_allowed()

    return response


ds_pin = machine.Pin(TEMP_PIN)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

roms = ds_sensor.scan()
print("Found DS devices: ", roms)
fan_percent = 100

if len(roms) < 1:
    print("Did not get any sensors, exiting")
    exit(1)

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print("listening on", addr)

p = select.poll()
p.register(s, select.POLLIN)

try:
    while True:
        ds_sensor.convert_temp()
        time.sleep_ms(750)
        # Only read first sensor for now
        temperature = ds_sensor.read_temp(roms[0])
        print("Temperature is {} C".format(temperature))

        if auto_speed:
            set_fan_speed_temp(temperature)

        fan_rpm = get_fan_rpm()
        mode = "auto" if auto_speed else "manual"
        print("Fan operates at {} RPM in {} mode".format(fan_rpm, mode))

        events = p.poll(5000)
        for sock, evt in events:
            if evt and select.POLLIN:
                try:
                    conn, addr = s.accept()
                    conn.settimeout(3.0)
                    print("Got a connection from %s" % str(addr))
                    request = conn.recv(1024)
                    conn.settimeout(None)
                    request = request.decode("utf-8")
                    print("Content = %s" % request)

                    response = prepare_response(request, temperature, fan_rpm)
                    conn.sendall(response)
                    conn.close()
                except OSError as e:
                    conn.close()
                    print("Connection closed: {}".format(e))

except KeyboardInterrupt:
    print("Closing socket")
    s.close()
