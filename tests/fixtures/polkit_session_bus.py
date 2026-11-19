"""Run a mock desktop session manager on a private dbus-run-session bus."""
import os
import subprocess
import sys
import threading

from gi.repository import Gio, GLib

connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
xml = '''<node><interface name="org.gnome.SessionManager">
<method name="RegisterClient"><arg type="s" direction="in"/>
<arg type="s" direction="in"/><arg type="o" direction="out"/></method>
</interface></node>'''
calls = []


def handle(connection, sender, path, interface, method, parameters, invocation):
    calls.append(parameters.unpack())
    invocation.return_value(GLib.Variant('(o)', ('/org/gnome/SessionManager/Client1',)))


connection.register_object('/org/gnome/SessionManager',
    Gio.DBusNodeInfo.new_for_xml(xml).interfaces[0], handle, None, None)
connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
    'org.freedesktop.DBus', 'RequestName',
    GLib.Variant('(su)', ('org.gnome.SessionManager', 0)), None,
    Gio.DBusCallFlags.NONE, -1, None)
loop = GLib.MainLoop()
thread = threading.Thread(target=loop.run)
thread.start()
try:
    result = subprocess.run([sys.argv[1]], env=os.environ, timeout=10)
    assert result.returncode == 0
    assert calls == [('polkit-mate-authentication-agent-1.desktop',
                      os.environ.get('DESKTOP_AUTOSTART_ID', ''))], calls
finally:
    loop.quit()
    thread.join(timeout=3)
