#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=8 sts=4 sw=4 expandtab ft=python

#
# Copyright (c) 2013, 2014, chys <admin@CHYS.INFO>
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
import os
import string
import subprocess
import sys
import threading
import time
from wsgiref.simple_server import make_server
try:
    from queue import Queue  # Python 3
except ImportError:
    from Queue import Queue  # Python 2

import markdown


DEFAULT_FILE = 'README.md'
OPEN_COMMAND = {
        'cygwin': 'cygstart',
        'linux': 'xdg-open',
        'linux2': 'xdg-open',
        }
ATTEMPT_PORTS = [80, 8000, 8080, 12345, 25054]
CSS_FILE = 'mdqp.css'
TEMPLATE = '''<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <title>$title</title>
        <style>
        $css
        </style>
    </head>
    <body>
        $main
    </body>
</html>
'''


def httpd_main(html, q):

    def wsgiapp(environ, start_response):
        headers = [('Content-Type', 'text/html; charset=utf-8'),
                ('Cache-Control', 'no-cache'),
                ]
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    for port in ATTEMPT_PORTS:
        try:
            httpd = make_server('localhost', port, wsgiapp)
        except (IOError, OSError, ):
            continue
        q.put(port)
        httpd.timeout = 10
        httpd.handle_request()
        break
    else:
        q.put(0)


def send_to_browser(html):
    open_command = OPEN_COMMAND.get(sys.platform)
    if not open_command:
        sys.exit("Don't know how to start a browser in your platform.")
    q = Queue()
    httpd_thread = threading.Thread(target=httpd_main, args=(html, q))
    httpd_thread.start()
    port = q.get()
    if port == 0:
        sys.exit("Failed to start a minimal HTTP server")
    url = 'http://localhost:{}/'.format(port)
    print('Opening {}'.format(url))
    subprocess.Popen([open_command, url])
    httpd_thread.join()


def get_default_css_file():
    exe = __file__

    # Same dir as this script
    name = os.path.join(os.path.dirname(exe), CSS_FILE)
    if os.access(name, os.R_OK):
        return name

    # Perhaps this script is run through a symlink..
    if os.path.islink(exe):
        exe = os.path.realpath(exe)
        name = os.path.join(os.path.dirname(exe), CSS_FILE)
        if os.access(name, os.R_OK):
            return name

    return None


def main():
    usage = '''Usage: %prog [options] [filename]
        default filename is {}'''.format(DEFAULT_FILE)
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-e', '--encoding', dest='encoding', default='utf-8',
                      help='Source encoding. Defaults to UTF-8.')
    parser.add_option('-c', '--css', dest='cssfile', default=None,
                      help='Specify CSS filename.')
    parser.add_option('--fix-id', dest='fixid', action='store_true',
                      default=False,
                      help='Support [text](id:tag)')
    parser.add_option('-s', '--save', dest='savefile', default=None,
                      help='Save to a file instead of opening in a browser.')
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

    cssfile = options.cssfile
    if not cssfile:
        cssfile = get_default_css_file()
    if cssfile:
        with open(cssfile, 'rb') as f:
            css = f.read().decode('utf-8')
    else:
        css = ''

    html = markdown.markdown(unictxt, output_format='html')
    html = string.Template(TEMPLATE).substitute(title=filename,
                                                css=css,
                                                main=html)
    if options.fixid:
        html = html.replace('href="id:', 'name="')

    if options.savefile:
        open(options.savefile, 'wb').write(html.encode('utf-8'))
    else:
        send_to_browser(html)


if __name__ == '__main__':
    main()
