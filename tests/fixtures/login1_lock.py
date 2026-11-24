"""Private login1 fixture; uses only the explicitly supplied session bus."""
import os
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
DBusGMainLoop(set_as_default=True)
bus=dbus.SessionBus()
name=dbus.service.BusName('org.freedesktop.login1',bus=bus)
class Session(dbus.service.Object):
    def __init__(self):
        super().__init__(name,'/org/freedesktop/login1/session/test')
    @dbus.service.method('org.freedesktop.DBus.Properties',in_signature='s',out_signature='a{sv}')
    def GetAll(self,iface):
        return {'Id':'test','Active':True,'LockedHint':False,'IdleHint':False}
    @dbus.service.method('org.freedesktop.login1.Session',in_signature='b',out_signature='')
    def SetIdleHint(self,value): pass
    @dbus.service.method('org.freedesktop.login1.Session',in_signature='b',out_signature='')
    def SetLockedHint(self,value): pass
    @dbus.service.signal('org.freedesktop.login1.Session',signature='')
    def Lock(self): pass
    @dbus.service.signal('org.freedesktop.login1.Session',signature='')
    def Unlock(self): pass
session=Session()
class Manager(dbus.service.Object):
    def __init__(self):
        super().__init__(name,'/org/freedesktop/login1')
        self.fd=os.open('/dev/null',os.O_RDONLY)
    @dbus.service.method('org.freedesktop.DBus.Properties',in_signature='s',out_signature='a{sv}')
    def GetAll(self,iface): return {}
    @dbus.service.method('org.freedesktop.login1.Manager',in_signature='s',out_signature='o')
    def GetSession(self,id):
        return '/org/freedesktop/login1/session/test'
    @dbus.service.method('org.freedesktop.login1.Manager',in_signature='u',out_signature='o')
    def GetSessionByPID(self,pid): return '/org/freedesktop/login1/session/test'
    @dbus.service.method('org.freedesktop.login1.Manager',in_signature='ssss',out_signature='h')
    def Inhibit(self,what,who,why,mode): return dbus.types.UnixFd(self.fd)
    @dbus.service.method('org.skynet.Test',in_signature='',out_signature='')
    def EmitLock(self):
        session.Lock()
    @dbus.service.method('org.skynet.Test',in_signature='',out_signature='')
    def EmitUnlock(self): session.Unlock()
manager=Manager()
GLib.MainLoop().run()
