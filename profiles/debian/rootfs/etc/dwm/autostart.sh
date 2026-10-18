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

# Restore the last wallpaper selected with feh.
if [ -r "$HOME/.fehbg" ] && command -v feh >/dev/null 2>&1; then
    sh "$HOME/.fehbg" || xsetroot -solid '#000000'
else
    xsetroot -solid '#000000'
fi

start_once dunst dunst
start_once snixembed /usr/local/bin/snixembed
start_once slstatus /usr/local/bin/slstatus
start_once nm-applet nm-applet
start_once blueman-applet blueman-applet
start_once spoofdpi spoofdpi --listen-addr 127.0.0.1:9080 --dns-mode https --dns-https-url https://1.1.1.1/dns-query --dns-qtype ipv4 --dns-cache --https-split-mode first-byte --no-tui --log-level error

# Provide the standard desktop dialog for administrative authentication.
task_agent=/usr/lib/x86_64-linux-gnu/libexec/polkit-kde-authentication-agent-1
if [ -x "$task_agent" ] &&
   ! pgrep -u "$task_uid" -f "^$task_agent([[:space:]]|$)" >/dev/null; then
    "$task_agent" &
fi
