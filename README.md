# ccbear 🐻

Hibernate idle Claude Code sessions to free memory (~300MB each). Wake them
later with full conversation history — nothing is lost, because Claude Code
keeps every conversation in an on-disk transcript.

Zero dependencies (Python 3 stdlib). No daemon, no hooks, no wrapper — ccbear
passively reads the session registry Claude Code itself maintains at
`~/.claude/sessions/`, so it sees every session no matter how it was started.

## Usage

```
ccbear ps                     # list sessions: live, busy, marked, frozen
ccbear hibernate misc-7c      # freeze a session (snapshot, then SIGTERM)
ccbear wake misc-7c           # resume it right here, full history intact
ccbear tag misc-7c auth pin   # tag it; the "pin" tag exempts it from auto
ccbear hibernate @auth        # freeze everything tagged "auth"
ccbear auto                   # one mark-and-sweep pass (--dry-run to preview)
ccbear run                    # watch on a loop, sweeping as sessions go idle
```

Targets can be a session name (`misc-7c`), pid, sessionId prefix, or `@tag`.

## Config

Stored in `~/.ccbear.conf.json`; missing file or keys fall back to defaults.
Changes apply live to a running `ccbear run`.

```
ccbear --set-mark-time 300    # idle seconds before a session is marked (default 600)
ccbear --set-sweep-time 120   # seconds from mark to freeze (default 300)
ccbear --reset-config         # back to defaults
```

## How auto works (mark and sweep)

1. **Mark** — a session idle ≥ 10 min (no transcript growth, claude idle,
   no running tool) becomes a candidate.
2. **Reprieve** — any activity during the next 5 min cancels the mark.
3. **Sweep** — still quiet after the grace period → snapshot + SIGTERM.
   Resume anytime with `ccbear wake` (or `claude --resume <sessionId>`).

Sessions tagged `pin` are never auto-hibernated.

## State

`~/.ccbear.json` holds tags, hibernation snapshots, and sweep marks;
`~/.ccbear.conf.json` holds your settings.
Delete it and ccbear forgets its bookkeeping; your conversations are unaffected
(they live in `~/.claude/projects/`).

## Install

```
chmod +x ccbear.py
ln -s "$PWD/ccbear.py" ~/bin/ccbear   # or anywhere on your PATH
```
