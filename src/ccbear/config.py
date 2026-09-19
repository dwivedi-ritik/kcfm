import json
import os

CLAUDE_DIR = os.path.expanduser("~/.claude")
SESSIONS_DIR = os.path.join(CLAUDE_DIR, "sessions")
PROJECTS_DIR = os.path.join(CLAUDE_DIR, "projects")
STATE_FILE = os.path.expanduser("~/.ccbear.json")
CONF_FILE = os.path.expanduser("~/.ccbear.conf.json")

DEFAULTS = {
    "mark_time": 600,   # secs of inactivity before a session is marked
    "sweep_time": 300,  # secs after marking before it is frozen
    "interval": 120,    # secs between passes in `ccbear run`
}

TERM_WAIT_SECS = 3    # SIGTERM grace before SIGKILL
START_TOLERANCE = 10  # max secs drift when matching process start to startedAt
PIN_TAG = "pin"       # sessions with this tag are never auto-hibernated


def load_conf():
    """DEFAULTS overridden by ~/.ccbear.conf.json; unknown keys ignored."""
    try:
        with open(CONF_FILE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    return {**DEFAULTS, **{k: data[k] for k in DEFAULTS if k in data}}


def set_conf(key, value):
    try:
        with open(CONF_FILE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    data[key] = value
    tmp = CONF_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, CONF_FILE)


def reset_conf():
    """No conf file means defaults."""
    try:
        os.remove(CONF_FILE)
    except FileNotFoundError:
        pass
