from config import WAIT_SECONDS

# status values: "sweeping" | "waiting" | "paused" | "manual"
state = {
    "status":         "sweeping",
    "sweep":          0,
    "total_sweeps":   20,
    "cycle":          0,
    "countdown":      0,
    "paused":         False,
    "pre_pause":      "sweeping",
    "manual_running": False,
    "manual_sweep":   0,
    "wait_seconds":   WAIT_SECONDS,
    "history":        []
}
