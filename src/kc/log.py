"""Structured, colored log lines shared by the watcher and manual commands.

Colors are written into the line unconditionally: the log file is meant to be
read through `kc log` (tail -f in a terminal), and foreground output goes
straight to a terminal too. Event colors match the `ls` state colors.
"""

import time

# event tag -> ANSI color (same palette as cli STATE/SWEEP columns)
COLORS = {
    "WATCH": "2",     # dim
    "MARK": "33",     # yellow — matches "marked"
    "SLEEP": "36",    # cyan — matches "freed"
    "REPRIEVE": "32", # green — session stayed alive
    "SKIP": "2",      # dim
}


def event(tag, msg=""):
    ts = time.strftime("%H:%M:%S")
    code = COLORS.get(tag, "")
    label = f"\033[{code}m{tag:<8}\033[0m" if code else f"{tag:<8}"
    print(f"\033[2m{ts}\033[0m  {label}  {msg}".rstrip())
