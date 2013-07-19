#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2013, chys <admin@CHYS.INFO>
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
#   Neither the name of chys <admin@CHYS.INFO> nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Calculate or verify the last digit of an
18-digit Chinese ID (second-generation ID) number.

Usage: idfinal <17or18digits> ...
"""

from __future__ import print_function

import sys


def calculate(s):
    '''Given the first 17 digits, return the last digit as a string.

    If something is wrong, return None.
    '''
    if len(s) == 17 and set(s).issubset('0123456789'):
        n = sum(map(lambda a,b: a * (ord(b) - ord('0')), \
                (7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2), s)) % 11
        return '10X98765432'[n]
    else:
        return None


def main():

    if len(sys.argv) < 2 or sys.argv[1] == '--help':
        print(__doc__)
        sys.exit(0)

    err = 0

    for s in sys.argv[1:]:
        if len(s) == 17:
            x = calculate(s)
            if x:
                print(s + x)
            else:
                print('Invalid: ', s + '?', file=sys.stderr)
                err = 1
        else:
            x = calculate(s[:17])
            if s == s[:17] + x:
                print('Valid: ', s)
            else:
                print('Invalid: ', s, file=sys.stderr)
                err = 1
    sys.exit(err)


if __name__ == '__main__':
	main()
