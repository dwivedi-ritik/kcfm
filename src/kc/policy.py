"""Mark-and-sweep: mark idle sessions, reprieve on activity, sweep after grace."""

import time

from . import state as state_mod
from .actions import sleep_one
from .config import load_conf
from .sessions import has_children, live_sessions


def fmt_dur(secs):
    secs = max(0, int(secs))
    if secs >= 86400:
        return f"{secs // 86400}d{secs % 86400 // 3600}h"
    if secs >= 3600:
        return f"{secs // 3600}h{secs % 3600 // 60}m"
    if secs >= 60:
        return f"{secs // 60}m"
    return f"{secs}s"


def auto_pass(state):
    cfg = load_conf()  # re-read each pass so config changes apply live
    live = live_sessions()
    state_mod.reconcile(state, live)
    now = time.time()
    for s in live:
        sid, label = s["sid"], s["name"] or s["sid"][:8]
        mark = state["marks"].get(sid)
        active = (s["status"] == "busy" or has_children(s["pid"])
                  or now - s["last_activity"] < cfg["mark_time"])
        if active:
            if mark:
                del state["marks"][sid]
                state_mod.save(state)
                print(f"reprieved {label}")
            continue
        if mark:
            if (s["tsize"], s["tmtime"]) != (mark["tsize"], mark["tmtime"]):
                del state["marks"][sid]
                state_mod.save(state)
                print(f"reprieved {label}")
            elif now - mark["markedAt"] >= cfg["sweep_time"]:
                sleep_one(s, state)
        elif s["tsize"] is not None:
            state["marks"][sid] = {"markedAt": now, "tsize": s["tsize"],
                                   "tmtime": s["tmtime"]}
            state_mod.save(state)
            print(f"marked {label}: sleeping in {fmt_dur(cfg['sweep_time'])} unless active")
