# kc

**kill-claude-for-memory** — sleep idle Claude Code sessions to free memory
(~300MB each), and wake them later with full conversation history intact.

- **Frees memory automatically** — idle sessions are slept on a timer
- **Wakes instantly** — resume any slept session right where you left off
- **Sees every session** — no wrapper or setup; start `claude` however you like
- **Configurable timing** — set how long idle before sleeping
- **Lightweight** — a plain CLI, zero dependencies, no resident daemon

## Install

```
./install.sh
```

Needs only `python3`. Installs a global `kc` command.

## Usage

```
kc ls                     # list sessions with state and memory freed
kc sleep misc-7c          # free a session's memory now
kc wake misc-7c           # resume it, full history intact
kc auto                   # one auto-sleep pass (--dry-run to preview)
kc start                  # start the background watcher
kc status                 # is the watcher running?
kc stop                   # stop the watcher
kc run                    # watch in the foreground (what start runs)
```

Targets can be a session name (`misc-7c`), pid, or sessionId prefix.

## Config

```
kc config                 # show current settings
kc --set-mark-time 300    # idle seconds before a session is marked (default 600)
kc --set-sweep-time 120   # seconds from mark to sleep (default 300)
kc --reset-config         # back to defaults (also stops the watcher)
```

Stored in `~/.kc.conf.json`; changes apply live to a running watcher.
A marked session is reprieved if it becomes active before the sweep time.

Your conversations are never at risk — kc only frees memory; the history
lives in Claude Code's own transcripts.
