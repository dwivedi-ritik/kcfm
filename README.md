#### kcfm (kill-claude-for-memory)

I built this out of frustration: I found Claude Code tabs eating 2GB of memory even the ones sitting completely idle.(I use to run GTA Vice city in this much of ram.)
**kc** kills those idle sessions to reclaim the memory. It uses a mark-and-sweep approach - a session that goes quiet is marked, and if it's still quiet after a grace period, it's swept (killed).
and importantly you can resume the killed session whenever needed.

## Install

```
./install.sh
```

Needs only `python3`. Installs a global `kc` command. Do not any third party libs.

## Usage

```
kc ls                     # list sessions with state and memory freed
kc sleep abc23            # free a session's memory now
kc wake 7c34              # resume it, full history intact
kc auto                   # one auto-sleep pass (--dry-run to preview)
kc start                  # start the background watcher
kc status                 # is the watcher running?
kc stop                   # stop the watcher
kc run                    # watch in the foreground (what start runs)
```

Targets can be a session name (`7c34`), pid, or sessionId prefix like docker.

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
