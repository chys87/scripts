from collections import OrderedDict
import os
import pwd
import re
import subprocess


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

    if show:
        print('Symlinking {} <== {}'.format(target, link))

    os.symlink(target, link)


def mkdirp(path, show=True):
    if not os.path.isdir(path):
        if show:
            print('Mkdir {}'.format(path))
        os.makedirs(path)


def git_clone(url, dst):
    subprocess.check_call(['git', 'clone', url, dst])


def check_popen(cmd):
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    try:
        return pipe.stdout.read()
    finally:
        code = pipe.wait()
        if code != 0:
            raise subprocess.CalledProcessError(code, cmd)


class Environment:
    def __init__(self):
        self.base = self.find_git_base()
        self.home = pwd.getpwuid(os.getuid()).pw_dir

    def find_git_base(self):
        curdir = os.path.dirname(os.path.realpath(__file__))
        while curdir != '/' and not os.path.isdir(curdir + '/.git'):
            curdir = os.path.dirname(curdir)
        if curdir == '/':
            raise SysInitError('Failed to find base dir of this git repo')
        return curdir


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


class Task(metaclass=TaskMeta):
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
