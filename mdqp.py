#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2013, chys <admin@CHYS.INFO>
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

"""Quick preview of a Markdown file.

If no filename is given, it attempts to use README.md
"""

from __future__ import print_function

import optparse
import string
import subprocess
import sys
import tempfile
import time

import markdown


DEFAULT_FILE = 'README.md'
OPEN_COMMAND = 'xdg-open'
TEMPLATE = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" \
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <title>$title</title>
    </head>
    <body>
        $main
    </body>
</html>
'''


def main():
    usage = '''Usage: %prog [options] [filename]
        default filename is {}'''.format(DEFAULT_FILE)
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-e', '--encoding', dest='encoding', default='utf-8',
                      help='Source encoding. Defaults to UTF-8.')
    (options, args) = parser.parse_args()
    if len(args) > 1:
        print('Too many filenames', file=sys.stderr)
        sys.exit(1)
    if args:
        filename = args[0]
    else:
        filename = DEFAULT_FILE

    try:
        with open(filename, 'rb') as fp:
            bintxt = fp.read()
    except IOError:
        print('Failed to read from {}'.format(filename), file=sys.stderr)
        sys.exit(1)

    try:
        unictxt = bintxt.decode(options.encoding)
    except UnicodeDecodeError:
        print('Failed to decode text from {}'.format(options.encoding),
              file=sys.stderr)
        sys.exit(1)

    html = markdown.markdown(unictxt, output_format='xhtml')
    html = string.Template(TEMPLATE).substitute(title=filename,
                                                main=html)

    tmp = tempfile.NamedTemporaryFile(prefix='markdown.', suffix='.html')
    tmp.write(html.encode('utf-8'))
    tmp.flush()

    subprocess.check_call([OPEN_COMMAND, tmp.name])
    time.sleep(1)


if __name__ == '__main__':
    main()