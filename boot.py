def do_connect():
    try:
        f = open("wifi_SSID")
    except Exception as e:
        print("Failed to open wifi_SSID file: {}".format(e))
        exit(1)

    SSID = f.read()
    f.close()

    try:
        f = open("wifi_pass")
    except Exception as e:
        print("Failed to open wifi_pass file: {}".format(e))
        exit(1)

    PASS = f.read()
    f.close

    import network

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("connecting to network...")
        sta_if.active(True)
        sta_if.connect(SSID, PASS)
        while not sta_if.isconnected():
            pass
    print("network config:", sta_if.ifconfig())


do_connect()
