#!/usr/bin/python3
"""Build a stock control and the reviewed MTL016 backport; never install/load."""
import difflib
import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import tarfile
import argparse

os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
RECIPE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('workdir', type=Path)
BASE = parser.parse_args().workdir.resolve()
assert BASE.is_dir()
KERNEL = '6.12.115+deb13.1-amd64'
VERSION = '0.6-skynet-mtl016-deb13-115'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def run(*args, cwd=BASE):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
    return p.stdout + p.stderr

package = BASE/'linux-source-6.12_6.12.115-2_all.deb'
assert sha(package) == 'dd4eb9248eb941e769688d847d5046ab7d05d3608e156ec07da0863a3230f03c'
print('Debian package SHA256 verified.', flush=True)
extracted = BASE/'source-package'
run('dpkg-deb', '-x', str(package), str(extracted))
with tarfile.open(extracted/'usr/src/linux-source-6.12.tar.xz') as archive:
    source = archive.extractfile('linux-source-6.12/drivers/pci/controller/vmd.c').read()
pristine = BASE/'pristine'; pristine.mkdir(exist_ok=True)
(pristine/'vmd.c').write_bytes(source)
stock = BASE/'build-stock'; patched = BASE/'build-patched'
for directory in (stock, patched):
    directory.mkdir(exist_ok=True)
    (directory/'vmd.c').write_bytes(source)
    (directory/'Makefile').write_text('obj-m := vmd.o\n')
patch = (RECIPE/'backport.patch').read_text().replace('0.6-mtl016-b437504-deb13-113', VERSION)
(BASE/'backport.patch').write_text(patch)
output = run('patch', '--batch', '--fuzz=0', '-p1', '-i', str(BASE/'backport.patch'), cwd=patched)
assert 'fuzz' not in output and 'FAILED' not in output
(BASE/'patch.log').write_text(output)
(BASE/'source.diff').write_text(''.join(difflib.unified_diff(source.decode().splitlines(True),
    (patched/'vmd.c').read_text().splitlines(True), fromfile='Debian/vmd.c', tofile='MTL016/vmd.c')))
for directory in (stock, patched):
    print('Building ' + directory.name + ' against ' + KERNEL, flush=True)
    (BASE/(directory.name+'.log')).write_text(run('make','-C','/lib/modules/'+KERNEL+'/build',
        'M='+str(directory), '-j2', 'W=1', 'modules'))
official = pristine/'vmd-debian.ko'
official.write_bytes(lzma.decompress(Path('/lib/modules') .joinpath(KERNEL,'kernel/drivers/pci/controller/vmd.ko.xz').read_bytes()))
modules = {'debian':official, 'rebuilt_stock':stock/'vmd.ko', 'patched':patched/'vmd.ko'}
results = {}
for name, module in modules.items():
    text = BASE/(name+'-text.bin')
    run('objcopy','-O','binary','--only-section=.text',str(module),str(text))
    versions = run('modprobe','--show-modversions',str(module))
    (BASE/(name+'-versions.txt')).write_text(versions)
    results[name] = {'sha256':sha(module), 'text_sha256':sha(text),
        **{field:run('modinfo','-F',field,str(module)).strip() for field in ('vermagic','version','depends','alias')},
        'symbols':{line.split()[1]:line.split()[0] for line in versions.splitlines()}}
assert results['debian']['text_sha256'] == results['rebuilt_stock']['text_sha256'], 'Stock executable text differs'
assert results['patched']['vermagic'] == results['debian']['vermagic']
assert results['patched']['version'] == VERSION
assert results['patched']['alias'] == results['debian']['alias']
assert results['patched']['depends'] == results['debian']['depends']
headers = Path('/lib/modules')/KERNEL/'build/Module.symvers'
available = {line.split()[1]:line.split()[0] for line in headers.read_text().splitlines()}
for symbol, crc in results['patched']['symbols'].items():
    assert available[symbol] == crc, (symbol, 'CRC mismatch')
for symbol, crc in results['debian']['symbols'].items():
    assert results['patched']['symbols'].get(symbol) == crc, (symbol, 'Stock symbol differs')
results.update(stock_text_reproduced=True, all_imported_symbols_match_kernel=True,
    new_imported_symbols=sorted(set(results['patched']['symbols'])-set(results['debian']['symbols'])),
    kernel=KERNEL, source_package_sha256=sha(package), source_sha256=sha(pristine/'vmd.c'),
    patched_source_sha256=sha(patched/'vmd.c'), patch_sha256=sha(BASE/'backport.patch'),
    upstream_discussion='https://lists.openwall.net/linux-kernel/2026/10/05/2042', installed=False, runtime_tested=False)
(BASE/'build-verification.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k:v for k,v in results.items() if k not in modules},indent=2),flush=True)
