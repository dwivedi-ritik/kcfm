"""Background watcher lifecycle: start / stop / status.

The daemon record lives in the config file alongside settings, so
`--reset-config` also stops it (see cli.handle_config_flags).
"""

import os
import shutil
import signal
import subprocess
import sys
import time

from .config import (LOG_FILE, START_TOLERANCE, clear_daemon, get_daemon,
                     set_daemon)
from .policy import fmt_dur
from .sessions import proc_start_epoch


def _alive(rec):
    """True if the recorded daemon pid is still our running process."""
    if not rec or not rec.get("pid"):
        return False
    try:
        os.kill(rec["pid"], 0)
    except OSError:
        return False
    # pid-reuse guard: start time must match what we recorded
    start = proc_start_epoch(rec["pid"])
    if start is not None and rec.get("startEpoch"):
        return abs(start - rec["startEpoch"]) < START_TOLERANCE
    return True


def is_running():
    return _alive(get_daemon())


def _self_cmd():
    """Command to relaunch ccbear, resolving argv[0] to an absolute path."""
    prog = sys.argv[0]
    if os.path.sep not in prog:
        prog = shutil.which(prog) or prog
    return [sys.executable, os.path.abspath(prog), "run"]


def start():
    if is_running():
        print(f"already running (pid {get_daemon()['pid']})")
        return
    log = open(LOG_FILE, "a")
    p = subprocess.Popen(
        _self_cmd(),
        stdin=subprocess.DEVNULL, stdout=log, stderr=log,
        start_new_session=True,  # detach from this terminal
    )
    time.sleep(0.3)  # surface an immediate crash instead of reporting success
    if p.poll() is not None:
        print(f"failed to start; see {LOG_FILE}")
        return
    set_daemon({"pid": p.pid, "startEpoch": proc_start_epoch(p.pid),
                "startedAt": time.time()})
    print(f"ccbear running in background (pid {p.pid}); log: {LOG_FILE}")


def stop_running():
    """Kill the watcher if running. Returns the killed pid, or None."""
    rec = get_daemon()
    if not _alive(rec):
        if rec:
            clear_daemon()
        return None
    try:
        os.kill(rec["pid"], signal.SIGTERM)
    except ProcessLookupError:
        pass
    clear_daemon()
    return rec["pid"]


def stop():
    pid = stop_running()
    print(f"stopped (pid {pid})" if pid else "not running")


def status():
    rec = get_daemon()
    if _alive(rec):
        up = fmt_dur(time.time() - rec.get("startedAt", time.time()))
        print(f"running (pid {rec['pid']}, up {up}); log: {LOG_FILE}")
    else:
        print("not running")
