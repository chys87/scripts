#!/usr/bin/env python3
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2018-2026, chys <admin@CHYS.INFO>
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
from dataclasses import dataclass
import fcntl
import os
import shlex
import subprocess
import sys


def move_finished_files(args, temp_fd: int, dest_fd: int, names: list[str]):
    if not names:
        return

    print(f'Moving {len(names)} files from {args.temp} to {args.dest}')
    for name in names:
        os.rename(name, name, src_dir_fd=temp_fd, dst_dir_fd=dest_fd)


def find_local_finished_files(temp_fd: int,
                              remote_file_set: set[str]) -> list[str]:
    '''
    Find local temp files that are not present at remote end
    '''
    res = []
    os.lseek(temp_fd, 0, os.SEEK_SET)
    for entry in os.scandir(temp_fd):
        if entry.is_file() and entry.name not in remote_file_set:
            res.append(entry.path)
    return res


@dataclass
class RemoteFile:
    name: str
    size: int
    done_size: int
    remain_size: int


def fetch_remote_files(args, temp_fd: int) -> list[RemoteFile]:
    files_str = subprocess.check_output(
        ['ssh', args.host,
         f'cd {shlex.quote(args.src)} && '
         "find -maxdepth 1 -type f -printf \'%p\\0%s\\0\' 2>/dev/null"])

    parts = files_str.decode('utf-8').split('\0')

    res: list[RemoteFile] = []

    for filename, size in zip(parts[::2], parts[1::2]):
        filename = os.path.normpath(filename)
        total_size = int(size)

        try:
            fetched_size = os.stat(filename, dir_fd=temp_fd).st_size
        except FileNotFoundError:
            fetched_size = 0

        res.append(RemoteFile(name=filename,
                              size=total_size,
                              done_size=fetched_size,
                              remain_size=total_size-fetched_size))

    match args.sort:
        case 'smaller':
            res.sort(key=lambda rf: (-rf.done_size, rf.remain_size))
        case 'larger':
            res.sort(key=lambda rf: (-rf.done_size, -rf.remain_size))
        case 'alpha':
            res.sort(key=lambda rf: (-rf.done_size, rf.name))
    return res


def transfer(args, temp_fd: int, dest_fd: int, file_list: list[str], size: int):
    if not file_list:
        return

    print(f'Downloading {len(file_list)} files, '
          f'total size {size/1048576:.2f} MiB')

    lftp_cmds = [
        f'open sftp://{args.host}{args.src} || exit 1',
    ]
    if args.rate_limit:
        lftp_cmds.append(f'set net:limit-rate {args.rate_limit}K')

    lftp_cmds.append('get -c ' + ' '.join(
        f'{quoted} -o {quoted}' for quoted in map(shlex.quote, file_list)))

    lftp_cmd = ' ; '.join(lftp_cmds)
    cmd = ['lftp', '-c', lftp_cmd]
    subprocess.check_call(cmd, cwd=args.temp)

    subprocess.check_call(
        ['ssh', args.host,
         f'cd {shlex.quote(args.src)} && '
         f'mv {" ".join(map(shlex.quote, file_list))} '
         f'{shlex.quote(args.src_bak)}'])

    move_finished_files(args, temp_fd, dest_fd, file_list)


def main():
    parser = argparse.ArgumentParser(
        description='MOVE files from remote SFTP server')
    parser.add_argument('lock', help='Lock file')
    parser.add_argument('host', help='Remote host')
    parser.add_argument('src', help='Remote src dir')
    parser.add_argument('src_bak', help='Remote backup dir')
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
    parser.add_argument('-s', '--sort',
                        type=str, default='smaller',
                        choices=('smaller', 'larger', 'alpha'),
                        help='Sort method (default: smaller)')
    args = parser.parse_args()

    f = open(args.lock, 'a')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return

    for name in (args.temp, args.dest):
        if not os.path.isdir(name):
            sys.exit(f'{name} is not a directory')

    temp_fd = os.open(args.temp,
                      os.O_CLOEXEC | os.O_RDONLY | os.O_DIRECTORY)
    dest_fd = os.open(args.dest,
                      os.O_CLOEXEC | os.O_RDONLY | os.O_DIRECTORY)

    files = fetch_remote_files(args, temp_fd)

    for rf in files:
        print(f'{rf.name}\t{rf.size/(1024*1024):.2f} MiB')

    file_set = set(item.name for item in files)
    move_finished_files(args, temp_fd, dest_fd,
                        find_local_finished_files(temp_fd, file_set))

    trans_file_list: list[str] = []
    trans_file_list_size = 0
    for rf in files:
        if trans_file_list and (
                len(trans_file_list) >= args.max_files_per_transfer or
                trans_file_list_size + rf.remain_size >
                args.max_mb_per_transfer * 1048576):

            transfer(args, temp_fd, dest_fd, trans_file_list, trans_file_list_size)
            trans_file_list = []
            trans_file_list_size = 0

        trans_file_list.append(rf.name)
        trans_file_list_size += rf.remain_size

    if trans_file_list:
        transfer(args, temp_fd, dest_fd, trans_file_list, trans_file_list_size)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        import signal
        sys.exit(128 + signal.SIGINT)
