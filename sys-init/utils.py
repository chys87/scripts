from collections import OrderedDict
import os
import pwd
import re
import subprocess

from . import six


try:
    FileNotFoundError = FileNotFoundError
except NameError:
    FileNotFoundError = IOError


class SysInitError(Exception):
    pass


def find_executable(name):
    for path in os.environ['PATH'].split(os.pathsep):
        full = os.path.join(path, name)
        if os.access(full, os.X_OK):
            return full
    return None


def auto_symlink(real, link, show=True):
    linkdir = os.path.dirname(link)

    mkdirp(linkdir, show=show)

    if real.split('/')[:2] == linkdir.split('/')[:2]:
        target = os.path.relpath(real, linkdir)
    else:
        target = real

    if os.path.exists(link):
        try:
            oldtarget = os.readlink(link)
        except OSError:
            raise SysInitError('{} exists and is not a symlink'.format(link))
        if os.path.abspath(oldtarget) != os.path.abspath(target):
            raise SysInitError('Inconsistent target for {}:\nOld: {}\nNew: {}'
                               .format(link, oldtarget, target))
        return

    if show:
        print('Symlinking {} <== {}'.format(target, link))

    os.symlink(target, link)


def mkdirp(path, show=True):
    if not os.path.isdir(path):
        if show:
            print('Mkdir {}'.format(path))
        os.makedirs(path)


def unlink(path, show=True):
    if os.path.lexists(path):
        if show:
            print('Unlinking {}'.format(path))
        os.unlink(path)


def canonicalize_git_url(url):
    return re.sub(r'^git@github.com:', 'https://github.com/', url)


def git_clone(url, dst, update=True):
    if os.path.isdir(dst):
        oldurl = check_popen(['git', 'ls-remote', '--get-url', 'origin'],
                             cwd=dst)
        # "git remote get-url origin" is better, but only for git >=2.7
        oldurl = oldurl.strip().decode()
        if canonicalize_git_url(url) != canonicalize_git_url(oldurl):
            raise SysInitError('Inconsistent URL for {}\nOld: {}\nNew: {}'
                               .format(dst, oldurl, url))
        if update:
            print('Updating {}'.format(dst))
            subprocess.check_call(['git', 'pull'], cwd=dst)
    else:
        subprocess.check_call(['git', 'clone', url, dst])


def check_popen(cmd, **kwargs):
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, **kwargs)
    try:
        return pipe.stdout.read()
    finally:
        code = pipe.wait()
        if code != 0:
            raise subprocess.CalledProcessError(code, cmd)


class Environment(object):
    def __init__(self, args):
        self.base = self.find_git_base()
        self.home = os.path.realpath(pwd.getpwuid(os.getuid()).pw_dir)
        self.X = args.X
        self.git_pull = args.git_pull
        self.is_remote = self.is_remote_machine()

        self._external = None

    def find_git_base(self):
        curdir = os.path.dirname(os.path.realpath(__file__))
        while curdir != '/' and not os.path.isdir(curdir + '/.git'):
            curdir = os.path.dirname(curdir)
        if curdir == '/':
            raise SysInitError('Failed to find base dir of this git repo')
        return curdir

    def is_remote_machine(self):
        return 'SSH_CLIENT' in os.environ

    @property
    def external(self):
        if not self._external:
            external_dir = os.path.join(self.home, 'external')
            mirror_base = os.path.join(external_dir, 'awesome-mirrors')
            if os.path.isdir(mirror_base):
                self._external = ExternalFromMirror(external_dir, mirror_base)
            else:
                self._external = ExternalDir(external_dir)

        return self._external


class ExternalDir(object):
    def __init__(self, external_dir):
        self.external = external_dir
        mkdirp(external_dir)

    def clone(self, url, name, update=True):
        return self.create_from_git(url, name, update)

    def create_from_git(self, url, name, update=True):
        path = os.path.join(self.external, name)
        git_clone(url, path, update)
        return path


class ExternalFromMirror(ExternalDir):
    def __init__(self, external_dir, mirror_base):
        super(ExternalFromMirror, self).__init__(external_dir)
        self.mirror_base = mirror_base

        self._updated_mirror = False

    def clone(self, url, name, update=True):
        if update and not self._updated_mirror:
            print('Updating {}'.format(self.mirror_base))
            subprocess.check_call(['git', 'pull'], cwd=self.mirror_base)
            self._updated_mirror = True

        target = os.path.join(self.mirror_base, name)
        if os.path.isdir(target):
            path = os.path.join(self.external, name)
            auto_symlink(target, path)
            return path
        else:
            return self.create_from_git(url, name, update)


class TaskMeta(type):
    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))
        if name != 'Task':
            if name.startswith('Task'):
                task_name = name[:4]
            else:
                task_name = name
            task_name = re.sub('(?<=[a-z])(?=[A-Z])', r'_', task_name)
            task_name = task_name.lower()
            Task.registry[task_name] = result
        return result


@six.add_metaclass(TaskMeta)
class Task(object):
    __slots__ = 'env',
    registry = OrderedDict()
    normal_user = True
    root = True

    def __init__(self, env):
        self.env = env

    def precheck(self):
        return True

    def run(self):
        raise NotImplementedError
