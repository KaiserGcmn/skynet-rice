"""Fake greetd IPC regression checks; never use PAM or real credentials."""
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include "proto.h"
static struct request request;
static const unsigned char *wire;
static size_t wire_length;
static int checked;
static int all_zero(const void *memory, size_t length) {
    const unsigned char *bytes = memory;
    for (size_t i = 0; i < length; i++) if (bytes[i]) return 0;
    return 1;
}
ssize_t __real_send(int, const void *, size_t, int);
ssize_t __real_read(int, void *, size_t);
ssize_t __wrap_send(int fd, const void *buffer, size_t length, int flags) {
    static int interrupted;
    if (!all_zero(&request, sizeof(request))) _exit(80);
    if (!wire && length > 4) { wire = buffer; wire_length = length; }
    if (getenv("TEST_INTERRUPTED_SEND") && !interrupted++) {
        errno = EINTR;
        return -1;
    }
    if (getenv("TEST_PARTIAL_SEND") && length > 1) length /= 2;
    return __real_send(fd, buffer, length, flags);
}
ssize_t __wrap_read(int fd, void *buffer, size_t length) {
    if (!all_zero(&request, sizeof(request)) || !wire ||
        !all_zero(wire, wire_length)) _exit(81);
    checked = 1;
    return __real_read(fd, buffer, length);
}
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    request.request_type = atoi(argv[1]);
    if (getenv("TEST_UNTERMINATED")) memset(&request.body, 'x', sizeof(request.body));
    else snprintf(request.body.request_post_auth_message_response.response,
                  sizeof(request.body.request_post_auth_message_response.response), "%s", argv[2]);
    struct response response = roundtrip(&request);
    if (!all_zero(&request, sizeof(request))) return 82;
    printf("%d %d\n", response.response_type, checked);
    return 0;
}
'''


class GreeterProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            raise unittest.SkipTest('requires cc and json-c development files')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'json-c'],
                               capture_output=True, text=True)
        if flags.returncode:
            raise unittest.SkipTest('requires json-c development files')
        cls.work = tempfile.TemporaryDirectory(prefix='hud-greeter-protocol-')
        cls.addClassCleanup(cls.work.cleanup)
        cls.directory = Path(cls.work.name)
        driver = cls.directory / 'driver.c'
        driver.write_text(DRIVER)
        cls.binary = cls.directory / 'check'
        source = ROOT / 'sources/gtkgreet-hud'
        subprocess.run(['cc', '-O2', '-Wall', '-Wextra', '-Werror', str(driver),
                        str(source / 'proto.c'), '-I' + str(source),
                        '-Wl,--wrap=send', '-Wl,--wrap=read', '-o', str(cls.binary),
                        *shlex.split(flags.stdout)], check=True, capture_output=True)
        # Some restricted build environments prohibit Unix sockets.
        with socket.socket(socket.AF_UNIX) as probe:
            try:
                probe.bind(str(cls.directory / 'probe'))
            except PermissionError:
                raise unittest.SkipTest('requires permission to create a private Unix socket')

    def call(self, kind=3, value='FAKE_AUDIT_PASSWORD', reply=None,
             raw_reply=None, env_extra=None, no_server=False):
        endpoint = self.directory / 'mock.sock'
        endpoint.unlink(missing_ok=True)
        env = dict(os.environ, GREETD_SOCK=str(endpoint))
        env.update(env_extra or {})
        received, errors = [], []
        if not no_server:
            server = socket.socket(socket.AF_UNIX)
            server.bind(str(endpoint))
            server.listen(1)
            server.settimeout(5)

            def exact(conn, length):
                data = b''
                while len(data) < length:
                    part = conn.recv(length - len(data))
                    if not part:
                        raise RuntimeError('truncated request')
                    data += part
                return data

            def serve():
                try:
                    with server:
                        conn, _ = server.accept()
                        with conn:
                            size = struct.unpack('=I', exact(conn, 4))[0]
                            received.append(json.loads(exact(conn, size)))
                            payload = json.dumps(reply if reply is not None else {
                                'type': 'error', 'error_type': 'auth_error',
                                'description': 'Synthetic rejection',
                            }).encode()
                            packet = raw_reply if raw_reply is not None else struct.pack('=I', len(payload)) + payload
                            if packet:
                                conn.sendall(packet)
                except BaseException as error:
                    errors.append(error)

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
        result = subprocess.run([str(self.binary), str(kind), value], env=env,
                                capture_output=True, text=True, timeout=6)
        if not no_server:
            thread.join(timeout=6)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors, errors)
        self.assertEqual(result.returncode, 0, result.stderr)
        response, scrub_checked = map(int, result.stdout.split())
        if not no_server:
            self.assertEqual(scrub_checked, 1, 'wire buffer must be erased before reply read')
        return response, received

    def test_secret_buffers_cleared_before_daemon_reply(self):
        for value in ['', 'FAKE_PASSWORD', 'tırnak"\\şifre\n\t',
                      ''.join(chr(i) for i in range(1, 32)), '\x01' * 127]:
            with self.subTest(value_length=len(value)):
                response, received = self.call(value=value)
                self.assertEqual(response, 2)
                self.assertEqual(received, [{'type': 'post_auth_message_response', 'response': value}])

    def test_all_request_types_and_partial_writes(self):
        cases = [(1, 'example', {'type': 'create_session', 'username': 'example'}),
                 (2, 'session --arg "quoted"', {'type': 'start_session', 'cmd': ['session --arg "quoted"']}),
                 (4, '', {'type': 'cancel_session'})]
        for kind, value, expected in cases:
            with self.subTest(kind=kind):
                response, received = self.call(kind, value, reply={'type': 'success'},
                                               env_extra={'TEST_PARTIAL_SEND': '1', 'TEST_INTERRUPTED_SEND': '1'})
                self.assertEqual(response, 1)
                self.assertEqual(received, [expected])

    def test_malformed_or_missing_reply_never_succeeds(self):
        replies = [b'', b'\x01', struct.pack('=I', 8) + b'{',
                   struct.pack('=I', 0), struct.pack('=I', 0xffffffff),
                   struct.pack('=I', 3) + b'bad']
        for packet in replies:
            with self.subTest(packet=packet):
                self.assertNotEqual(self.call(raw_reply=packet)[0], 1)
        for reply in [{}, [], {'type': 1}, {'type': 'unexpected'},
                      {'type': 'error', 'description': 'missing error type'},
                      {'type': 'auth_message', 'auth_message_type': 'bogus', 'auth_message': 'status'}]:
            with self.subTest(reply=reply):
                self.assertNotEqual(self.call(reply=reply)[0], 1)

    def test_transport_and_input_failures_erase_request(self):
        for kind, extra in [(3, {}), (3, {'GREETD_SOCK': 'x' * 200}),
                            (3, {'TEST_UNTERMINATED': '1'}), (99, {})]:
            with self.subTest(kind=kind, extra=extra):
                self.assertNotEqual(self.call(kind, env_extra=extra, no_server=True)[0], 1)

    def test_password_prompt_and_only_explicit_success(self):
        prompt = {'type': 'auth_message', 'auth_message_type': 'secret', 'auth_message': 'Password:'}
        self.assertEqual(self.call(reply=prompt)[0], 3)
        self.assertEqual(self.call(reply={'type': 'success'})[0], 1)


if __name__ == '__main__':
    unittest.main()
