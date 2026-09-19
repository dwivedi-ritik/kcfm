"""Sleep and wake sessions."""

import os
import signal
import sys
import time

from . import state as state_mod
from .config import TERM_WAIT_SECS
from .sessions import proc_rss_mb, resolve


def sleep_one(s, state):
    """Snapshot then kill one live session. Returns freed MB or None."""
    label = s["name"] or s["sid"][:8]
    if s["tsize"] is None:
        print(f"skip {label}: no transcript yet, nothing to resume")
        return None
    rss = proc_rss_mb(s["pid"])
    # snapshot BEFORE killing: graceful exit deletes claude's sessions/<pid>.json
    state["hibernated"][s["sid"]] = {
        "name": s["name"], "cwd": s["cwd"], "frozenAt": time.time(),
        "freedMb": rss,
    }
    state["marks"].pop(s["sid"], None)
    state_mod.save(state)
    try:
        os.kill(s["pid"], signal.SIGTERM)
        deadline = time.time() + TERM_WAIT_SECS
        while time.time() < deadline:
            time.sleep(0.1)
            os.kill(s["pid"], 0)
        os.kill(s["pid"], signal.SIGKILL)
    except ProcessLookupError:
        pass
    print(f"slept {label} ({s['sid'][:8]}), freed ~{rss}MB")
    return rss


def wake(target, state, live):
    live_hits, hib = resolve(target, live, state)
    if live_hits and not hib:
        print(f"'{target}' is already awake")
        return
    if len(hib) != 1:
        names = ", ".join(h.get("name") or sid[:8] for sid, h in hib.items())
        print(f"{'no' if not hib else 'multiple'} hibernated sessions match "
              f"'{target}'" + (f": {names}" if hib else ""))
        sys.exit(1)
    sid, h = next(iter(hib.items()))
    del state["hibernated"][sid]
    state_mod.save(state)
    if h.get("cwd"):
        os.chdir(h["cwd"])
    # exec replaces this process — the session resumes in the user's terminal
    os.execvp("claude", ["claude", "--resume", sid])
