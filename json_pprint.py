#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2014, chys <admin@CHYS.INFO>
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
import json
import pprint
import re
import sys


def fix_json(src):
    # I have to deal with a lot of non-standard JSON.
    # Try to fix them whenever possible.

    # Fix property names missing quotes
    src = re.sub(r'([\{,]\s*)(\w+)(?=\s*:)', r'\1"\2"', src)
    return src


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', nargs='?',
                        help='Input file. Default is standard input.')
    parser.add_argument('-F', '--format', type=str, default='python',
                        choices=['python', 'json'],
                        help='Output format')
    options = parser.parse_args()

    if options.file:
        with open(options.file, 'r') as f:
            src = f.read()
    else:
        src = sys.stdin.read()

    try:
        data = json.loads(src, strict=False)
    except ValueError:
        data = None
    if not data:
        data = json.loads(fix_json(src), strict=False)

    fmt = options.format.lower()
    if fmt == 'json':
        json.dump(data, sys.stdout, ensure_ascii=False, indent=4)
    else:
        pprint.pprint(data)


if __name__ == '__main__':
    main()
