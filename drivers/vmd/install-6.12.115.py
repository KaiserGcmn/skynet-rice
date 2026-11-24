#!/usr/bin/python3
"""Install the verified, exact-ABI module for the NEXT boot; never reload VMD.

Requires an explicitly reviewed work directory with build-verification.json,
install-manifest.json and an existing user-owned install-result.json. Keeps
the packaged module and a stock initramfs recovery entry. No other kernel is
changed. This is an administrative maintenance tool, not a restore hook.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import traceback

KERNEL = '6.12.115+deb13.1-amd64'
VERSION = '0.6-skynet-mtl016-deb13-115'
os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
BASE = Path(sys.argv[1]).resolve()
MODULE = Path('/lib/modules') / KERNEL / 'updates/skynet-vmd/vmd.ko'
INITRD = Path('/boot') / ('initrd.img-' + KERNEL)
BACKUP = Path(str(INITRD) + '.skynet-stock')
CUSTOM = Path('/boot/grub/custom.cfg')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode}): '
                           + result.stdout + result.stderr)
    return result.stdout


def regular(path):
    assert stat.S_ISREG(path.lstat().st_mode), str(path)


def atomic(path, data, mode):
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchown(stream.fileno(), 0, 0)
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def module_names(listing):
    return {re.sub(r'\.(xz|gz|zst)$', '', Path(line).name)
            for line in listing.splitlines()
            if re.search(r'\.ko(?:\.(?:xz|gz|zst))?$', line)}


def main():
    assert os.geteuid() == 0, 'Run through polkit as root'
    manifest = json.loads((BASE / 'install-manifest.json').read_text())
    verification = json.loads((BASE / 'build-verification.json').read_text())
    assert os.uname().release == KERNEL == manifest['kernel']
    assert verification['kernel'] == KERNEL
    assert verification['stock_text_reproduced']
    assert verification['all_imported_symbols_match_kernel']
    assert Path('/sys/bus/pci/devices/0000:00:0e.0/vendor').read_text().strip() == '0x8086'
    assert Path('/sys/bus/pci/devices/0000:00:0e.0/device').read_text().strip() == '0x7d0b'
    assert 'SecureBoot disabled' in run('/usr/bin/mokutil', '--sb-state')
    assert '[none]' in Path('/sys/kernel/security/lockdown').read_text()
    assert not any(p.exists() or p.is_symlink() for p in (MODULE.parent, BACKUP, CUSTOM))
    for name, expected in manifest['protected'].items():
        path = Path(name)
        regular(path)
        assert path.stat().st_uid == 0, name
        assert digest(path.read_bytes()) == expected, 'Changed before install: ' + name

    candidate = (BASE / 'build-patched/vmd.ko').read_bytes()
    assert digest(candidate) == manifest['module_sha256'] == verification['patched']['sha256']
    stock = INITRD.read_bytes()
    grub = Path('/boot/grub/grub.cfg').read_bytes()
    assert 'source ${config_directory}/custom.cfg' in grub.decode()
    blocks = re.findall(r"^menuentry .*?\n\}", grub.decode(), re.M | re.S)
    blocks = [block for block in blocks if re.search(
        r'^\s*linux\s+/boot/vmlinuz-' + re.escape(KERNEL) + r'\s', block, re.M)]
    assert len(blocks) == 1, 'Expected exactly one top-level current-kernel entry'
    entry = blocks[0]
    assert re.search(r'^\s*initrd\s+/boot/initrd.img-' + re.escape(KERNEL) + r'\s*$', entry, re.M)
    recovery = entry.replace(entry.splitlines()[0],
        "menuentry 'Devuan 6.12.115 - original VMD (recovery)' "
        "--class devuan --class gnu-linux --id skynet-vmd-stock {")
    recovery = re.sub(r'(^\s*initrd\s+)/boot/initrd.img-' + re.escape(KERNEL) + r'\s*$',
                      lambda match: match[1] + str(BACKUP), recovery, flags=re.M)
    recovery = ('# SKYNET exact-kernel VMD fallback; original kernel arguments preserved.\n'
                + recovery + '\n').encode()
    before_listing = run('/usr/bin/lsinitramfs', str(INITRD))
    old_modules = module_names(before_listing)
    assert 'vmd.ko' in old_modules
    installed = False
    switched = False
    backup_created = False
    custom_created = False
    result = {}
    with tempfile.TemporaryDirectory(prefix='skynet-vmd-', dir='/var/tmp') as temporary:
        temporary = Path(temporary)
        try:
            reviewed = temporary / 'vmd.ko'
            reviewed.write_bytes(candidate)
            assert run('/usr/sbin/modinfo', '-F', 'version', str(reviewed)).strip() == VERSION
            assert run('/usr/sbin/modinfo', '-F', 'vermagic', str(reviewed)).split()[0] == KERNEL
            custom_check = temporary / 'custom.cfg'
            custom_check.write_bytes(recovery)
            run('/usr/bin/grub-script-check', str(custom_check))
            MODULE.parent.mkdir(mode=0o755)
            installed = True
            atomic(MODULE, candidate, 0o644)
            run('/usr/sbin/depmod', '-a', KERNEL)
            assert Path(run('/usr/sbin/modinfo', '-k', KERNEL, '-n', 'vmd').strip()).resolve() == MODULE.resolve()
            new_initrd = temporary / 'initrd.img'
            print('Building and checking next-boot initramfs...', flush=True)
            run('/usr/sbin/mkinitramfs', '-o', str(new_initrd), KERNEL)
            listing = run('/usr/bin/lsinitramfs', str(new_initrd))
            assert not (old_modules - module_names(listing)), 'Storage/module files lost'
            unpacked = temporary / 'unpacked'
            run('/usr/bin/unmkinitramfs', str(new_initrd), str(unpacked))
            modules = [p for p in unpacked.rglob('vmd.ko*') if p.is_file()]
            root = next(unpacked.glob('main'))
            selected = root / 'usr/lib/modules' / KERNEL / 'updates/skynet-vmd/vmd.ko'
            original = root / 'usr/lib/modules' / KERNEL / 'kernel/drivers/pci/controller/vmd.ko.xz'
            # MODULES=most can include the packaged module as well. Both files
            # must be known; the dependency index and actual PCI modalias must
            # resolve exclusively to the verified override.
            assert selected in modules
            assert set(modules) <= {selected, original}, 'Unexpected VMD copies'
            assert digest(selected.read_bytes()) == digest(candidate)
            if original in modules:
                expected = manifest['protected'][str(Path('/lib/modules') / KERNEL /
                    'kernel/drivers/pci/controller/vmd.ko.xz')]
                assert digest(original.read_bytes()) == expected
            plan = run('/usr/sbin/modprobe', '-d', str(root), '-S', KERNEL,
                       '--show-depends', 'vmd')
            assert '/updates/skynet-vmd/vmd.ko' in plan
            assert '/kernel/drivers/pci/controller/vmd.ko' not in plan
            alias = Path('/sys/bus/pci/devices/0000:00:0e.0/modalias').read_text().strip()
            alias_plan = run('/usr/sbin/modprobe', '-d', str(root), '-S', KERNEL,
                             '--show-depends', alias)
            assert '/updates/skynet-vmd/vmd.ko' in alias_plan
            assert '/kernel/drivers/pci/controller/vmd.ko' not in alias_plan
            assert (root / 'init').is_file()
            assert 'nvme.ko' in module_names(listing)
            assert 'ext4.ko' in module_names(listing)
            for name, expected in manifest['protected'].items():
                assert digest(Path(name).read_bytes()) == expected, 'Concurrent change: ' + name
            assert Path('/boot/grub/grub.cfg').read_bytes() == grub
            atomic(BACKUP, stock, stat.S_IMODE(INITRD.stat().st_mode))
            backup_created = True
            atomic(CUSTOM, recovery, 0o600)
            custom_created = True
            # Every referenced file exists before the default initramfs is replaced.
            atomic(INITRD, new_initrd.read_bytes(), stat.S_IMODE(INITRD.stat().st_mode))
            switched = True
            assert digest(INITRD.read_bytes()) == digest(new_initrd.read_bytes())
            assert BACKUP.read_bytes() == stock
            assert Path('/boot/grub/grub.cfg').read_bytes() == grub
            for name, expected in manifest['protected'].items():
                if Path(name) != INITRD:
                    assert digest(Path(name).read_bytes()) == expected, name
            os.sync()
            result = dict(installed=True, runtime_tested=False, kernel=KERNEL,
                          module_version=VERSION, module_sha256=digest(candidate),
                          initrd_sha256=digest(INITRD.read_bytes()),
                          stock_initrd_sha256=digest(stock), recovery_initrd=str(BACKUP),
                          recovery_entry='Devuan 6.12.115 - original VMD (recovery)',
                          protected_files_unchanged=True, initrd_module_verified=True,
                          original_module_unchanged=True,
                          running_vmd_version=Path('/sys/module/vmd/version').read_text().strip())
        except BaseException:
            if switched:
                atomic(INITRD, stock, 0o644)
            if custom_created:
                CUSTOM.unlink()
            if backup_created:
                BACKUP.unlink()
            if installed:
                if MODULE.exists():
                    MODULE.unlink()
                MODULE.parent.rmdir()
                run('/usr/sbin/depmod', '-a', KERNEL)
            raise
    return result


if __name__ == '__main__':
    output = BASE / 'install-result.json'
    regular(output)
    owner = output.stat().st_uid
    assert owner != 0
    fd = os.open(output, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
    assert os.fstat(fd).st_uid == owner
    try:
        outcome = main()
    except BaseException:
        outcome = {'installed': False, 'error': traceback.format_exc()}
    with os.fdopen(fd, 'w') as stream:
        json.dump(outcome, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(outcome, indent=2), flush=True)
    sys.exit(0 if outcome.get('installed') else 1)
