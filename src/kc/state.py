import json
import os

from .config import STATE_FILE


def load():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}
    for key in ("hibernated", "marks"):
        state.setdefault(key, {})
    return state


def save(state):
    # temp + rename so a concurrent kc never sees a half-written file
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def reconcile(state, live):
    """Drop hibernated entries already woken elsewhere, and marks for dead sessions."""
    live_sids = {s["sid"] for s in live}
    for sid in [s for s in state["hibernated"] if s in live_sids]:
        del state["hibernated"][sid]

    for sid in [s for s in state["marks"] if s not in live_sids]:
        del state["marks"][sid]

    # Removing session which are already closed 
    for sid in state["hibernated"]:
        if sid not in live_sids:
            del state["hibernated"][sid]

    for sid in state["marks"]:
            if sid not in live_sids:
                del state["marks"][sid]

    save(state)


