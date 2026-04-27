import network
import socket
import time
from machine import Pin, PWM
from time import sleep, sleep_ms
import json

# ─── WIFI CREDENTIALS ───────────────────────────────────────────────
SSID     = "PUT SSID HERE"
PASSWORD = "PUT PASSWORD HERE"
# ────────────────────────────────────────────────────────────────────

# ─── STATIC IP CONFIG ───────────────────────────────────────────────
STATIC_IP = "PUT YOUR IP HERE"
SUBNET    = "255.255.255.0"
GATEWAY   = "PUT YOUR GATEWAY HERE"
DNS       = "8.8.8.8"
# ────────────────────────────────────────────────────────────────────

# ─── SERVO SETUP ────────────────────────────────────────────────────
servo = PWM(Pin(0))
servo.freq(50)

def set_angle(angle):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (max_duty - min_duty) * angle / 180)
    servo.duty_u16(duty)

# ─── STATE ──────────────────────────────────────────────────────────
state = {
    "running":      False,
    "stopped":      False,
    "paused":       False,
    "sweep":        0,
    "total_sweeps": 20,
    "countdown":    0,
    "wait_seconds": 30,
    "cycle":        0,
    "status":       "idle",
    "manual_mode":  False,
    "history":      []
}

# ─── WIFI ───────────────────────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.ifconfig((STATIC_IP, SUBNET, GATEWAY, DNS))
    wlan.connect(SSID, PASSWORD)
    print("Connecting to WiFi", end="")
    timeout = 20
    while not wlan.isconnected() and timeout > 0:
        print(".", end="")
        time.sleep(1)
        timeout -= 1
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\n Connected! IP: {ip}")
        print(f"  Open http://{ip} in your browser")
        return ip
    print("\n WiFi connection failed")
    return None

# ─── SERVE HTML (chunked) ────────────────────────────────────────────
def serve_html(conn):
    try:
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
        with open("index.html", "r") as f:
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                conn.send(chunk)
    except Exception as e:
        print(f"HTML serve error: {e}")

def serve_status(conn):
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n")
    conn.send(json.dumps(state))

def send_ok(conn):
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n")
    conn.send('{"ok":true}')

# ─── CHECK REQUESTS MID-SWEEP ───────────────────────────────────────
def check_requests(server_sock):
    try:
        server_sock.settimeout(0)
        conn, addr = server_sock.accept()
        handle_request(conn, server_sock, non_blocking=True)
    except:
        pass

# ─── SINGLE SWEEP PASS (respects pause/stop) ────────────────────────
def do_sweep(server_sock):
    for pos in range(0, 181, 5):
        if state["stopped"]:
            return False
        while state["paused"] and not state["stopped"]:
            check_requests(server_sock)
            sleep_ms(100)
        if state["stopped"]:
            return False
        set_angle(pos)
        sleep_ms(10)
    for pos in range(180, -1, -5):
        if state["stopped"]:
            return False
        while state["paused"] and not state["stopped"]:
            check_requests(server_sock)
            sleep_ms(100)
        if state["stopped"]:
            return False
        set_angle(pos)
        sleep_ms(10)
    return True

# ─── NORMAL RUN (20 sweeps, countdown, loops forever) ───────────────
def run_normal(server_sock):
    state["running"]     = True
    state["stopped"]     = False
    state["paused"]      = False
    state["manual_mode"] = False
    state["total_sweeps"] = 20
    state["status"]      = "sweeping"

    while not state["stopped"]:
        state["cycle"] += 1
        print(f"\n--- Cycle {state['cycle']} ---")

        for i in range(1, 21):
            if state["stopped"]:
                break
            state["sweep"] = i
            print(f"  Sweep {i} of 20")
            if not do_sweep(server_sock):
                break
            check_requests(server_sock)

        if state["stopped"]:
            break

        # Log
        t = time.localtime()
        state["history"].insert(0, {
            "cycle":  state["cycle"],
            "time":   f"{t[3]:02}:{t[4]:02}:{t[5]:02}",
            "sweeps": 20,
            "type":   "normal"
        })
        if len(state["history"]) > 20:
            state["history"].pop()

        # Countdown
        state["status"] = "waiting"
        for remaining in range(state["wait_seconds"], 0, -1):
            if state["stopped"]:
                break
            while state["paused"] and not state["stopped"]:
                check_requests(server_sock)
                sleep_ms(100)
            state["countdown"] = remaining
            print(f"\r  Next cycle in {remaining}s...", end="")
            sleep(1)
            check_requests(server_sock)

        state["countdown"] = 0
        if not state["stopped"]:
            state["status"] = "sweeping"

    state["running"] = False
    state["status"]  = "idle"
    state["sweep"]   = 0
    state["paused"]  = False
    print("\n  Stopped.")

