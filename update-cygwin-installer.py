#!/usr/bin/env python

from __future__ import print_function

import os
import re
import sys
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen


def get_installation_dir():
    try:
        with open('/Cygwin.bat') as f:
            content = f.read().replace('\r\n', '\n')
        match = re.search(r'^chdir ([A-Z]:\\.*)$', content, re.M)
        if not match:
            return None

        dos_dir = match.group(1)
        cyg_dir = '/cygdrive/' + dos_dir[0].lower() + \
                  dos_dir[2:].replace('\\', '/')

        if os.path.basename(cyg_dir) == 'bin':
            cyg_dir = os.path.dirname(cyg_dir)

        if os.stat(cyg_dir).st_ino != os.stat('/').st_ino:
            return None

        return cyg_dir

    except (IOError, OSError):
        return None


def yield_dirs(cyg_dir):
    p = cyg_dir.rstrip(os.sep)
    while True:
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
        yield p


def get_installer(base_name, cyg_dir):
    try_names = [base_name, 'cygwin-' + base_name]

    for path in yield_dirs(cyg_dir):
        for try_name in try_names:
            installer = os.path.join(path, try_name)
            if os.path.isfile(installer):
                return installer

    return None


def download(url, installer):
    obj = urlopen(url)
    content = obj.read()
    try:
        content_type = obj.info().get_content_type()  # Py3k
    except AttributeError:
        content_type = obj.info().gettype()
    if content_type != 'application/octet-stream':
        dump_file = '/tmp/update-cygwin-installer-dump'
        with open(dump_file, 'wb') as f:
            f.write(content)
        sys.exit('Got {}; dumped to {}'.format(content_type, dump_file))
    with open(installer, 'wb') as f:
        f.write(content)


def main():
    if sys.platform != 'cygwin':
        sys.exit('This script runs only in Cygwin')

    cyg_dir = get_installation_dir()
    if not cyg_dir:
        sys.exit('Failed to determine Cygwin installation dir')

    # Python doc says this is more reliable than platform.architecture()
    if sys.maxsize > 2 ** 32:
        base_name = 'setup-x86_64.exe'
    else:
        base_name = 'setup-x86.exe'

    installer = get_installer(base_name, cyg_dir)
    if not installer:
        sys.exit('Failed to locate an installer')

    url = 'http://cygwin.com/' + base_name

    print('Downloading {} to {}'.format(url, installer))
    download(url, installer)


if __name__ == '__main__':
    main()
