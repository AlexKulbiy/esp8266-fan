def do_connect():
    SSID = "<setme>"
    PASS = "<setme>"
    import network

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("connecting to network...")
        sta_if.active(True)
        sta_if.connect(SSID, PASS)
        while not sta_if.isconnected():
            pass
    print("network config:", sta_if.ifconfig())


# def do_install():
#     import upip

#     upip.install("urequests")
