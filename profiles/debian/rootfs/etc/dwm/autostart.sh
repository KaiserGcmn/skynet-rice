#!/bin/sh
# Shared dwm startup. Each graphical helper runs once for the current user.
task_uid=$(id -u)
start_once() {
    task_name=$1
    shift
    if command -v "$1" >/dev/null 2>&1 &&
       ! pgrep -u "$task_uid" -x "$task_name" >/dev/null; then
        "$@" &
    fi
}

# Restore the selected GIF, video or image without blocking desktop startup.
if command -v skynet-wallpaper >/dev/null 2>&1; then
    skynet-wallpaper start &
else
    xsetroot -solid '#000000'
fi

start_once dunst dunst
start_once snixembed /usr/local/bin/snixembed
start_once slstatus /usr/local/bin/slstatus
start_once nm-applet nm-applet
start_once blueman-applet blueman-applet
start_once spoofdpi /usr/local/bin/skynet-spoofdpi

# Provide the standard desktop dialog for administrative authentication.
# Prefer the dwm-compatible agent; retain the distribution binary as fallback.
task_agent=/usr/local/libexec/polkit-mate-authentication-agent-1
if [ ! -x "$task_agent" ]; then
    task_agent=/usr/libexec/polkit-mate-authentication-agent-1
fi
if [ ! -x "$task_agent" ]; then
    printf '%s\n' 'dwm autostart: no executable MATE Polkit agent found' >&2
elif ! pgrep -u "$task_uid" -f '^(/usr/local/libexec|/usr/libexec)/polkit-mate-authentication-agent-1([[:space:]]|$)' >/dev/null; then
    "$task_agent" &
fi
