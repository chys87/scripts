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


def ensure_dirs_for_files(dir_fd, base, files):
    ensured_dirs = set()
    for name in files:
        dirname = os.path.dirname(name)
        if dirname in ensured_dirs:
            continue
        ensured_dirs.add(dirname)
        if not os.access(dirname, os.F_OK, dir_fd=dir_fd):
            full = os.path.join(base, dirname)
            print(f'Mkdir {full}')
            os.makedirs(full, exist_ok=True)


def move_finished_files(args, names):
    if not names:
        return

    ensure_dirs_for_files(args.dest_fd, args.dest, names)

    print(f'Moving {len(names)} files from {args.temp} to {args.dest}')
    for name in names:
        os.rename(name, name, src_dir_fd=args.temp_fd, dst_dir_fd=args.dest_fd)


def find_local_finished_files(args, remote_file_set):
    res = []
    for dirpath, dirnames, filenames, dirfd in os.fwalk('.',
                                                        dir_fd=args.temp_fd):
        for name in filenames:
            full = os.path.normpath(os.path.join(dirpath, name))
            if full not in remote_file_set:
                res.append(full)
    return res


def fetch_remote_files(args):
    files_str = subprocess.check_output(
        ['ssh', args.host,
         f'cd {shlex.quote(args.src)} && ' +
         "{ find -type d -delete; find -type f -printf \'%p\\0%s\\0\' } " +
         '2>/dev/null'])

    parts = files_str.decode('utf-8').split('\0')

    res = []

    for filename, size in zip(parts[::2], parts[1::2]):
        filename = os.path.normpath(filename)
        total_size = int(size)

        try:
            fetched_size = os.stat(filename, dir_fd=args.temp_fd).st_size
        except FileNotFoundError:
            fetched_size = 0

        res.append((filename, total_size - fetched_size))

    res.sort(key=lambda item: item[1])
    return res


def transfer(args, file_list, size):
    if not file_list:
        return

    ensure_dirs_for_files(args.temp_fd, args.temp, file_list)

    print(f'Downloading {len(file_list)} files, '
          f'total size {size/1048576:.2f} MiB')

    lftp_cmds = [
        f'open sftp://{args.host}{args.src} || exit 1',
    ]
    if args.rate_limit:
        lftp_cmds.append(f'set net:limit-rate {args.rate_limit}K')

    lftp_cmds.append('get -c -E ' + ' '.join(
        f'{quoted} -o {quoted}' for quoted in map(shlex.quote, file_list)))

    lftp_cmd = ' ; '.join(lftp_cmds)
    cmd = ['lftp', '-c', lftp_cmd]
    subprocess.check_call(cmd, cwd=args.temp)

    move_finished_files(args, file_list)


def clean_empty_temp_dirs(args):
    for dirpath, dirnames, filenames, dirfd in os.fwalk('.', topdown=False,
                                                        dir_fd=args.temp_fd):
        if not dirnames and not filenames:
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
    parser.add_argument('-M', '--max-mb-per-transfer', type=int, default=100,
                        help='Max number of mebibytes for each transfer'
                             ' (default: 100)')
    parser.add_argument('-N', '--max-files-per-transfer',
                        type=int, default=100,
                        help='Max number of files for each transfer'
                             ' (default: 100)')
    args = parser.parse_args()

    f = open(args.lock, 'a')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return

    for name in (args.temp, args.dest):
        if not os.path.isdir(name):
            sys.exit(f'{name} is not a directory')

    args.temp_fd = os.open(args.temp,
                           os.O_CLOEXEC | os.O_RDONLY | os.O_DIRECTORY)
    args.dest_fd = os.open(args.dest,
                           os.O_CLOEXEC | os.O_RDONLY | os.O_DIRECTORY)

    files = fetch_remote_files(args)

    file_set = set(item[0] for item in files)
    move_finished_files(args, find_local_finished_files(args, file_set))

    trans_file_list = []
    trans_file_list_size = 0
    for filename, size in files:

        if trans_file_list and (
                len(trans_file_list) >= args.max_files_per_transfer or
                trans_file_list_size + size >
                args.max_mb_per_transfer * 1048576):

            transfer(args, trans_file_list, trans_file_list_size)
            trans_file_list = []
            trans_file_list_size = 0

        trans_file_list.append(filename)
        trans_file_list_size += size

    if trans_file_list:
        transfer(args, trans_file_list, trans_file_list_size)

    clean_empty_temp_dirs(args)


if __name__ == '__main__':
    main()
