import argparse
import os
import subprocess
import sys
import time

from . import daemon
from . import log
from . import state as state_mod
from .actions import sleep_one, wake
from .config import CONF_FILE, DEFAULTS, LOG_FILE, load_conf, reset_conf, set_conf
from .policy import auto_pass, fmt_dur
from .sessions import has_children, live_sessions, proc_rss_mb, resolve

# standard ANSI colors, applied only when writing to a real terminal
GREEN, YELLOW, CYAN, DIM = "32", "33", "36", "2"


def _color(text, code):
    if not code or not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def _state_color(state):
    return {"IDLE": GREEN, "BUSY": CYAN, "FROZEN": DIM}.get(state)


def _sweep_color(sweep):
    if sweep.startswith("marked"):
        return YELLOW
    if sweep.startswith("freed"):
        return CYAN
    return None


def cmd_ls(args):
    state = state_mod.load()
    cfg = load_conf()
    live = live_sessions()
    state_mod.reconcile(state, live)
    home = os.path.expanduser("~")
    rows = []
    for s in sorted(live, key=lambda s: s["last_activity"], reverse=True):
        mark = state["marks"].get(s["sid"])
        busy = s["status"] == "busy" or has_children(s["pid"])
        if mark:
            left = cfg["sweep_time"] - (time.time() - mark["markedAt"])
            sweep = f"marked, {fmt_dur(left)} left"
        else:
            sweep = "-"
        rows.append((s["name"], "BUSY" if busy else "IDLE", sweep,
                     fmt_dur(time.time() - s["last_activity"]),
                     f"{proc_rss_mb(s['pid'])}M",
                     s["sid"][:8], s["cwd"].replace(home, "~")))
    for sid, h in state["hibernated"].items():
        freed = f"freed ~{h['freedMb']}M" if h.get("freedMb") else "freed"
        rows.append((h.get("name", ""), "FROZEN", freed,
                     fmt_dur(time.time() - h.get("frozenAt", 0)), "-",
                     sid[:8], h.get("cwd", "").replace(home, "~")))
    if not rows:
        print("no sessions")
        return
    headers = ("NAME", "STATE", "SWEEP", "IDLE", "MEM", "SESSION", "CWD")
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip())
    for row in rows:
        # color STATE and SWEEP after padding, so column widths stay aligned
        cells = [c.ljust(w) for c, w in zip(row, widths)]
        cells[1] = _color(cells[1], _state_color(row[1]))
        cells[2] = _color(cells[2], _sweep_color(row[2]))
        print("  ".join(cells).rstrip())


def cmd_sleep(args):
    state = state_mod.load()
    live = live_sessions()
    for target in args.target:
        hits, _ = resolve(target, live, state)
        if not hits:
            print(f"no live session matches '{target}'")
            continue
        for s in hits:
            sleep_one(s, state)


def cmd_wake(args):
    state = state_mod.load()
    wake(args.target, state, live_sessions())


def cmd_config(args):
    cfg = load_conf()
    print(f"mark_time   {cfg['mark_time']}s   (idle before a session is marked)")
    print(f"sweep_time  {cfg['sweep_time']}s   (from mark to sleep)")
    print(f"interval    {cfg['interval']}s   (between watcher passes)")


def cmd_run(args):
    sys.stdout.reconfigure(line_buffering=True)  # visible when piped to a log
    cfg = load_conf()
    interval = args.interval or cfg["interval"]
    log.event("WATCH", f"mark {fmt_dur(cfg['mark_time'])} / "
              f"sweep {fmt_dur(cfg['sweep_time'])} / every {fmt_dur(interval)}")
    while True:
        try:
            auto_pass(state_mod.load())
            time.sleep(interval)
        except KeyboardInterrupt:
            return


def cmd_log(args):
    if not daemon.is_running():
        print("not running")
        return
    try:
        subprocess.run(["tail", "-f", LOG_FILE])
    except KeyboardInterrupt:
        pass


def handle_config_flags(args):
    """Returns True if any config operation ran (CLI exits after)."""
    ran = False
    if args.reset_config:
        pid = daemon.stop_running()
        if pid:
            print(f"stopped background watcher (pid {pid})")
        reset_conf()
        print("config reset to defaults: " + ", ".join(
            f"{k}={v}s" for k, v in DEFAULTS.items()))
        ran = True
    for key, value in (("mark_time", args.set_mark_time),
                       ("sweep_time", args.set_sweep_time)):
        if value is None:
            continue
        if value <= 0:
            print(f"{key} must be a positive number of seconds")
            raise SystemExit(1)
        set_conf(key, value)
        print(f"{key} = {value}s (saved to {CONF_FILE})")
        ran = True
    return ran


def main():
    p = argparse.ArgumentParser(
        prog="kc",
        description="Hibernate idle Claude Code sessions to free memory; "
                    "wake them later with full history.")
    p.add_argument("--set-mark-time", type=int, metavar="SECS",
                   help="idle seconds before a session is marked")
    p.add_argument("--set-sweep-time", type=int, metavar="SECS",
                   help="seconds after marking before it is frozen")
    p.add_argument("--reset-config", action="store_true",
                   help="reset config to defaults")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("ls", help="list sessions").set_defaults(fn=cmd_ls)
    sub.add_parser("config", help="show current settings").set_defaults(fn=cmd_config)

    sp = sub.add_parser("sleep", help="sleep session(s) to free memory")
    sp.add_argument("target", nargs="+",
                    help="session name, pid, or sessionId prefix")
    sp.set_defaults(fn=cmd_sleep)

    sp = sub.add_parser("wake", help="resume a sleeping session here")
    sp.add_argument("target")
    sp.set_defaults(fn=cmd_wake)

    sp = sub.add_parser("run", help="watch sessions in the foreground")
    sp.add_argument("--interval", type=int, metavar="SECS",
                    help="seconds between passes (default from config)")
    sp.set_defaults(fn=cmd_run)

    sub.add_parser("start", help="start the background watcher"
                   ).set_defaults(fn=lambda a: daemon.start())
    sub.add_parser("stop", help="stop the background watcher"
                   ).set_defaults(fn=lambda a: daemon.stop())
    sub.add_parser("status", help="is the background watcher running?"
                   ).set_defaults(fn=lambda a: daemon.status())
    sub.add_parser("log", help="tail the watcher's log").set_defaults(fn=cmd_log)

    args = p.parse_args()
    if handle_config_flags(args):
        return
    if not args.cmd:
        p.print_help()
        raise SystemExit(1)
    args.fn(args)
