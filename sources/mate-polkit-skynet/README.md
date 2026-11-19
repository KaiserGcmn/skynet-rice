# MATE Polkit agent with optional desktop-session registration

Source: Debian `mate-polkit_1.26.1-4`, upstream MATE 1.26.1. License: COPYING.
The authentication listener, authenticator and dialog sources are unchanged.
`session-optional.patch` changes only optional GNOME/MATE session registration:

- Do not auto-start a desktop session manager.
- Check whether its D-Bus name has an owner before registering.
- Pass an empty startup identifier when the environment variable is absent.

The system Polkit authority, elogind session, authorization rules, password
checks, temporary-authorization revocation and PAM are unchanged. A missing
desktop session manager is normal under dwm; authority failures still fail.

Build with GTK 3, GLib and Polkit development headers using `make`. Install to
`/usr/local/libexec/polkit-mate-authentication-agent-1`; keep the distribution
agent at `/usr/libexec/` as fallback. Desktop autostart selects the local agent
when present. Run only one authentication agent per login session.
