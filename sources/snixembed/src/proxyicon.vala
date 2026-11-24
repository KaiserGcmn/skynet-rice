class ProxyIcon : Object {
    StatusNotifierItem item;
    Gtk.StatusIcon icon;
    DbusmenuGtk.Menu? menu;
    string bus_name;
    bool closed = false;
    Cancellable cancellable = new Cancellable();
    ulong changed_handler;
    ulong icon_handler;
    Gdk.Event? pending_menu_event;
    uint menu_timeout;

    public ProxyIcon(string name, string object) throws IOError {
        init.begin(name, object);
    }

    async void init(string name, string object) {
        bus_name = name;
        try {
            item = yield Bus.get_proxy(BusType.SESSION, name, object,
                                      DBusProxyFlags.DO_NOT_AUTO_START, cancellable);
        } catch (Error e) {
            if (!closed && !(e is IOError.CANCELLED))
                message("SNI %s%s disappeared during setup: %s", name, object, e.message);
            return;
        }
        if (closed) return;
        // "visible" is not a construct property: setting it to false in
        // Object.new happens AFTER GTK has shown the XEmbed window. Hiding
        // and showing again races the tray's pending reparent events.
        icon = new Gtk.StatusIcon();

        changed_handler = item.changed.connect(property => {
            switch(property) {
            case "tool-tip": set_tooltip(); break;
            }
        });
        icon_handler = item.icon_changed.connect(set_icon);

        icon.set_from_icon_name("image-missing");
        set_icon();
        // set_name() hides/unrealizes/re-shows an already realized GtkPlug.
        // Keep one XEmbed window; a title labels it without that lifecycle race.
        icon.set_title(item.title ?? item.id ?? "Application");
        set_tooltip();

        // Construct the remote menu only when requested. Do not start menu
        // I/O for an icon which may disappear during application startup.
        icon.activate.connect(() => send_action.begin("Activate", new Variant("(ii)", 0, 0))); // TODO: consider smarter coordinate hints
        icon.button_press_event.connect(on_button_press);
        icon.scroll_event.connect(on_scroll);
    }

    bool on_button_press(Gdk.EventButton event) {
        if (event.button == 3) {
            string? path = item.menu;
            if (menu == null && path != null && path != "/" && path != "/NO_DBUSMENU") {
                menu = new DbusmenuGtk.Menu(bus_name, path);
            }
            if (menu != null) {
                pending_menu_event = event.copy();
                if (menu_timeout != 0) Source.remove(menu_timeout);
                int64 deadline = get_monotonic_time() + 2000000;
                menu_timeout = Timeout.add(25, () => {
                    if (closed || get_monotonic_time() >= deadline) {
                        menu_timeout = 0;
                        pending_menu_event = null;
                        return Source.REMOVE;
                    }
                    if (menu != null && menu.get_client().get_root() != null &&
                        menu.get_children().length() > 0) {
                        menu_timeout = 0;
                        show_ready_menu();
                        return Source.REMOVE;
                    }
                    return Source.CONTINUE;
                });
                show_ready_menu();
                return true;
            }

            send_action.begin("ContextMenu", new Variant("(ii)", (int)event.x_root, (int)event.y_root));
            return true;
        }
        return false;
    }

    bool on_scroll(Gdk.EventScroll event) {
        switch(event.direction) {
            case Gdk.ScrollDirection.SMOOTH:
                 // It seems that we can safely ignore this
                 break;
            case Gdk.ScrollDirection.DOWN:
            case Gdk.ScrollDirection.UP:
                 send_action.begin("Scroll", new Variant("(is)", (int)event.delta_y, "vertical"));
                 break;
            case Gdk.ScrollDirection.LEFT:
            case Gdk.ScrollDirection.RIGHT:
                 send_action.begin("Scroll", new Variant("(is)", (int)event.delta_x, "horizontal"));
                 break;
            default: stderr.printf("unsupported scrolling event\n");
                 break;
        }
        return true;
    }

    void show_ready_menu() {
        if (closed || menu == null || pending_menu_event == null ||
            menu.get_client().get_root() == null || menu.get_children().length() == 0) return;
        if (menu_timeout != 0) { Source.remove(menu_timeout); menu_timeout = 0; }
        menu.popup_at_pointer(pending_menu_event);
        pending_menu_event = null;
    }

    async void send_action(string method, Variant args) {
        if (closed) return;
        var proxy = (DBusProxy) item;
        try {
            yield proxy.call(method, args, DBusCallFlags.NO_AUTO_START, 2000, cancellable);
        } catch (Error e) {
            if (!closed && proxy.get_name_owner() != null && !(e is IOError.CANCELLED))
                message("SNI %s: %s failed: %s", bus_name, method, e.message);
        }
    }

    public void close() {
        closed = true;
        cancellable.cancel();
        if (item != null) {
            if (changed_handler != 0) item.disconnect(changed_handler);
            if (icon_handler != 0) item.disconnect(icon_handler);
            changed_handler = icon_handler = 0;
        }
        if (icon != null) icon.visible = false;
        if (menu_timeout != 0) { Source.remove(menu_timeout); menu_timeout = 0; }
        pending_menu_event = null;
        if (menu != null) {
            menu.destroy(); menu = null;
        }
    }

    void set_icon() {
        if (closed || icon == null) return;
        var name = item.icon_name;
        if (name != null && name != "") {
            /* Some apps wrongly set a filename for name, relying on this
             * undefined behavior. Since StatusIcon.set_from_file gives no
             * feedback, this check and race is about the best we can do. */
            if (name.contains("/") && FileUtils.test(name, FileTest.EXISTS)) {
                icon.set_from_file(name);
                return;
            }

            var theme = Gtk.IconTheme.get_for_screen(icon.screen);
            var path = item.icon_theme_path;
            if (path != null) {
                string[] paths;
                theme.get_search_path(out paths);
                if (!(path in paths)) {
                    theme.append_search_path(path);
                }
            }
            if (!theme.rescan_if_needed() && !theme.has_icon(name)) {
                /* Forcibly trigger a rescan in case the icon file was added
                 * after the theme has been scanned (new files don't change
                 * mtime if they're in a subdirectory). */
                string[] paths;
                theme.get_search_path(out paths);
                theme.set_search_path(paths);
            }

            set_icon_name(name);
            if (theme.has_icon(name)) {
                return;
            }
        }

        var pixmaps = item.icon_pixmap;
        if (pixmaps != null) {
            set_icon_pixmap(pixmaps);
        }
    }

    void set_icon_name(string name) {
        icon.set_from_icon_name(name);
    }

    void set_icon_pixmap(IconPixmap[] pixmaps) {
        if (pixmaps.length == 0) return;

        var pixmap = pixmaps[0];
        // Validate before calculating strides; never mutate the D-Bus cache.
        if (pixmap.width < 1 || pixmap.height < 1 ||
            pixmap.width > 1024 || pixmap.height > 1024 ||
            pixmap.data.length != pixmap.width * pixmap.height * 4) return;
        uint8[] rgba = new uint8[pixmap.data.length];
        for (int i = 0; i < rgba.length; i += 4) {
            rgba[i] = pixmap.data[i + 1];
            rgba[i + 1] = pixmap.data[i + 2];
            rgba[i + 2] = pixmap.data[i + 3];
            rgba[i + 3] = pixmap.data[i];
        }
        var pixbuf = new Gdk.Pixbuf.from_data(rgba, Gdk.Colorspace.RGB,
                true, 8, pixmap.width, pixmap.height, pixmap.width * 4);
        icon.set_from_pixbuf(pixbuf);
    }

    void set_tooltip() {
        if (closed || icon == null) return;
        var tooltip = item.tool_tip;
        string title = tooltip.title;
        string text = tooltip.text;

        if (text != null && text != "") {
            title += @"\n$(tooltip.text)";
        }
        icon.set_tooltip_markup(title);
    }
}
