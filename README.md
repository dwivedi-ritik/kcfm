#### ☠️ kcfm (kill-claude-for-memory)

I built this out of frustration: I found claude code eating 2GB of memory for 6 parellel tabs, A terminal app which is just idle doing nothing seriously ?? i use to play GTA Vice city in this much of memory.

**kc** kills those idle sessions to reclaim the memory. It uses a mark-and-sweep approach - a session that goes quiet is marked, and if it's still quiet after a grace period, it's swept (killed).

You can resume the killed session whenever needed nothing will be lost.

## Install

```
./install.sh
```

Needs only `python3` with 0 dependencies. Installs a global `kc` command.

## Usage

```
kc ls                     # list sessions with state and memory freed
kc sleep abc23            # free a session's memory now
kc wake 7c34              # resume it, full history intact
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

