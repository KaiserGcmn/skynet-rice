import ctypes as C,os,subprocess as S,time,secrets,signal,json,sys,tempfile,shutil
from pathlib import Path
from PIL import Image
FIXTURE=Path(__file__).with_name('snixembed_item.py')
CANDIDATE=Path(sys.argv[1]).resolve()
BASELINE=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else None
W=Path(tempfile.mkdtemp(prefix='skynet-tray-test-'));X=C.CDLL('libX11.so.6');P=C.c_void_p;U=C.c_ulong;I=C.c_int
for n,r,a in [('XOpenDisplay',P,[C.c_char_p]),('XDefaultRootWindow',U,[P]),('XCreateSimpleWindow',U,[P,U,I,I,C.c_uint,C.c_uint,C.c_uint,U,U]),('XSync',I,[P,I]),('XDestroyWindow',I,[P,U]),('XCloseDisplay',I,[P]),('XGetImage',P,[P,U,I,I,C.c_uint,C.c_uint,U,I]),('XDestroyImage',I,[P])]:
 f=getattr(X,n);f.restype=r;f.argtypes=a
class XImage(C.Structure):
 _fields_=[('width',I),('height',I),('xoffset',I),('format',I),('data',P),('byte_order',I),('bitmap_unit',I),('bitmap_bit_order',I),('bitmap_pad',I),('depth',I),('bytes_per_line',I),('bits_per_pixel',I)]
E=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
for f in Path('/proc').glob('[0-9]*/comm'):
 try:
  if f.read_text().strip()=='dwm':
   for item in (f.parent/'environ').read_bytes().split(b'\0'):
    k,_,v=item.partition(b'=')
    if k in (b'DISPLAY',b'XAUTHORITY'):E[k.decode()]=v.decode()
   break
 except OSError:pass
assert not Path('/tmp/.X11-unix/X195').exists()
host=X.XOpenDisplay(E['DISPLAY'].encode());assert host
parent=X.XCreateSimpleWindow(host,X.XDefaultRootWindow(host),0,0,1000,700,0,0,0);X.XSync(host,0)
auth=W/'xauth';auth.touch(mode=0o600);S.run(['xauth','-f',str(auth),'add',':195','.',secrets.token_hex(16)],check=True)
home=W/'test-home';(home/'.local/share/dwm').mkdir(parents=True,exist_ok=True)
runtime=W/'runtime';runtime.mkdir(mode=0o700,exist_ok=True)
T=dict(E,DISPLAY=':195',XAUTHORITY=str(auth),HOME=str(home),XDG_DATA_HOME=str(home/'.local/share'),XDG_RUNTIME_DIR=str(runtime),NO_AT_BRIDGE='1',TRAY_TEST_DIR=str(W))
processes=[];logs=[];buspid=None;d=None

def spawn(cmd,env,name):
 log=(W/(name+'.log')).open('w');logs.append(log)
 p=S.Popen(cmd,env=env,stdin=S.DEVNULL,stdout=log,stderr=log,start_new_session=True);processes.append(p);return p

def until(fn,timeout=5):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if fn():return
  time.sleep(.05)
 raise RuntimeError('Timed out')
def run(*cmd):return S.run(cmd,env=T,capture_output=True,text=True,check=True,timeout=5)
def call(method,*args):return run('gdbus','call','--session','--dest','org.example.SkynetTrayTest','--object-path','/StatusNotifierItem','--method','org.example.SkynetTrayTest.'+method,*map(str,args))
def stats():return json.loads((W/'fake-stats.json').read_text())
def stop(p):
 if p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=3)
  except S.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def shot(name):
 img=X.XGetImage(d,X.XDefaultRootWindow(d),0,0,1000,700,U(-1),2);assert img
 im=C.cast(img,C.POINTER(XImage)).contents
 Image.frombytes('RGB',(im.width,im.height),C.string_at(im.data,im.bytes_per_line*im.height),'raw','BGRX',im.bytes_per_line).save(W/name);X.XDestroyImage(img)
