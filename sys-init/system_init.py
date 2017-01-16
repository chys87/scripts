import os
import subprocess
import sys

import utils



class PackageManagerMeta(type):
    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))

        executable = getattr(result, 'executable', None)
        if executable:
            PackageManager.registry.append(result)

        return result


class PackageManager(metaclass=PackageManagerMeta):
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
        subprocess.check_call(['aptitude', 'install'] + lst)


class InstallPackages(utils.Task):
    normal_user = False

    _packages = [
        'autoconf',
        {'apt': 'build-essential'},
        'bvi',
        'ccache',
        'convmv',
        {'apt': 'glibc-doc'},
        'htop',
        'ipython',
        {'apt': 'ipython3'},
        'lftp',
        {'apt': ['manpages-dev', 'manpages-posix']},
        'p7zip',
        {'apt': 'p7zip-full'},
        {'apt': 'pkg-config'},
        {'apt': ['pyflakes', 'pyflakes3'], 'default': 'pyflakes'},
        ['rar', 'unrar'],
        'strace',
        'tmux',
        'tree',
        'unzip',
        'zip',
        'zsh',
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

        to_install = []
        for conf in self._packages:
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