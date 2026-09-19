# ccbear 🐻

Hibernate idle Claude Code sessions to free memory (~300MB each), and wake
them later with full conversation history intact.

- **Frees memory automatically** — idle sessions are hibernated on a timer
- **Wakes instantly** — resume any hibernated session right where you left off
- **Sees every session** — no wrapper or setup; start `claude` however you like
- **Tags** — label and act on groups of sessions; `pin` protects one from auto
- **Configurable timing** — set how long idle before hibernating
- **Lightweight** — a plain CLI, zero dependencies, no background daemon

## Install

```
./install.sh
```

Requires [uv](https://docs.astral.sh/uv/). Installs a global `ccbear` command.

## Usage

```
ccbear ls                     # list sessions with state and memory freed
ccbear hibernate misc-7c      # free a session's memory now
ccbear wake misc-7c           # resume it, full history intact
ccbear tag misc-7c auth pin   # tag it; the "pin" tag exempts it from auto
ccbear hibernate @auth        # hibernate everything tagged "auth"
ccbear auto                   # one auto-hibernate pass (--dry-run to preview)
ccbear start                  # start the background watcher
ccbear status                 # is the watcher running?
ccbear stop                   # stop the watcher
ccbear run                    # watch in the foreground (what start runs)
```

Targets can be a session name (`misc-7c`), pid, sessionId prefix, or `@tag`.

## Config

```
ccbear --set-mark-time 300    # idle seconds before a session is marked (default 600)
ccbear --set-sweep-time 120   # seconds from mark to hibernate (default 300)
ccbear --reset-config         # back to defaults
```

Stored in `~/.ccbear.conf.json`; changes apply live to a running watcher.
`--reset-config` also stops the background watcher.
A marked session is reprieved if it becomes active before the sweep time; a
session tagged `pin` is never auto-hibernated.

Your conversations are never at risk — ccbear only frees memory; the history
lives in Claude Code's own transcripts.
