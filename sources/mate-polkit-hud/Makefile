CC ?= cc
PKG_CONFIG ?= pkg-config
CFLAGS ?= -O2 -g
GTK_CFLAGS := $(shell $(PKG_CONFIG) --cflags gtk+-3.0 gio-2.0)
GTK_LIBS := $(shell $(PKG_CONFIG) --libs gtk+-3.0 gio-2.0)
POLKIT_CFLAGS ?= $(shell $(PKG_CONFIG) --cflags polkit-agent-1 polkit-gobject-1)
POLKIT_LIBS ?= $(shell $(PKG_CONFIG) --libs polkit-agent-1 polkit-gobject-1)
DEFINES = -DHAVE_CONFIG_H -DPOLKIT_AGENT_I_KNOW_API_IS_SUBJECT_TO_CHANGE \
          -DG_LOG_DOMAIN='"polkit-mate-1"' -DDATADIR='"/usr/share/mate-polkit"' \
          -DMATELOCALEDIR='"/usr/share/locale"'
SOURCES = main.c polkitmatelistener.c polkitmateauthenticator.c polkitmateauthenticationdialog.c

all: polkit-mate-authentication-agent-1

polkit-mate-authentication-agent-1: $(SOURCES) $(wildcard *.h)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(DEFINES) $(GTK_CFLAGS) $(POLKIT_CFLAGS) $(SOURCES) $(LDFLAGS) $(GTK_LIBS) $(POLKIT_LIBS) -o $@

clean:
	rm -f polkit-mate-authentication-agent-1

.PHONY: all clean
