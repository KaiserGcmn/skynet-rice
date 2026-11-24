# Rebuild with Debian libgtk-3-dev, libjson-c-dev, build-essential and pkg-config.
CC ?= cc
export DEB_BUILD_MAINT_OPTIONS = hardening=+all
CFLAGS += -std=c11 -Wall -Wextra -Wno-unused-parameter -Wno-missing-braces $(shell dpkg-buildflags --get CFLAGS)
CPPFLAGS += $(shell dpkg-buildflags --get CPPFLAGS) $(shell pkg-config --cflags gtk+-3.0 json-c) -DGETTEXT_PACKAGE='"gtkgreet"' -DLOCALEDIR='"/usr/share/locale"'
LDFLAGS += $(shell dpkg-buildflags --get LDFLAGS)
LDLIBS += $(shell pkg-config --libs gtk+-3.0 json-c) -lm
SOURCES = main.c proto.c config.c actions.c window.c gtkgreet.c
# skynet-hud.h shares the lock screen's HUD (../xsecurelock-style).
gtkgreet-hud: $(SOURCES) $(wildcard *.h) $(wildcard ../xsecurelock-style/cyber-hud.h ../xsecurelock-style/sys-stats.h ../xsecurelock-style/skynet-globe.h ../xsecurelock-style/skynet-globe-land.h)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCES) $(LDFLAGS) $(LDLIBS) -o $@
clean:
	rm -f gtkgreet-hud
.PHONY: clean
