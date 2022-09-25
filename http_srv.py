import socket

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print("listening on", addr)

# # HELP bme_680_temperature Temperature in Bedroom in C
# # TYPE bme_680_temperature gauge
# bme_680_temperature{room="bedroom"} 22.7408

resp = """"# HELP esp8266_temperature Temperature in Network Closet in C
# TYPE esp8266_temperature gauge
esp8266_temperature{room="office"} {}
"""

while True:
    cl, addr = s.accept()
    print("client connected from", addr)
    response = resp.format(temp)
    cl.send("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
    cl.send(response)
    cl.close()
