import argparse
import os
import sys
import time

from . import state as state_mod
from .actions import edit_tags, hibernate_one, wake
from .config import CONF_FILE, DEFAULTS, load_conf, reset_conf, set_conf
from .policy import auto_pass, fmt_dur
from .sessions import has_children, live_sessions, proc_rss_mb, resolve


def cmd_ps(args):
    state = state_mod.load()
    cfg = load_conf()
    live = live_sessions(state)
    state_mod.reconcile(state, live)
    home = os.path.expanduser("~")
    rows = []
    for s in sorted(live, key=lambda s: s["last_activity"], reverse=True):
        mark = state["marks"].get(s["sid"])
        if s["status"] == "busy" or has_children(s["pid"]):
            st = "busy"
        elif mark:
            left = cfg["sweep_time"] - (time.time() - mark["markedAt"])
            st = f"marked({fmt_dur(left)})"
        else:
            st = "idle"
        rows.append((s["name"], st, fmt_dur(time.time() - s["last_activity"]),
                     f"{proc_rss_mb(s['pid'])}M", ",".join(s["tags"]),
                     s["sid"][:8], s["cwd"].replace(home, "~")))
    for sid, h in state["hibernated"].items():
        rows.append((h.get("name", ""), "frozen",
                     fmt_dur(time.time() - h.get("frozenAt", 0)), "-",
                     ",".join(state["tags"].get(sid, [])), sid[:8],
                     h.get("cwd", "").replace(home, "~")))
    if not rows:
        print("no sessions")
        return
    headers = ("NAME", "STATE", "IDLE", "MEM", "TAGS", "SESSION", "CWD")
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))]
    for row in (headers, *rows):
        print("  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip())


def cmd_hibernate(args):
    state = state_mod.load()
    live = live_sessions(state)
    for target in args.target:
        hits, _ = resolve(target, live, state)
        if not hits:
            print(f"no live session matches '{target}'")
            continue
        for s in hits:
            hibernate_one(s, state, force=args.force)


def cmd_wake(args):
    state = state_mod.load()
    wake(args.target, state, live_sessions(state))


def cmd_tag(args):
    state = state_mod.load()
    edit_tags(args.target, args.tags, state, live_sessions(state), add=True)


def cmd_untag(args):
    state = state_mod.load()
    edit_tags(args.target, args.tags, state, live_sessions(state), add=False)


def cmd_auto(args):
    auto_pass(state_mod.load(), dry=args.dry_run)


def cmd_run(args):
    sys.stdout.reconfigure(line_buffering=True)  # visible when piped to a log
    cfg = load_conf()
    interval = args.interval or cfg["interval"]
    print(f"ccbear watching: mark after {fmt_dur(cfg['mark_time'])} idle, "
          f"sweep {fmt_dur(cfg['sweep_time'])} later, pass every {fmt_dur(interval)}")
    while True:
        try:
            auto_pass(state_mod.load())
            time.sleep(interval)
        except KeyboardInterrupt:
            return


def handle_config_flags(args):
    """Returns True if any config operation ran (CLI exits after)."""
    ran = False
    if args.reset_config:
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
        prog="ccbear",
        description="Hibernate idle Claude Code sessions to free memory; "
                    "wake them later with full history.")
    p.add_argument("--set-mark-time", type=int, metavar="SECS",
                   help="idle seconds before a session is marked")
    p.add_argument("--set-sweep-time", type=int, metavar="SECS",
                   help="seconds after marking before it is frozen")
    p.add_argument("--reset-config", action="store_true",
                   help="reset config to defaults")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("ps", help="list sessions").set_defaults(fn=cmd_ps)

    sp = sub.add_parser("hibernate", help="freeze session(s)")
    sp.add_argument("target", nargs="+",
                    help="session name, pid, sessionId prefix, or @tag")
    sp.add_argument("--force", action="store_true", help="freeze even if busy")
    sp.set_defaults(fn=cmd_hibernate)

    sp = sub.add_parser("wake", help="resume a hibernated session here")
    sp.add_argument("target")
    sp.set_defaults(fn=cmd_wake)

    sp = sub.add_parser("tag", help="add tags to a session")
    sp.add_argument("target")
    sp.add_argument("tags", nargs="+")
    sp.set_defaults(fn=cmd_tag)

    sp = sub.add_parser("untag", help="remove tags from a session")
    sp.add_argument("target")
    sp.add_argument("tags", nargs="+")
    sp.set_defaults(fn=cmd_untag)

    sp = sub.add_parser("auto", help="one mark-and-sweep pass")
    sp.add_argument("--dry-run", action="store_true", help="report, touch nothing")
    sp.set_defaults(fn=cmd_auto)

    sp = sub.add_parser("run", help="watch sessions: mark and sweep on a loop")
    sp.add_argument("--interval", type=int, metavar="SECS",
                    help="seconds between passes (default from config)")
    sp.set_defaults(fn=cmd_run)

    args = p.parse_args()
    if handle_config_flags(args):
        return
    if not args.cmd:
        p.print_help()
        raise SystemExit(1)
    args.fn(args)
