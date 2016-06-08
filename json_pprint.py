#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2014, 2015, chys <admin@CHYS.INFO>
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
from collections import OrderedDict
import json
import pprint
import re
import sys


def lpc_2_json(lpc_str):
    # I deal with some lpc data. Convert them to JSON
    convert_dict = [
        ('([', '{'),
        (',])', '}'),
        ('])', '}'),

        ('({', '['),
        (',})', ']'),
        ('})', ']'),
    ]

    for old, new in convert_dict:
        lpc_str = lpc_str.replace(old, new)

    return lpc_str


def fix_json(src):
    # I have to deal with a lot of non-standard JSON.
    # Try to fix them whenever possible.

    # Fix property names missing quotes
    src = re.sub(r'([\{,]\s*)(\w+)(?=\s*:)', r'\1"\2"', src)
    return src


def json_loads(s):
    return json.loads(s, strict=False, object_pairs_hook=OrderedDict)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', nargs='?',
                        help='Input file. Default is standard input.')
    parser.add_argument('-F', '--format', type=str, default='json',
                        choices=['python', 'json', 'keys'],
                        help='Output format')
    parser.add_argument('key', nargs='*')
    options = parser.parse_args()

    if options.file and options.file != '-':
        with open(options.file, 'r') as f:
            src = f.read()
    else:
        src = sys.stdin.read()

    try:
        data = json_loads(src)
    except ValueError:
        data = None

    if data is None:
        try:
            data = json_loads(fix_json(src))
        except ValueError:
            data = None

    if data is None:
        data = json_loads(fix_json(lpc_2_json(src)))

    for key in options.key:
        try:
            data = data[key]
        except KeyError:
            try:
                data = data[int(key)]
            except (KeyError, ValueError):
                sys.exit('{0} not found'.format(key))

    fmt = options.format.lower()
    if fmt == 'keys':
        print('\n'.join(data.keys()))
    elif fmt == 'json':
        json.dump(data, sys.stdout, ensure_ascii=False, indent=4)
    else:
        pprint.pprint(data)


if __name__ == '__main__':
    main()
