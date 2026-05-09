# 🕷️ Bug Sweeper

A MicroPython web-controlled servo system running on a Raspberry Pi Pico W. Built to automate the removal of bugs, spider webs, and debris from outdoor security camera lenses — controllable from any browser on the local network without touching the hardware.

---

## Real-World Use Case

Outdoor security cameras in rural environments collect spider webs, bugs, and debris on the lens over time. Manually cleaning them means physically accessing the camera mount. Bug Sweeper attaches an SG90 servo directly to the camera housing and sweeps a cleaning arm across the lens on a scheduled cycle or on demand via a local web dashboard — no ladder required.

---

## Features

- **Web dashboard** served directly from the Pico W over local WiFi
- **Start Sweep** — runs continuous 20-sweep cycles with a 30-second countdown between each
- **Manual 10** — triggers a quick 10-sweep one-shot run for on-demand cleaning
- **E-Stop** — pauses the servo mid-sweep instantly; resumes exactly where it left off
- **Live progress** — real-time sweep counter, progress bar, and animated countdown ring
- **Sweep history log** — timestamped log of every completed run, distinguishing normal vs manual runs
- **Static IP** — configured directly on the Pico for consistent local network access

---

## Hardware

| Component | Details |
|-----------|---------|
| Microcontroller | Raspberry Pi Pico W |
| Servo | SG90 Micro Servo (180°) |
| Power | 5V USB power supply |
| Language | MicroPython |

### Wiring

| SG90 Wire | Pico W Pin |
|-----------|------------|
| Brown (GND) | GND |
| Red (VCC) | VBUS (Pin 40 — 5V) |
| Orange (Signal) | GP0 (Pin 1) |

> ⚠️ Use VBUS (5V) not 3.3V for the SG90 — it requires 4.8–6V to operate reliably.

---

## Project Origin

This project started as an Arduino sketch and was translated to MicroPython for the Pico W. The original sketch used `Servo.h` and Arduino's `delay()` — the MicroPython version manually handles PWM duty cycles via `machine.PWM` and `duty_u16()` since MicroPython does not have a built-in servo library.

---

## Setup

### 1. Flash MicroPython
- Hold **BOOTSEL** on the Pico W and plug into your PC
- Download the latest Pico W MicroPython firmware from [micropython.org](https://micropython.org/download/RPI_PICO_W/)
- Drag the `.uf2` file onto the RPI-RP2 drive that appears

### 2. Configure credentials
Open `main.py` and fill in your network details:

```python
SSID      = "YOUR_WIFI_NAME_HERE"
PASSWORD  = "YOUR_WIFI_PASSWORD_HERE"
STATIC_IP = "YOUR_STATIC_IP_HERE"
SUBNET    = "255.255.255.0"
GATEWAY   = "YOUR_GATEWAY_HERE"
DNS       = "8.8.8.8"
```

> The Pico W only supports **2.4GHz** WiFi networks.

### 3. Set a static IP
Configure a static IP directly in `main.py` using an address outside your router's DHCP range (e.g. `192.168.x.200`). This ensures the dashboard is always reachable at the same address.

### 4. Upload files
Using [Thonny](https://thonny.org/) or your preferred MicroPython tool, upload both files to the Pico W:
- `main.py`
- `index.html`

### 5. Access the dashboard
Power the Pico W from any USB power supply. Open a browser on the same network and navigate to:

```
http://YOUR_STATIC_IP
```

---

## File Structure

```
pico-bug-sweeper/
├── main.py       # Web server, servo control, state management
├── index.html    # Web dashboard (served directly from Pico W)
└── README.md
```

---

## Tech Stack

- **MicroPython** — firmware and servo control
- **machine.PWM / duty_u16()** — manual PWM duty cycle calculation for servo positioning
- **socket** — lightweight HTTP server running on port 80
- **JSON** — state serialization between Pico and browser
- **HTML / CSS / JavaScript** — dashboard frontend with live polling via `fetch()`

---

## Notes

- The web server polls `/status` every second via JavaScript `fetch()` to update the dashboard in real time
- HTML is served in 512-byte chunks due to Pico W memory constraints
- The E-Stop holds the servo at its current position and blocks the sweep loop until resumed — the cycle count and sweep position are preserved
- Manual runs are logged separately in the history with a `MANUAL` badge

---

## License

MIT
