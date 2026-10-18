#!/usr/bin/env python3
"""Build into a fresh .build directory; never install or activate anything."""
import argparse
import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://deb.debian.org/debian/pool/main/x/xsecurelock/xsecurelock_1.9.0.orig.tar.gz'
SHA256 = '6e8df4d804e388499e7a9116161a0355034d2ebb61471291383875be515e8025'


def run(args, cwd, env=None):
    print('+ ' + shlex.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def output(args):
    return shlex.split(subprocess.check_output(args, text=True).strip())


def install(source, dest, executable=True):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    dest.chmod(0o755 if executable else 0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-locker', action='store_true', help='Download hash-verified XSecureLock 1.9.0 and apply the saved patch')
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Build as an ordinary user, without sudo.')
    if not 1 <= args.jobs <= 16:
        parser.error('--jobs must be between 1 and 16')
    build_root = ROOT / '.build'
    if build_root.is_symlink():
        parser.error('.build must not be a symlink')
    build_root.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='desktop-', dir=build_root))
    stage = work / 'rootfs'
    stage.mkdir()
    for name in ('dwm', 'dmenu', 'slstatus', 'xwinwrap', 'gtkgreet-skynet'):
        src = work / name
        shutil.copytree(ROOT / 'sources' / name, src)
        run(['make', '-j' + str(args.jobs)], src)
        binaries = {'dwm': ['dwm'], 'dmenu': ['dmenu', 'stest', 'dmenu_run', 'dmenu_path'],
                    'slstatus': ['slstatus'], 'xwinwrap': ['xwinwrap'],
                    'gtkgreet-skynet': ['gtkgreet-skynet']}[name]
        for binary in binaries:
            target = 'usr/local/libexec/greetd/' if name == 'gtkgreet-skynet' else 'usr/local/bin/'
            install(src / binary, stage / target / binary)
    env = dict(os.environ, DEB_BUILD_MAINT_OPTIONS='hardening=+all')
    flags = lambda key: shlex.split(subprocess.check_output(['dpkg-buildflags', '--get', key], env=env, text=True))
    style = ROOT / 'sources/xsecurelock-style'
    for name in ('saver-lock-style', 'tuigreet-battery'):
        libs = ['xft', 'xrender', 'xscrnsaver', 'libpng'] if name == 'saver-lock-style' else []
        command = ['cc', *flags('CPPFLAGS'), *flags('CFLAGS'), '-Wall', '-Wextra', '-Werror']
        if libs:
            command += output(['pkg-config', '--cflags', *libs])
        command += [str(style / (name + '.c')), '-o', str(work / name), *flags('LDFLAGS')]
        if libs:
            command += output(['pkg-config', '--libs', *libs]) + ['-lXext', '-lm']
        run(command, work, env)
        install(work / name, stage / 'usr/local/libexec' / name)
    for source in sorted((ROOT / 'runtime').rglob('*')):
        if source.is_file():
            install(source, stage / source.relative_to(ROOT / 'runtime'))
    # Only the desktop autostart enters staging. Debian services/boot/PAM stay in reference profiles.
    install(ROOT / 'profiles/debian/rootfs/etc/dwm/autostart.sh', stage / 'etc/dwm/autostart.sh')
    if args.with_locker:
        archive_path = work / 'xsecurelock.tar.gz'
        with urllib.request.urlopen(URL, timeout=90) as response, archive_path.open('wb') as stream:
            shutil.copyfileobj(response, stream)
        if hashlib.sha256(archive_path.read_bytes()).hexdigest() != SHA256:
            raise SystemExit('XSecureLock source checksum mismatch; no archive extracted.')
        extracted = work / 'locker-source'
        extracted.mkdir()
        with tarfile.open(archive_path) as archive:
            archive.extractall(extracted, filter='data')
        src = next(p for p in extracted.iterdir() if p.is_dir())
        run(['patch', '--batch', '--fuzz=0', '-p1', '-i', ROOT / 'sources/xsecurelock-power/local-changes.patch'], src)
        env.update(CFLAGS=shlex.join(flags('CFLAGS')), CPPFLAGS=shlex.join(flags('CPPFLAGS') + ['-D_DEFAULT_SOURCE']),
                   LDFLAGS=shlex.join(flags('LDFLAGS')), GIT_VERSION='1.9.0-local-power')
        if not (src / 'configure').exists():
            run(['autoreconf', '-fi'], src, env)
        run(['./configure', '--prefix=/usr/local', '--libexecdir=/usr/libexec', '--without-pam',
             '--with-default-authproto-module=authproto_pam', '--with-default-auth-module=auth_x11', '--without-pandoc'], src, env)
        run(['make', '-j' + str(args.jobs), 'xsecurelock'], src, env)
        install(src / 'xsecurelock', stage / 'usr/local/bin/xsecurelock-power')
    (build_root / 'last-build.txt').write_text(str(work) + '\n')
    print(f'\nBuild complete. Staging directory: {stage}\nNothing installed. Read docs/RESTORE.md and docs/DEVUAN.md.')


if __name__ == '__main__':
    main()
