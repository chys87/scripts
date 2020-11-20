from __future__ import absolute_import, print_function

import os
import subprocess
import sys

from . import six
from . import utils



class PackageManagerMeta(type):
    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))

        executable = getattr(result, 'executable', None)
        if executable:
            PackageManager.registry.append(result)

        return result


@six.add_metaclass(PackageManagerMeta)
class PackageManager(object):
    registry = []

    def get_installed_set(self):
        raise NotImplementedError

    def install(self, lst):
        raise NotImplementedError


class DebianPackageManager(PackageManager):
    executable = 'apt-get'
    name = 'apt'

    def get_installed_set(self):
        res = set()

        content = utils.check_popen(['dpkg', '-l'])
        for line in content.splitlines():
            try:
                res.add(line.split()[1].decode('ascii'))
            except IndexError:
                pass

        return res

    def install(self, lst):
        subprocess.check_call(['apt', 'install'] + lst)


class InstallPackages(utils.Task):
    normal_user = False

    _packages = [
        'autoconf',
        {'apt': 'build-essential'},
        'bvi',
        'ccache',
        'colordiff',
        'convmv',
        {'apt': 'universal-ctags', 'default': 'ctags'},
        'curl',
        {'apt': 'g++-multilib'},
        'git',
        {'apt': 'gcc-doc'},
        {'apt': 'glibc-doc'},
        'htop',
        {'apt': 'ipython3', 'default': 'ipython'},
        'lftp',
        'lrzsz',
        {'apt': ['manpages-dev', 'manpages-posix']},
        {'apt': 'ninja-build', 'default': 'ninja'},
        'p7zip',
        {'apt': ['p7zip-full', 'p7zip-rar']},
        {'apt': ['python3-pip']},
        {'apt': 'pkg-config'},
        {'apt': ['pyflakes3'], 'default': 'pyflakes'},
        {'apt': 'python3-yaml', 'default': 'pyyaml'},
        ['rar', 'unrar'],
        'strace',
        'tmux',
        'tree',
        'unzip',
        'valgrind',
        'zip',
        'zsh',
    ]
    _x_packages = [
        'dia',
        'gimp',
        'gitk',
        'kcachegrind',
        'pqiv',
        {'apt': ['fonts-wqy-microhei', 'fonts-wqy-zenhei']},
    ]

    def find_package_manager(self):
        for cls in PackageManager.registry:
            if utils.find_executable(cls.executable):
                return cls()
        return None

    def run(self):
        pkg_mgr = self.find_package_manager()
        if not pkg_mgr:
            print('Unsupported package manager', file=sys.stderr)
            return

        installed = pkg_mgr.get_installed_set()

        packages = self._packages
        if self.env.X:
            packages = packages + self._x_packages

        to_install = []
        for conf in packages:
            if isinstance(conf, (str, list, tuple)):
                pkg = conf
            else:
                pkg = conf.get(pkg_mgr.name) or conf.get('default')

            if isinstance(pkg, str):
                pkg_list = [pkg]
            elif isinstance(pkg, (list, tuple, set, frozenset)):
                pkg_list = pkg
            else:
                continue

            for pkg in pkg_list:
                if pkg not in installed:
                    to_install.append(pkg)

        if to_install:
            print('Installing: {}'.format(' '.join(sorted(to_install))))
            pkg_mgr.install(to_install)


class DefaultEditor(utils.Task):
    normal_user = False
    _preferred = '/usr/bin/vim.basic'

    def run(self):
        try:
            editor = os.readlink('/etc/alternatives/editor')
        except utils.FileNotFoundError:
            return

        if '/vim' in editor:
            return

        if os.access(self._preferred, os.X_OK):
            subprocess.check_call(['update-alternatives', '--set',
                                   'editor', self._preferred])
