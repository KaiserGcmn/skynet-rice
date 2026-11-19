PKG = gtk+-3.0 gio-2.0 Dbusmenu-0.4 DbusmenuGtk3-0.4
CPKG = dbusmenu-gtk3-0.4
SRC = src/*.vala version.vala

PREFIX ?= /usr
BINDIR ?= /bin
MANDIR ?= /share/man

PKG := $(foreach pkg, $(PKG), --pkg $(pkg))
CFLAGS := $(CFLAGS) $(shell pkg-config --cflags --libs $(CPKG))
VFLAGS := $(foreach flag, $(CPPFLAGS) $(CFLAGS) $(LDFLAGS), -X $(flag)) $(VFLAGS)

snixembed: $(SRC)
	valac -o $@ $(VFLAGS) $(PKG) $(SRC)

version.vala: # update version from git if possible
ifneq (,$(wildcard ./.git/HEAD))
	echo "const string VERSION = \"$(shell git describe --always --tags --dirty)\";" > $@
endif

doc: $(SRC)
	valadoc --force -o $@ --internal --private --package-name snixembed $(SRC) $(PKG)

clean:
	rm -rf src/*.c version.vala snixembed doc

install: snixembed
	install -Dm755 snixembed $(DESTDIR)$(PREFIX)$(BINDIR)/snixembed
	install -Dm644 snixembed.1 $(DESTDIR)$(PREFIX)$(MANDIR)/man1/snixembed.1

uninstall:
	rm -f $(DESTDIR)$(PREFIX)$(BINDIR)/snixembed \
		$(DESTDIR)$(PREFIX)$(MANDIR)/man1/snixembed.1

.PHONY: clean install uninstall version.vala
