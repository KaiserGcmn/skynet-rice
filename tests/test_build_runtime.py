"""Desktop build staging must not ship Python bytecode from runtime/."""
import importlib.util
from pathlib import Path
import tempfile
import unittest


BUILD = Path(__file__).resolve().parents[1] / 'scripts/build.py'
spec = importlib.util.spec_from_file_location('skynet_build', BUILD)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class RuntimeFilesTest(unittest.TestCase):
    def test_bytecode_caches_are_not_staged(self):
        with tempfile.TemporaryDirectory(prefix='skynet-build-test-') as directory:
            runtime = Path(directory)
            for name in ('usr/local/bin/helper', 'etc/init.d/service',
                         'usr/local/bin/__pycache__/helper.cpython-313.pyc',
                         'usr/local/libexec/stray.pyc'):
                path = runtime / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('x')
            staged = [str(path.relative_to(runtime)) for path in build.runtime_files(runtime)]
            self.assertEqual(staged, ['etc/init.d/service', 'usr/local/bin/helper'])


if __name__ == '__main__':
    unittest.main()