try:
 spawn(['/usr/bin/Xephyr',':195','-parent',str(parent),'-screen','1000x700','-nolisten','tcp','-auth',str(auth)],E,'xephyr')
 until(lambda:S.run(['xdpyinfo'],env=T,stdout=S.DEVNULL,stderr=S.DEVNULL).returncode==0)
 # XOpenDisplay uses the calling process XAUTHORITY.
 os.environ['XAUTHORITY']=str(auth);d=X.XOpenDisplay(b':195');assert d
 bus=S.check_output(['dbus-daemon','--session','--fork','--print-address=1','--print-pid=1'],env=T,text=True).splitlines();T['DBUS_SESSION_BUS_ADDRESS']=bus[0];buspid=int(bus[1])
 spawn(['/usr/local/bin/dwm'],T,'dwm');time.sleep(.5)
 results={}
 for label in (['baseline'] if BASELINE else []) + ['snixembed']:
  bridge=spawn([str(BASELINE if label=='baseline' else CANDIDATE)],T,label);time.sleep(.4)
  fake=spawn(['/usr/bin/python3',str(FIXTURE)],T,label+'-fake');time.sleep(.7)
  assert bridge.poll() is None and fake.poll() is None
  for _ in range(3):call('Burst',10);time.sleep(.2)
  time.sleep(.5);shot(label+'-icon.png')
  if label=='snixembed':
   run('xdotool','mousemove','988','14','click','1');until(lambda:stats()['activate']>=1)
   run('xdotool','click','3');time.sleep(.8);shot('menu.png');assert stats()['layout']>=1
   tree=run('xwininfo','-root','-tree').stdout;(W/'tree.txt').write_text(tree)
   run('xdotool','mousemove','920','31','click','1');until(lambda:stats()['event']>=1)
   for mode in ['pixels','malformed','pixels','normal']:call('Change',mode);time.sleep(.25);assert bridge.poll() is None
   # A valid pixel update after a malformed one must still render.
   call('Change','pixels');time.sleep(.3);shot('pixels.png')
   call('Change','normal');time.sleep(.2)
   results['menu_action']=stats()['event'];results['click_activation']=stats()['activate'];results['menu_layouts']=stats()['layout'];results['property_calls']=stats()['gets']
   # Actually release the bus name and restart the fixture: duplicate
   # registration alone is ignored by the watcher and cannot test XEmbed.
   for cycle in range(30):
    call('Quit');fake.wait(timeout=3);time.sleep(.1)
    fake=spawn(['/usr/bin/python3',str(FIXTURE)],T,'restart-'+str(cycle));time.sleep(.25)
    call('Burst',1);assert bridge.poll() is None and fake.poll() is None
   time.sleep(.4)
   run('xdotool','mousemove','988','14','click','1');until(lambda:stats()['activate']>=1)
   results['replacement_cycles']=30
  call('Quit');fake.wait(timeout=3);time.sleep(.4);assert bridge.poll() is None
  stop(bridge)
  log=(W/(label+'.log')).read_text();results[label]={'critical':log.count('CRITICAL'),'warnings':log.count('WARNING'),'uncaught':log.count('uncaught error'),'log':log[-600:],'diagnostics':[line for line in log.splitlines() if any(tag in line for tag in ['CRITICAL','WARNING'])][:4]}
 assert results['snixembed']['critical']==0 and results['snixembed']['warnings']==0 and results['snixembed']['uncaught']==0, results
 if BASELINE:assert results['baseline']['uncaught']>0
 print(json.dumps(results),flush=True)
finally:
 if d:X.XCloseDisplay(d)
 for p in reversed(processes):stop(p)
 if buspid:
  try:os.kill(buspid,signal.SIGTERM)
  except ProcessLookupError:pass
 for l in logs:l.close()
 X.XDestroyWindow(host,parent);X.XSync(host,0);X.XCloseDisplay(host)

 shutil.rmtree(W)
