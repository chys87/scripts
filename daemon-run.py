#!/usr/bin/env python
# coding: utf-8

#
# Copyright (c) 2019, chys <admin@CHYS.INFO>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#   Neither the name of chys <admin@CHYS.INFO> nor the names of other
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import print_function

import os
import pprint
import pwd
import socket
import stat
import sys
import subprocess
import threading
import time

try:
    import Queue as queue
except ImportError:
    import queue

try:
    import cPickle as pickle
except ImportError:
    import pickle


def get_socket_path():
    return '\0/tmp/daemon-run-{}'.format(pwd.getpwuid(os.getuid()).pw_name)


def colorize(*args, **kwargs):
    color = kwargs.pop('color')
    print('[{}] \033[{}m'.format(time.strftime('%Y-%m-%d %H:%M:%S'), color),
          end='')
    kwargs['end'] = '\033[0m' + kwargs.pop('end', '\n')
    print(*args, **kwargs)


def info(*args, **kwargs):
    colorize(*args, color='32', **kwargs)


def error(*args, **kwargs):
    colorize(*args, color='31;1', **kwargs)


current_proc = None


def executor(q):
    global current_proc
    while True:
        req = q.get()
        if req is None:
            break
        info('Handling request: {}'.format(pprint.pformat(req)))
        try:
            current_proc = subprocess.Popen(req['cmd'], cwd=req['pwd'])
            ret = current_proc.wait()
        except (KeyError, TypeError, ValueError, OSError) as e:
            error('Failed to execute command {}: {}'.format(
                pprint.pformat(req), str(e)))
        else:
            info('Done with request: {} ret code: {}'.format(
                pprint.pformat(req), ret))
        finally:
            current_proc = None


def daemon_handle(q, conn):
    try:
        try:
            req_s = conn.recv(16384)
        except socket.error as e:
            error(str(e))
            return
        info('Received {} bytes'.format(len(req_s)))

        try:
            req = pickle.loads(req_s)
        except (pickle.UnpicklingError, ValueError, TypeError) as e:
            error(str(e))
            conn.send(b'Failed to unpickle message')
            return

        conn.send(b'OK')

    except socket.error as e:
        error(str(e))
        return
    finally:
        conn.close()

    info('Parsed request: {}'.format(pprint.pformat(req)))

    cmd = req.get('cmd', ())
    if cmd and cmd[0] == '--kill':
        proc = current_proc
        if proc:
            for i in range(20):
                if proc.poll() is not None:
                    break
                else:
                    proc.terminate()
                    info('Sent SIGTERM to current process')
                    time.sleep(0.1)
            else:
                proc.kill()
                info('Sent SIGKILL to current process')
        else:
            error('No current process to kill')
    else:
        q.put(req)


def daemon():
    path = get_socket_path()
    s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(path)
    s.listen(5)
    info('Listing on Unix-domain socket', s.getsockname())

    q = queue.Queue()
    th = threading.Thread(target=executor, args=(q,))
    th.start()

    try:
        while True:
            conn, addr = s.accept()
            info('Accepted new conection', addr)
            daemon_handle(q, conn)
    except KeyboardInterrupt:
        import signal
        sys.exit(128 + signal.SIGINT)
    finally:
        q.put(None)
        th.join()


def get_cwd():
    env = os.environ.get('PWD')
    real = os.getcwd()

    if not env:
        return real

    try:
        st_env = os.stat(env)
    except (IOError, OSError):
        return real

    try:
        st_real = os.stat(real)
    except (IOError, OSError):
        return env

    if stat.S_ISDIR(st_env.st_mode) and st_env == st_real:
        return env
    else:
        return real


def client():
    path = get_socket_path()
    s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    s.connect(path)
    msg = {
        'pwd': get_cwd(),
        'cmd': sys.argv[1:],
    }
    info(pprint.pformat(msg))
    # Force version 2 so that Python 2 and 3 can be used interchagably
    s.send(pickle.dumps(msg, 2))
    info('RECEIVED FROM DAEMON:', s.recv(4096))


def main():
    if len(sys.argv) < 2:
        daemon()
    else:
        client()


if __name__ == '__main__':
    main()
