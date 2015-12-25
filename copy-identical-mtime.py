#!/usr/bin/env python3
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2015, chys <admin@CHYS.INFO>
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
import binascii
import collections
from datetime import datetime
import fnmatch
import hashlib
import os
import stat


File = collections.namedtuple('File', ['path', 'mtime_ns'])


SKIP_DIRS = ['.git', '.svn', '.hg']


def flt(files, pattern):
    if pattern:
        return fnmatch.filter(files, pattern)
    else:
        return files


def init_src_dic(src, pattern):
    dic = {}

    for dirname, subdirs, subfiles, dirfd in os.fwalk(src):
        for skip in SKIP_DIRS:
            if skip in subdirs:
                subdirs.remove(skip)
        for fname in flt(subfiles, pattern):
            st = os.stat(fname, dir_fd=dirfd, follow_symlinks=False)
            if stat.S_ISREG(st.st_mode):
                fullname = os.path.join(dirname, fname)
                dic.setdefault(fname, []).append(fullname)

    return dic


def hash_file(path, dir_fd=None):
    def opener(name, flags):
        return os.open(name, flags, dir_fd=dir_fd)

    with open(path, 'rb', opener=opener) as f:
        content = f.read()
    return hashlib.md5(content).digest()


def hash_files(filename_list):
    if not isinstance(filename_list, list):
        return filename_list

    res = {}
    for path in filename_list:
        h = hash_file(path)
        mtime_ns = os.stat(path).st_mtime_ns

        if h not in res or res[h].mtime_ns < mtime_ns:
            res[h] = File(path=path, mtime_ns=mtime_ns)

    return res


def copy(src_dic, dst, pattern, pretend):
    for dirname, subdirs, subfiles, dirfd in os.fwalk(dst):
        for fname in flt(subfiles, pattern):
            src_info = src_dic.get(fname)
            if not src_info:
                continue
            if not isinstance(src_info, dict):
                src_info = src_dic[fname] = hash_files(src_info)

            st = os.stat(fname, dir_fd=dirfd)
            if not stat.S_ISREG(st.st_mode):
                continue

            h = hash_file(fname, dir_fd=dirfd)

            src_file = src_info.get(h)
            if src_file:
                dst_path = os.path.join(dirname, fname)
                src_mtime_ns = src_file.mtime_ns
                print('{h} {mtime:%Y-%m-%d %H:%M:%S.%f} {src} => {dst}'.format(
                      src=src_file.path,
                      dst=dst_path,
                      mtime=datetime.fromtimestamp(src_mtime_ns / 1.e9),
                      h=binascii.hexlify(h).decode()))
                if not pretend:
                    os.utime(fname, dir_fd=dirfd,
                             ns=(src_mtime_ns, src_mtime_ns))


def main():
    parser = argparse.ArgumentParser(
        description='Copy file mtime by identicality')
    parser.add_argument('src', type=str, help='Source dir')
    parser.add_argument('dst', type=str, help='Destination dir')
    parser.add_argument('-p', '--pattern', help='Pattern (e.g. *.h)')
    parser.add_argument('-P', '--pretend', action='store_true',
                        help='Don\'t actually copy mtime')
    args = parser.parse_args()

    src_dic = init_src_dic(args.src, args.pattern)

    copy(src_dic, args.dst, args.pattern, args.pretend)


if __name__ == '__main__':
    main()
