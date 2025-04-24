import datetime
import os
import subprocess
import sys

from . import utils



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
                res.add(line.split()[1].split(b':')[0].decode('ascii'))
            except IndexError:
                pass

        return res

    def install(self, lst):
        subprocess.check_call(['apt', 'install'] + lst)


class InstallPackages(utils.Task):
    normal_user = False

    _packages = [
        {'apt': 'libabsl-dev', 'default': 'abseil-cpp'},
        'autoconf',
        'autoconf-archive',
        {'apt': 'bind9-dnsutils'},
        {'apt': 'build-essential'},
        {'apt': ['binutils-doc', 'binutils-multiarch']},
        'bvi',
        'ccache',
        ['clang', 'clang-format', 'lld'],
        'colordiff',
        'convmv',
        'curl',
        {'apt': 'cython3', 'default': 'cython'},
        {'apt': 'fd-find', 'default': 'fd'},
        'fzf',
        'git',
        'git-lfs',
        {'apt': 'gcc-doc'},
        {'apt': 'glibc-doc'},
        'htop',
        {'apt': 'info'},
        {'apt': 'ipython3', 'default': 'ipython'},
        'lftp',
        'lrzsz',
        'lsof',
        {'apt': 'make-doc'},
        {'apt': ['manpages-dev', 'manpages-posix']},
        'moreutils',
        'neovim',
        {'apt': 'ninja-build', 'default': 'ninja'},
        {'apt': ['7zip', '7zip-rar'], 'default': 'p7zip'},
        'patchutils',
        {'apt': 'pax-utils'},
        {'apt': ['python3-pip', 'python3-venv']},
        {'apt': 'pkg-config'},
        'psmisc',
        {'apt': ['pyflakes3'], 'default': 'pyflakes'},
        {'apt': 'python3-yaml', 'default': 'pyyaml'},
        {'apt': 'python3-pynvim', 'default': 'pynvim'},
        'rsync',
        'strace',
        'tmux',
        'tree',
        'unrar',
        'unzip',
        'valgrind',
        {'apt': 'vim-nox', 'default': 'vim'},
        'zip',
        'zsh',
        'zstd',
    ]
    _x86_packages = [
        {'apt': 'g++-multilib'},
        #{'apt': 'g++-aarch64-linux-gnu'},
        'rar',
    ]
    _aarch64_packages = [
        {'apt': 'g++-multilib-x86-64-linux-gnu'},
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
        if os.uname().machine == 'x86_64':
            packages = packages + self._x86_packages
        elif os.uname().machine == 'aarch64':
            packages = packages + self._aarch64_packages

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
    _preferred = ['/usr/bin/vim.nox',
                  '/usr/bin/vim.basic']

    def run(self):
        try:
            editor = os.readlink('/etc/alternatives/editor')
        except utils.FileNotFoundError:
            return

        if '/vim' in editor:
            return

        for name in self._preferred:
            if os.access(name, os.X_OK):
                subprocess.check_call(['update-alternatives', '--set',
                                       'vim', name])
                subprocess.check_call(['update-alternatives', '--set',
                                       'editor', name])
                break


class RemoveLdPreload(utils.Task):
    normal_user = False

    def run(self):
        path = '/etc/ld.so.preload'
        try:
            st = os.stat(path)
        except FileNotFoundError:
            return

        if st.st_size == 0:
            return

        print(f'Removing {path}')
        t = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        os.rename(path, f'{path}.bak{t}')
