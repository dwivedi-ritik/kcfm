"""Discover live Claude Code sessions from ~/.claude/sessions/<pid>.json."""

import json
import os
import re
import subprocess
import time

from .config import PROJECTS_DIR, SESSIONS_DIR, START_TOLERANCE


def sh(args):
    try:
        return subprocess.run(args, capture_output=True, text=True).stdout
    except OSError:
        return ""


def proc_start_epoch(pid):
    out = sh(["ps", "-o", "lstart=", "-p", str(pid)]).strip()
    if not out:
        return None
    try:
        # lstart is local time, startedAt is UTC epoch ms — compare as epochs
        return time.mktime(time.strptime(out, "%a %b %d %H:%M:%S %Y"))
    except ValueError:
        return None


def is_claude(pid, started_at_ms):
    """Guard against pid reuse: right name AND right start time."""
    comm = sh(["ps", "-o", "comm=", "-p", str(pid)]).strip()
    if os.path.basename(comm) not in ("claude", "node"):
        return False
    start = proc_start_epoch(pid)
    return start is not None and abs(start - started_at_ms / 1000) < START_TOLERANCE


def proc_rss_mb(pid):
    out = sh(["ps", "-o", "rss=", "-p", str(pid)]).strip()
    return int(out) // 1024 if out.isdigit() else 0


def has_children(pid):
    """A live child process means a tool call is running — treat as busy."""
    return bool(sh(["pgrep", "-P", str(pid)]).strip())


def transcript_path(cwd, session_id):
    # Claude encodes the project cwd with every non-alphanumeric char as '-'
    enc = re.sub(r"[^A-Za-z0-9-]", "-", cwd)
    return os.path.join(PROJECTS_DIR, enc, session_id + ".jsonl")


def live_sessions():
    """Sessions with a verified live claude process behind them."""
    sessions = []
    try:
        files = os.listdir(SESSIONS_DIR)
    except OSError:
        return sessions
    for fname in files:
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(SESSIONS_DIR, fname)) as f:
                info = json.load(f)
        except (OSError, ValueError):
            continue
        pid, sid = info.get("pid"), info.get("sessionId")
        if not pid or not sid or not is_claude(pid, info.get("startedAt", 0)):
            continue
        tpath = transcript_path(info.get("cwd", ""), sid)
        try:
            st = os.stat(tpath)
            tsize, tmtime = st.st_size, st.st_mtime
        except OSError:
            tsize, tmtime = None, None  # no transcript yet -> not resumable
        sessions.append({
            "pid": pid,
            "sid": sid,
            "name": info.get("name", ""),
            "cwd": info.get("cwd", ""),
            "status": info.get("status", "?"),
            "last_activity": max(tmtime or 0, info.get("statusUpdatedAt", 0) / 1000),
            "transcript": tpath,
            "tsize": tsize,
            "tmtime": tmtime,
        })
    return sessions


def resolve(target, live, state):
    """Match name, pid, or sessionId prefix against live and hibernated."""
    live_hits = [s for s in live
                 if target in (s["name"], str(s["pid"])) or s["sid"].startswith(target)]
    hib_hits = {sid: h for sid, h in state["hibernated"].items()
                if target == h.get("name") or sid.startswith(target)}
    return live_hits, hib_hits
