import json
import time
from time import sleep, sleep_ms
import state
from hardware import set_angle
from config import SWEEP_STEP

# ── HTTP ─────────────────────────────────────────────────────────────

def send_ok(conn):
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
              "Cache-Control: no-cache\r\nConnection: close\r\n\r\n{\"ok\":true}")

def serve_status(conn):
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
              "Cache-Control: no-cache\r\nConnection: close\r\n\r\n")
    conn.send(json.dumps(state.state))

def serve_html(conn):
    try:
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
                  "Cache-Control: no-cache, no-store, must-revalidate\r\n"
                  "Pragma: no-cache\r\nExpires: 0\r\nConnection: close\r\n\r\n")
        with open("index.html") as f:
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                conn.send(chunk)
                sleep_ms(5)
    except Exception as e:
        print(f"HTML error: {e}")

# ── HELPERS ──────────────────────────────────────────────────────────

def check(sock):
    """Non-blocking check for incoming requests mid-sweep."""
    try:
        sock.settimeout(0)
        conn, _ = sock.accept()
        handle(conn, sock, nb=True)
    except:
        pass

def log(label, sweeps, kind):
    t = time.localtime()
    state.state["history"].insert(0, {
        "label":  label,
        "time":   f"{t[3]:02}:{t[4]:02}:{t[5]:02}",
        "sweeps": sweeps,
        "type":   kind
    })
    if len(state.state["history"]) > 20:
        state.state["history"].pop()

# ── SERVO ────────────────────────────────────────────────────────────

def move(sock, ignore_pause=False):
    """
    One full sweep 0->180->0.
    Returns True on completion, False if stopped.
    Respects pause unless ignore_pause=True (manual sweeps).
    """
    for positions in (range(0, 181, SWEEP_STEP), range(180, -1, -SWEEP_STEP)):
        for pos in positions:
            # Check for pause (not used during manual)
            if not ignore_pause:
                while state.state["paused"]:
                    check(sock)
                    sleep_ms(100)
            set_angle(pos)
            sleep_ms(10)
    return True

# ── MAIN CYCLE ───────────────────────────────────────────────────────

def run_forever(sock):
    """
    Main cycle. Runs on boot, loops indefinitely.
    20 sweeps -> wait -> repeat.
    E-Stop pauses/resumes. Manual runs independently during wait.
    """
    s = state.state

    while True:
        # ── SWEEP PHASE ──
        s["status"] = "sweeping"
        s["cycle"]  += 1
        print(f"\n=== Cycle {s['cycle']} ===")

        for i in range(1, 21):
            s["sweep"] = i
            print(f"  Sweep {i}/20")
            move(sock)

        log(s["cycle"], 20, "normal")
        s["sweep"] = 0

        # ── WAIT PHASE ──
        s["status"]   = "waiting"
        end_time      = time.time() + s["wait_seconds"]
        print(f"\n  Waiting {s['wait_seconds']}s...\n")

        while True:
            # Handle pause during wait
            if s["paused"]:
                pause_start = time.time()
                print("  [paused]")
                while s["paused"]:
                    check(sock)
                    sleep_ms(100)
                # Extend end time by how long we were paused
                end_time += time.time() - pause_start
                print("  [resumed]")

            remaining = int(end_time - time.time())
            if remaining <= 0:
                break

            s["countdown"] = remaining
            sleep(1)
            check(sock)

        s["countdown"] = 0

# ── MANUAL ───────────────────────────────────────────────────────────

def run_manual(sock):
    """
    10 manual sweeps. Only blocked when status is 'sweeping'.
    Countdown continues untouched in the background.
    Manual sweeps ignore pause.
    """
    s = state.state

    if s["status"] == "sweeping":
        print("  Manual blocked — servo in use")
        return

    prev_status = s["status"]
    s["manual_running"] = True
    s["status"] = "manual"
    print("\n=== Manual Sweep: 10 passes ===")

    for i in range(1, 11):
        s["manual_sweep"] = i
        print(f"  Manual {i}/10")
        move(sock, ignore_pause=True)
        check(sock)
        
    log("MAN", 10, "manual")
    s["manual_running"] = False
    s["manual_sweep"]   = 0
    s["status"]         = prev_status
    print("  Manual complete.")

# ── REQUEST HANDLER ──────────────────────────────────────────────────

def handle(conn, sock, nb=False):
    try:
        conn.settimeout(2)
        req = conn.recv(1024).decode()

        if "GET /estop" in req:
            s = state.state
            if s["paused"]:
                s["paused"] = False
                print("  Resumed")
            else:
                s["paused"] = True
                print("  Paused")
            send_ok(conn)
            conn.close()

        elif "GET /manual" in req:
            send_ok(conn)
            conn.close()
            run_manual(sock)

        elif "GET /status" in req:
            serve_status(conn)
            conn.close()

        elif "GET / " in req or "GET /index" in req:
            serve_html(conn)
            conn.close()

        else:
            conn.send("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
            conn.close()

    except Exception as e:
        if not nb:
            print(f"Request error: {e}")
        try:
            conn.close()
        except:
            pass
