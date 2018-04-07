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


def move_finished_file(args, name):
    print(f'Moving {name} from {args.temp} to {args.dest}')
    os.makedirs(os.path.join(args.dest, os.path.dirname(name)), exist_ok=True)
    os.rename(name, name, src_dir_fd=args.temp_fd, dst_dir_fd=args.dest_fd)


def find_local_finished_files(args, remote_file_set):
    for dirpath, dirnames, filenames, dirfd in os.fwalk('.', dir_fd=args.temp_fd):
        for name in filenames:
            full = os.path.normpath(os.path.join(dirpath, name))
            if full not in remote_file_set:
                yield full


def fetch_remote_files(args):
    files_str = subprocess.check_output(
        ['ssh', args.host,
         f'cd {shlex.quote(args.src)} && {{ find -type d -delete; find -type f -printf \'%p\\0%s\\0\' }} 2>/dev/null'])

    parts = files_str.decode('utf-8').split('\0')
    files = [
        (os.path.normpath(filename), int(size))
        for (filename, size) in zip(parts[::2], parts[1::2])
    ]
    files.sort(key=lambda item: item[1])
    return files


def transfer(args, file_list, size):
    print(f'Transferring {len(file_list)} files, total size {size/1048576} MiB')

    lftp_cmds = [
        f'open sftp://{args.host}{args.src} || exit 1',
    ]
    if args.rate_limit:
        lftp_cmds.append(f'set net:limit-rate {args.rate_limit}K')

    for filename in file_list:
        subdir = os.path.dirname(filename)

        os.makedirs(os.path.join(args.temp, subdir), exist_ok=True)

        lftp_cmds += [
            f'get -c -E {shlex.quote(filename)} -o {shlex.quote(filename)} || exit 1',
        ]

    lftp_cmd = ' ; '.join(lftp_cmds)
    cmd = ['lftp', '-c', lftp_cmd]
    # print(cmd)
    subprocess.check_call(cmd, cwd=args.temp)

    for filename in file_list:
        move_finished_file(args, filename)


def clean_empty_temp_dirs(args):
    for dirpath, dirnames, filenames, dirfd in os.fwalk('.', topdown=False, dir_fd=args.temp_fd):
        try:
            os.rmdir(dirpath, dir_fd=args.temp_fd)
        except OSError:
            pass


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

    args.temp_fd = os.open(args.temp, os.O_CLOEXEC | os.O_RDONLY | os.O_DIRECTORY)
    args.dest_fd = os.open(args.dest, os.O_CLOEXEC | os.O_RDONLY | os.O_DIRECTORY)

    f = open(args.lock, 'a')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return

    for name in (args.temp, args.dest):
        if not os.path.isdir(name):
            sys.exit(f'{name} is not a directory')

    files = fetch_remote_files(args)

    file_set = set(item[0] for item in files)
    for filename in find_local_finished_files(args, file_set):
        move_finished_file(args, filename)

    trans_file_list = []
    trans_file_list_size = 0
    for filename, size in files:

        trans_file_list.append(filename)
        trans_file_list_size += size

        if trans_file_list_size >= 100*1024*1024 or len(trans_file_list) >= 100:
            transfer(args, trans_file_list, trans_file_list_size)
            trans_file_list = []
            trans_file_list_size = 0

    if trans_file_list:
        transfer(args, trans_file_list, trans_file_list_size)

    clean_empty_temp_dirs(args)


if __name__ == '__main__':
    main()
