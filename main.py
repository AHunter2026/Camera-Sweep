import network
import socket
import time
from config import SSID, PASSWORD, STATIC_IP, SUBNET, GATEWAY, DNS
import server

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.ifconfig((STATIC_IP, SUBNET, GATEWAY, DNS))
    wlan.connect(SSID, PASSWORD)
    print("Connecting", end="")
    for _ in range(20):
        if wlan.isconnected():
            break
        print(".", end="")
        time.sleep(1)
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\n  Online: http://{ip}")
        return ip
    print("\n  WiFi failed")
    return None

def main():
    print("\n=== BUG SWEEPER v3.0 ===\n")
    ip = connect_wifi()
    if not ip:
        return

    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(socket.getaddrinfo("0.0.0.0", 80)[0][-1])
    sock.listen(5)
    sock.settimeout(1)
    print(f"  Serving on http://{ip}\n")

    server.run_forever(sock)

main()
