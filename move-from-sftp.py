#!/usr/bin/env python3
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2018, chys <admin@CHYS.INFO>
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


import argparse
import fcntl
import os
import shlex
import subprocess
import sys


def fetch_dir_structure(host, src, temp):
    dirs_str = subprocess.check_output(
        ['ssh', host,
         f'cd {shlex.quote(src)} && {{ find -type d -delete; find -type d -print0 }} 2>/dev/null'])
    return list(filter(None, dirs_str.decode('utf-8').split('\0')))


def main():
    parser = argparse.ArgumentParser(
        description='MOVE files from remote SFTP server')
    parser.add_argument('lock', help='Lock file')
    parser.add_argument('host', help='Remote host')
    parser.add_argument('src', help='Remote src dir')
    parser.add_argument('temp', help='Local temporary dir')
    parser.add_argument('dest', help='Location destination dir')
    parser.add_argument('-r', '--rate-limit', type=int,
                        help='Rate limit in KiB/s')
    args = parser.parse_args()

    f = open(args.lock, 'a')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return

    for name in (args.temp, args.dest):
        if not os.path.isdir(name):
            sys.exit(f'{name} is not a directory')

    subdirs = fetch_dir_structure(args.host, args.src, args.temp)

    lftp_cmds = [
        f'open sftp://{args.host}{args.src} || exit 1',
    ]
    if args.rate_limit:
        lftp_cmds.append(f'set net:limit-rate {args.rate_limit}K')

    for subdir in subdirs:

        subtemp = os.path.join(args.temp, subdir)

        if subdir != '.':
            os.makedirs(subtemp, exist_ok=True)

        lftp_cmds += [
            f'cd {shlex.quote(subdir)} || exit 1',
            f'lcd {shlex.quote(subdir)} || exit 1',
            'glob --not-exist * || mget -c -E * || exit 1',
            'cd -',
            'lcd -',
        ]

    lftp_cmd = ' ; '.join(lftp_cmds)
    cmd = ['lftp', '-c', lftp_cmd]
    print(cmd)

    subprocess.check_call(cmd, cwd=args.temp)

    for name in os.listdir(args.temp):
        src = os.path.join(args.temp, name)
        dst = os.path.join(args.dest, name)
        print(f'Moving {src} to {dst}')
        os.rename(src, dst)


if __name__ == '__main__':
    main()
