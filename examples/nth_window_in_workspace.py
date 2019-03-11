#!/usr/bin/env python3

"""
nth_window_in_workspace.py go to workspace name, index of window in there.

Arguments: workspace_name, index, [visible] [to_mode]
If `visible` is the word `"visible"` it will ignore invisible ones. For i.e. stacked
windows, the non-visible one in the stack are.. not visible for this.
(probably you dont want to use "visible"?)

If index is `"cycle"` or `"reverse_cycle"` it either go to the workspace, or cycle
through the windows if already there.

`to_mode` is whether to change to another mode, if "no" it will stay in the same mode.
Defaultly it is "default".(possibly returning to it)

- requires the `xprop` utility (for `window_is_visible`)

Examples in config file: (you'll have to specify `$pydir` too)

mapping: `bindsym r exec "python $pydir/nth_window_in_workspace.py 4  1"`
you'll need a lot of those for different numbers there and keys.

cycle:   `bindsym Mod2+KP_1 exec "python $pydir/nth_window_in_workspace.py 1  cycle`"
"""

from sys import argv
from itertools import cycle
from subprocess import check_output

import i3ipc

def get_windows_on_ws(conn):
    return filter(lambda x: x.window,
                  conn.get_tree().find_focused().workspace().descendents())

def workspace_by_name(conn, workspace):
    return next(filter(lambda ws: ws.name==workspace, conn.get_tree().workspaces()), None)

def window_is_visible(w):
    try:
        xprop = check_output(['xprop', '-id', str(w.window)]).decode()
    except FileNotFoundError:
        raise SystemExit("The `xprop` utility is not found!"
                         " Please install it and retry.")

    return '_NET_WM_STATE_HIDDEN' not in xprop

def pick_from_list(lst, n, alt=None):
    cnt = len(lst)
    return lst[max(0, min(n, cnt-1))] if cnt>0 else alt


def main(workspace_name, get_index, visibility='invisible', to_mode='default', *drek):

    conn = i3ipc.Connection()

    workspace = workspace_by_name(conn, workspace_name)  # Find workspace.
    if workspace == None:
        print("Workspace not found, making it.")
        conn.command("workspace " + workspace_name)

    else:
        windows =  workspace.leaves()  # Find windows in there, filter by visibility if needed.
        if visibility=='visible':
            windows = filter(window_is_visible, windows)
        elif visibility!='invisible':
            print("WARN: currently only support invisible and visible as selectors.")

        if workspace_name != workspace.name:
            conn.command("workspace " + workspace_name)
        elif get_index not in ['cycle', 'cycle_reverse']:
            get_index = int(get_index)  # Pick correct window from there.
            window = pick_from_list(list(windows), get_index)

            if window != None:
                print("Focussing %d" % window.window)
                conn.command('[id="%d"] focus' % window.window)
            else:  # It can happen, if an empty workspace is open?
                conn.command("workspace " + workspace_name)
        else:  # Cycle if in the correct window.
            cycle_windows = cycle(windows if get_index=='cycle' else reversed(windows))

            for i,window in enumerate(cycle_windows):
                if window.focused:
                    conn.command('[id="%d"] focus' % next(cycle_windows).window)
                    break
                elif i > len(windows)+1:
                    print("WTF", "not cyling in right workspace, yet %s == %s" % \
                          (workspace.name, workspace_name))
                    conn.command("workspace " + workspace_name)
                    break
    if to_mode != 'no':
        conn.command("mode " + to_mode)

if __name__ == '__main__':
    main(*argv[1:])
