#!/usr/bin/env python3
"""Package a previously extracted/patched Kitty 0.50.0 source tree.

Uses native system Python/libraries. Reuses only verified official kitten,
fonts, precompiled shaders and Slang; never downloads a Go toolchain.
No install or root operation. See README.md for source/dependency preparation.
"""

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import tarfile


ARCHIVE_SHA256 = "f04b11775574d6aabfb529b7e734cc0a7d7d12c7df9fb8ec1843e45420e514ee"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("official_archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--headers", type=Path, help="Optional extracted development packages")
    args = parser.parse_args()
    source, archive, output = (p.resolve() for p in (args.source, args.official_archive, args.output))
    if output.exists():
        parser.error("Output directory must not already exist")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        parser.error("Official binary archive checksum mismatch")
    official = output.with_name(output.name + ".official-build-input")
    if official.exists():
        parser.error("Build input directory already exists")
    try:
        with tarfile.open(archive) as handle:
            handle.extractall(official, filter="data")
        shutil.copytree(official / "lib/kitty/fonts", source / "fonts", dirs_exist_ok=True)
        shutil.copytree(official / "lib/kitty/shaders", source / "shaders", dirs_exist_ok=True)
        os.chdir(source)
        spec = importlib.util.spec_from_file_location("kitty_setup", source / "setup.py")
        setup = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = setup
        spec.loader.exec_module(setup)
        setup.build_ref_map()
        setup.build_cli_parser_specs()

        def official_helpers(options, launcher_dir, destination_dir="", for_freeze=False,
                             for_platform=None, shaders_dest=""):
            if for_freeze or for_platform or destination_dir:
                raise ValueError("This recipe supports a native Linux package only")
            target = Path(launcher_dir)
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(official / "bin/kitten", target / "kitten")
            if shaders_dest:
                shutil.copytree(official / "lib/kitty/shaders", shaders_dest, dirs_exist_ok=True)
            return str(target / "kitten")

        # A build-time provider for unchanged, checksum-verified release assets.
        # Runtime terminal code is compiled normally; no terminal-output filter.
        setup.build_static_kittens = official_helpers
        sys.argv = [str(source / "setup.py"), "linux-package", "--prefix", str(output),
                    "--skip-code-generation", "--vcs-rev", "skynet-compat-1",
                    "--update-check-interval", "0"]
        if args.headers:
            headers = args.headers.resolve()
            os.environ["PKG_CONFIG_PATH"] = str(headers / "usr/lib/x86_64-linux-gnu/pkgconfig")
            sys.argv += ["--extra-include-dirs", str(headers / "usr/include"),
                         "--extra-library-dirs", str(headers / "usr/lib/x86_64-linux-gnu"),
                         f"--python-compiler-flags=-I{headers}/usr/include/python3.13 "
                         f"-I{headers}/usr/include/x86_64-linux-gnu/python3.13"]
        os.environ.setdefault("CFLAGS", "-fstack-protector-strong -fstack-clash-protection -fcf-protection")
        os.environ.setdefault("LDFLAGS", "-Wl,-z,relro -Wl,-z,now")
        setup.main()
        shutil.copy2(official / "bin/slangc", output / "bin/slangc")
        for library in (official / "lib").glob("libslang-*.so*"):
            if library.is_symlink():
                (output / "lib" / library.name).symlink_to(library.readlink())
            else:
                shutil.copy2(library, output / "lib" / library.name)
        shutil.copy2(source / "LICENSE", output / "LICENSE")
        # Release packaging can retain the development launcher and test bytecode.
        # They are not needed for an installed terminal.
        dev_launcher = output / "lib/kitty/kitty/launcher"
        if dev_launcher.exists():
            shutil.rmtree(dev_launcher)
        print(f"Native package ready for validation: {output}")
    finally:
        if official.exists():
            shutil.rmtree(official)


if __name__ == "__main__":
    main()
