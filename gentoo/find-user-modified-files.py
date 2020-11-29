#!/usr/bin/env python3
#
# Copyright (c) 2020, chys <admin@CHYS.INFO>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
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
import dataclasses
import enum
import glob
import hashlib
import os
import re
from typing import Dict, Iterator, Tuple


class FileType(enum.Enum):
    OBJ = enum.auto()
    SYM = enum.auto()


@dataclasses.dataclass
class FileDetail:
    ft: FileType
    md5: str = ''  # OBJ only
    target: str = ''  # SYM only


class FileSource(enum.Enum):
    PORTAGE = enum.auto()
    USER = enum.auto()
    BOTH = enum.auto()  # User-modified


def read_contents_file(contents_filename: str) \
        -> Iterator[Tuple[str, FileDetail]]:
    _ignore_re = re.compile(r'^(dir|dev|fif) ')
    _obj_re = re.compile(r'^obj (?P<path>.+) (?P<md5>[\da-f]{32}) \d+$')
    _sym_re = re.compile(r'^sym (?P<path>.+) -> (?P<target>.+) \d+$')

    with open(contents_filename) as f:
        for line in f:
            line = line.rstrip()
            if (m := _obj_re.match(line)):
                yield m.group('path'), FileDetail(FileType.OBJ, m.group('md5'))
            elif (m := _sym_re.match(line)):
                yield (m.group('path'),
                       FileDetail(FileType.SYM, m.group('target')))
            elif _ignore_re.match(line):
                continue
            else:
                raise ValueError(
                    f'Unrecognized line {contents_filename}: "{line}"')


def collect_installed_files() -> Dict[str, FileDetail]:
    res: Dict[str, FileDetail] = {}
    for contents_file in glob.iglob('/var/db/pkg/*/*/CONTENTS'):
        res.update(read_contents_file(contents_file))
    return res


def is_modified(detail: FileDetail, path: str) -> bool:
    try:
        target = os.readlink(path)
        return detail.target == target
    except OSError:
        pass

    try:
        with open(path, 'rb') as f:
            content = f.read()
    except (OSError, IOError):
        return True
    return hashlib.md5(content).hexdigest() != detail.md5


def find_files(dir: str, installed: Dict[str, FileDetail]) \
        -> Iterator[Tuple[str, FileSource]]:
    for path, dirs, files in os.walk(dir):
        for fname in files:
            fpath = os.path.join(path, fname)
            portage_detail = installed.get(fpath)
            if not portage_detail:
                yield fpath, FileSource.USER
            elif is_modified(portage_detail, fpath):
                yield fpath, FileSource.BOTH
            else:
                yield fpath, FileSource.PORTAGE


def main():
    parser = argparse.ArgumentParser(
        description='Determine whether files are created, modified by user '
                    'or installed by portage.')
    parser.add_argument('dir')
    parser.add_argument('--created', '-c',
                        help='Show user created files',
                        action='store_true', default=False)
    parser.add_argument('--modified', '-m',
                        help='Show user modified files',
                        action='store_true', default=False)
    parser.add_argument('--installed', '-i',
                        help='Show portage installed files',
                        action='store_true', default=False)
    parser.add_argument('--relative', '-r',
                        help='Show relative path.',
                        action='store_true')
    args = parser.parse_args()

    if not args.created and not args.modified and not args.installed:
        return

    installed_files = collect_installed_files()
    for path, src in find_files(args.dir, installed_files):
        if (src == FileSource.USER and args.created) or \
                (src == FileSource.BOTH and args.modified) or \
                (src == FileSource.PORTAGE and args.installed):
            if args.relative:
                show_path = os.path.relpath(path, args.dir)
            else:
                show_path = path
            print(show_path)


if __name__ == '__main__':
    main()
