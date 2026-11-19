import dbus,dbus.service,dbus.mainloop.glib,json,os
from gi.repository import GLib
from pathlib import Path
W=Path(os.environ['TRAY_TEST_DIR']);dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus=dbus.SessionBus();name=dbus.service.BusName('org.example.SkynetTrayTest',bus)
mode='normal';stats={'activate':0,'context':0,'layout':0,'event':0,'gets':{}}
def record(): (W/'fake-stats.json').write_text(json.dumps(stats))
def pix():
 if mode=='malformed':return dbus.Array([dbus.Struct((2,2,dbus.ByteArray(b'\xff')))],signature='(iiay)')
 return dbus.Array([dbus.Struct((2,2,dbus.ByteArray(bytes([255,255,0,0,255,0,255,0,255,0,0,255,255,255,255,255]))))],signature='(iiay)')
def props():return {'Id':'skynet-tray-fixture','Title':'SKYNET TEST','IconName':'' if mode in ('pixels','malformed') else 'dialog-information','IconPixmap':pix(),'ToolTip':dbus.Struct(('',dbus.Array([],signature='(iiay)'),'SKYNET TEST','Test tooltip'),signature='sa(iiay)ss'),'Menu':dbus.ObjectPath('/TestMenu')}
class Item(dbus.service.Object):
 @dbus.service.method('org.freedesktop.DBus.Properties',in_signature='s',out_signature='a{sv}')
 def GetAll(self,iface):return props()
 @dbus.service.method('org.freedesktop.DBus.Properties',in_signature='ss',out_signature='v')
 def Get(self,iface,prop):
  stats['gets'][prop]=stats['gets'].get(prop,0)+1;record()
  if prop=='IconThemePath' or (mode=='normal' and prop=='IconPixmap'):
   raise dbus.exceptions.DBusException('error occurred in Get',name='org.freedesktop.DBus.Error.Failed')
  if prop not in props():raise dbus.exceptions.DBusException('Unknown property',name='org.freedesktop.DBus.Error.UnknownProperty')
  return props()[prop]
 @dbus.service.signal('org.kde.StatusNotifierItem',signature='')
 def NewIcon(self):pass
 @dbus.service.signal('org.kde.StatusNotifierItem',signature='')
 def NewToolTip(self):pass
 @dbus.service.method('org.kde.StatusNotifierItem',in_signature='ii',out_signature='')
 def Activate(self,x,y):stats['activate']+=1;record()
 @dbus.service.method('org.kde.StatusNotifierItem',in_signature='ii',out_signature='')
 def ContextMenu(self,x,y):stats['context']+=1;record()
 @dbus.service.method('org.kde.StatusNotifierItem',in_signature='is',out_signature='')
 def Scroll(self,direction,orientation):pass
 @dbus.service.method('org.example.SkynetTrayTest',in_signature='s',out_signature='')
 def Change(self,value):
  global mode
  mode=value
  self.NewIcon();self.NewToolTip()
 @dbus.service.method('org.example.SkynetTrayTest',in_signature='i',out_signature='')
 def Burst(self,n):
  for _ in range(n):self.NewIcon()
 @dbus.service.method('org.example.SkynetTrayTest',in_signature='',out_signature='')
 def Quit(self):GLib.idle_add(loop.quit)
class Menu(dbus.service.Object):
 @dbus.service.method('org.freedesktop.DBus.Properties',in_signature='s',out_signature='a{sv}')
 def GetAll(self,iface):return {'Version':dbus.UInt32(3),'TextDirection':'ltr','Status':'normal','IconThemePath':dbus.Array([],signature='s')}
 @dbus.service.method('org.freedesktop.DBus.Properties',in_signature='ss',out_signature='v')
 def Get(self,iface,p):return self.GetAll(iface)[p]
 @dbus.service.method('com.canonical.dbusmenu',in_signature='iias',out_signature='u(ia{sv}av)')
 def GetLayout(self,parent,depth,properties):
  stats['layout']+=1;record()
  child=dbus.Struct((1,dbus.Dictionary({'label':'Test action','enabled':True,'visible':True},signature='sv'),dbus.Array([],signature='v')),signature='ia{sv}av',variant_level=1)
  return dbus.UInt32(1),(0,dbus.Dictionary({'children-display':'submenu'},signature='sv'),dbus.Array([child],signature='v'))
 @dbus.service.method('com.canonical.dbusmenu',in_signature='i',out_signature='b')
 def AboutToShow(self,item):return False
 @dbus.service.method('com.canonical.dbusmenu',in_signature='isvu',out_signature='')
 def Event(self,item,event,data,timestamp):
  if event=='clicked':stats['event']+=1;record()
 @dbus.service.method('com.canonical.dbusmenu',in_signature='a(isvu)',out_signature='ai')
 def EventGroup(self,events):
  for item,event,data,timestamp in events:
   if event=='clicked':stats['event']+=1
  record();return []
 @dbus.service.method('com.canonical.dbusmenu',in_signature='aias',out_signature='a(ia{sv})')
 def GetGroupProperties(self,ids,properties):return [(i,{'children-display':'submenu'} if i==0 else {'label':'Test action','enabled':True,'visible':True}) for i in ids]
item=Item(bus,'/StatusNotifierItem');menu=Menu(bus,'/TestMenu');record()
watcher=dbus.Interface(bus.get_object('org.kde.StatusNotifierWatcher','/StatusNotifierWatcher'),'org.kde.StatusNotifierWatcher')
watcher.RegisterStatusNotifierItem('org.example.SkynetTrayTest')
loop=GLib.MainLoop();loop.run()
