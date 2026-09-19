import json
import os

CLAUDE_DIR = os.path.expanduser("~/.claude")
SESSIONS_DIR = os.path.join(CLAUDE_DIR, "sessions")
PROJECTS_DIR = os.path.join(CLAUDE_DIR, "projects")
STATE_FILE = os.path.expanduser("~/.ccbear.json")
CONF_FILE = os.path.expanduser("~/.ccbear.conf.json")
LOG_FILE = os.path.expanduser("~/.ccbear.log")

DEFAULTS = {
    "mark_time": 600,   # secs of inactivity before a session is marked
    "sweep_time": 300,  # secs after marking before it is frozen
    "interval": 120,    # secs between passes in `ccbear run`
}

TERM_WAIT_SECS = 3    # SIGTERM grace before SIGKILL
START_TOLERANCE = 10  # max secs drift when matching process start to startedAt
PIN_TAG = "pin"       # sessions with this tag are never auto-hibernated


def _read_raw():
    try:
        with open(CONF_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _write_raw(data):
    tmp = CONF_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, CONF_FILE)


def load_conf():
    """DEFAULTS overridden by ~/.ccbear.conf.json; unknown keys ignored."""
    data = _read_raw()
    return {**DEFAULTS, **{k: data[k] for k in DEFAULTS if k in data}}


def set_conf(key, value):
    data = _read_raw()
    data[key] = value
    _write_raw(data)


def get_daemon():
    return _read_raw().get("daemon")


def set_daemon(rec):
    data = _read_raw()
    data["daemon"] = rec
    _write_raw(data)


def clear_daemon():
    data = _read_raw()
    data.pop("daemon", None)
    _write_raw(data)


def reset_conf():
    """No conf file means defaults."""
    try:
        os.remove(CONF_FILE)
    except FileNotFoundError:
        pass