# ─── MANUAL RUN (10 sweeps, no loop) ────────────────────────────────
def run_manual(server_sock):
    state["running"]      = True
    state["stopped"]      = False
    state["paused"]       = False
    state["manual_mode"]  = True
    state["total_sweeps"] = 10
    state["status"]       = "sweeping"

    print("\n--- Manual Run: 10 sweeps ---")

    for i in range(1, 11):
        if state["stopped"]:
            break
        state["sweep"] = i
        print(f"  Sweep {i} of 10")
        if not do_sweep(server_sock):
            break
        check_requests(server_sock)

    if not state["stopped"]:
        t = time.localtime()
        state["history"].insert(0, {
            "cycle":  "-",
            "time":   f"{t[3]:02}:{t[4]:02}:{t[5]:02}",
            "sweeps": 10,
            "type":   "manual"
        })
        if len(state["history"]) > 20:
            state["history"].pop()

    state["running"]      = False
    state["status"]       = "idle"
    state["sweep"]        = 0
    state["total_sweeps"] = 20
    state["manual_mode"]  = False
    print("\n  Manual run complete.")

# ─── HANDLE HTTP REQUEST ─────────────────────────────────────────────
def handle_request(conn, server_sock, non_blocking=False):
    try:
        conn.settimeout(2)
        request = conn.recv(1024).decode("utf-8")

        if "GET /start" in request:
            send_ok(conn)
            conn.close()
            if not state["running"]:
                run_normal(server_sock)

        elif "GET /manual" in request:
            send_ok(conn)
            conn.close()
            if not state["running"]:
                run_manual(server_sock)

        elif "GET /estop" in request:
            if state["paused"]:
                state["paused"] = False
                state["status"] = "sweeping" if state["sweep"] > 0 else "waiting"
                print("  Resumed.")
            else:
                state["paused"] = True
                state["status"] = "paused"
                print("  E-Stop — paused.")
            send_ok(conn)
            conn.close()

        elif "GET /stop" in request:
            state["stopped"]   = True
            state["paused"]    = False
            state["running"]   = False
            state["status"]    = "idle"
            state["sweep"]     = 0
            state["countdown"] = 0
            send_ok(conn)
            conn.close()

        elif "GET /status" in request:
            serve_status(conn)
            conn.close()

        elif "GET / " in request or "GET /index" in request:
            serve_html(conn)
            conn.close()

        else:
            conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
            conn.close()

    except Exception as e:
        if not non_blocking:
            print(f"Request error: {e}")
        try:
            conn.close()
        except:
            pass

# ─── MAIN ────────────────────────────────────────────────────────────
def main():
    print()
    print("╔══════════════════════════╗")
    print("║     BUG SWEEPER v2.0     ║")
    print("╚══════════════════════════╝")
    print()

    ip = connect_wifi()
    if not ip:
        print("Cannot start without WiFi.")
        return

    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server_sock = socket.socket()
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(addr)
    server_sock.listen(5)
    server_sock.settimeout(1)
    print(f"\n  Web server running on http://{ip}")
    print("  Waiting for requests...\n")

    while True:
        try:
            conn, addr = server_sock.accept()
            handle_request(conn, server_sock)
        except:
            pass

main()