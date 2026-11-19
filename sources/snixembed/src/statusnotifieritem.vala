struct IconPixmap {
    int32 width;
    int32 height;
    uint8[] data;
}

struct ToolTip {
    string icon_title;
    IconPixmap[] icon_pixmap;
    string title;
    string text;
}

// StatusNotifierItem proxy
//
// Do not use the D-Bus signals directly, instead rely on icon_changed for icon changes
// and the property changed signals for the rest (title, tooltip, ...).
//
// TODO: handle race conditions
[DBus (name = "org.kde.StatusNotifierItem")]
interface StatusNotifierItem : Object {
    public const string OBJECT = "/StatusNotifierItem";

    // Properties
    public abstract string id { owned get; }
    public abstract string title { owned get; }
    public abstract string icon_name { owned get; }
    public abstract IconPixmap[] icon_pixmap { owned get; }
    public abstract ToolTip tool_tip { owned get; }
    public abstract ObjectPath menu { owned get; }

    // AppIndicator TODO: split in separate interface
    public abstract string icon_theme_path { owned get; }

    // Methods
    public abstract void activate(int x, int y);
    public abstract void context_menu(int x, int y);
    public abstract void scroll(int delta, string orientation);

    // Signals
    public virtual signal void new_title() {
        update_cache.begin("Title", "title");
    }

    public virtual signal void new_icon() {
        handle_new_icon.begin();
    }

    public signal void icon_changed();

    // Asynchronously update icon data and then emit icon_changed if necessary
    async void handle_new_icon() {
        if (get_data<bool>("icon-refresh-pending")) {
            set_data<bool>("icon-refresh-dirty", true);
            return;
        }
        set_data<bool>("icon-refresh-pending", true);
        var changes = 0;

        var done = 0;
        AsyncReadyCallback handler = (obj, res) => {
            try {
                if (update_cache.end(res)) changes++;
            } finally {
                if (++done == 3) handle_new_icon.callback();
            }
        };
        update_cache.begin("IconName", "icon-name", handler);
        update_cache.begin("IconPixmap", "icon-pixmap", handler);
        update_cache.begin("IconThemePath", "icon-theme-path", handler); // AppIndicator only
        yield;

        set_data<bool>("icon-refresh-pending", false);
        if (changes != 0) icon_changed();
        if (get_data<bool>("icon-refresh-dirty")) {
            set_data<bool>("icon-refresh-dirty", false);
            handle_new_icon.begin();
        }
    }

    public virtual signal void new_tool_tip() {
        update_cache.begin("ToolTip", "tool-tip");
    }

    // Internal cache updates and signalling
    //
    // This looks like the most ugly implementation ever, however:
    // - Vala DBus abstraction is abstract
    // - GObject notify signals doesn't work
    // - g_properties_changed does not get called automatically when the cache is updated
    // - this is simple and just works
    internal abstract signal void changed(string property);

    async bool update_cache(string property, string name) {
        var me = this as DBusProxy;

        var par = new Variant("(ss)", me.get_interface_name(), property);
        try {
            var res = yield me.call("org.freedesktop.DBus.Properties.Get", par, DBusCallFlags.NO_AUTO_START, 2000, null);
            Variant v;
            res.get("(v)", out v);
            me.set_data<string?>("property-error-" + property, null);

            Variant? cached = me.get_cached_property(property);
            if (cached == null || !v.equal(cached)) {
                me.set_cached_property(property, v);
                changed(name);
                return true;
            }
        } catch (DBusError.UNKNOWN_PROPERTY e) {
            // Optional property absent: retain the last usable icon.
        } catch (DBusError.INVALID_ARGS e) {
        } catch (Error e) {
            // Qt/Electron sometimes return Failed for unsupported properties.
            // A disappearing owner/cancelled query is normal during shutdown.
            if (me.get_name_owner() != null && !(e is IOError.CANCELLED)) {
                string key = "property-error-" + property;
                if (me.get_data<string>(key) != e.message) {
                    me.set_data<string>(key, e.message);
                    message("SNI %s%s: %s unavailable; keeping cached icon (%s)",
                            me.get_name(), me.get_object_path(), property, e.message);
                }
            }
        }
        return false;
    }
}
