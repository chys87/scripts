from __future__ import absolute_import, print_function

import os
import shutil

from . import utils


class Skel(utils.Task):
    def run(self):
        skel = '/etc/skel'
        if not os.path.isdir(skel):
            return
        for name in os.listdir(skel):
            if not name.startswith('.'):
                continue
            full = os.path.join(skel, name)
            if not os.path.isfile(full):
                continue
            if os.path.exists(os.path.join(self.env.home, name)):
                continue
            print('Copying {} to {}'.format(full, self.env.home))
            shutil.copy2(full, self.env.home)


class Shellrc(utils.Task):
    _script = r'''
if [ -r ~/.shellrc ]; then
    . ~/.shellrc
fi
:
'''

    def run(self):
        dst = os.path.join(self.env.home, '.shellrc')
        if not os.path.exists(dst):
            utils.auto_symlink(os.path.join(self.env.base, 'shellrc'), dst)
            for name in ['.bashrc', '.zshrc']:
                with open(os.path.join(self.env.home, name), 'a') as f:
                    f.write(self._script)


class DotFiles(utils.Task):
    _files = {
        'npmrc': '.npmrc',
        'pip.conf': '.pip/pip.conf',
        'tmux.conf': '.tmux.conf',
        'vimrc': '.vimrc',
    }

    def run(self):
        for name, target in self._files.items():
            dst = os.path.join(self.env.home, target)
            src = os.path.join(self.env.base, name)
            if not os.path.exists(dst):
                utils.auto_symlink(src, dst)


class VimPlugin(utils.Task):
    root = False

    _plugins = {
        'vim-neatstatus': 'https://github.com/maciakl/vim-neatstatus.git',
        'vim-localvimrc': 'https://github.com/embear/vim-localvimrc.git',
    }
    _bundles = {
        'typescript-vim': 'https://github.com/leafgarland/typescript-vim.git',
        'vim-less': 'https://github.com/groenewege/vim-less.git',
    }
    _autoloads = {
        'vim-pathogen': {
            'url': 'https://github.com/tpope/vim-pathogen.git',
            'file': 'autoload/pathogen.vim',
        },
    }

    def __init__(self, env):
        super(VimPlugin, self).__init__(env)
        self.autoloaddir = os.path.join(env.home, '.vim', 'autoload')
        self.plugindir = os.path.join(env.home, '.vim', 'plugin')
        self.bundledir = os.path.join(env.home, '.vim', 'bundle')

    def run(self):
        utils.mkdirp(self.autoloaddir)
        utils.mkdirp(self.plugindir)
        utils.mkdirp(self.bundledir)

        for name, conf in self._autoloads.items():
            self.run_item(self.autoloaddir, conf['url'], name, conf['file'])

        for name, url in self._plugins.items():
            self.run_item(self.plugindir, url, name)
        for name, url in self._bundles.items():
            self.run_item(self.bundledir, url, name)

    def run_item(self, link_dir, url, clone_name, link_file='.'):
        clone_dir = self.env.external.clone(url, clone_name,
                                            update=self.env.git_pull)

        link_target = os.path.normpath(os.path.join(clone_dir, link_file))
        link = os.path.join(link_dir, os.path.basename(link_target))
        utils.auto_symlink(link_target, link)


class Gitconfig(utils.Task):
    root = False

    def run(self):
        including_file = os.path.join(self.env.home, '.gitconfig')
        included_file = os.path.relpath(
            os.path.join(self.env.base, 'gitconfig'), self.env.home)
        try:
            with open(including_file, 'r') as f:
                content = f.read()
        except utils.FileNotFoundError:
            content = ''

        if included_file not in content:
            print('Modifying {}'.format(including_file))
            with open(including_file, 'a') as f:
                print('[include]', file=f)
                print('\tpath = {}'.format(included_file), file=f)


class InstallScripts(utils.Task):
    root = False

    _scripts = {
    }
    _remote_scripts = {
        'guess-ssh-agent': 'guess-ssh-agent.sh',
    }

    def run(self):
        bin_dir = os.path.join(self.env.home, 'bin2')

        utils.mkdirp(bin_dir)

        scripts = dict(self._scripts)
        if self.env.is_remote:
            scripts.update(self._remote_scripts)

        for link, target in scripts.items():
            link = os.path.join(bin_dir, link)
            target = os.path.join(self.env.base, target)
            if not os.path.exists(link):
                utils.auto_symlink(target, link)


class InstallBinDirs(utils.Task):
    root = False

    _dirs = {
        'node-tools': 'node-tools/bin',
        'git-tools': 'git-tools',
    }

    def run(self):
        bin_dir = os.path.join(self.env.home, 'bin.d')
        utils.mkdirp(bin_dir)

        for link, target in self._dirs.items():
            link = os.path.join(bin_dir, link)
            target= os.path.join(self.env.base, target)
            if not os.path.exists(link):
                utils.auto_symlink(target, link)
