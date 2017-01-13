import os
import shutil

import utils


class Skel(utils.Task):
    def run(self):
        skel = '/etc/skel'
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
    _files = [
        'tmux.conf',
        'vimrc',
    ]

    def run(self):
        for name in self._files:
            dst = os.path.join(self.env.home, '.' + name)
            src = os.path.join(self.env.base, name)
            if not os.path.exists(dst):
                utils.auto_symlink(src, dst)


class VimPlugin(utils.Task):
    root = False

    _plugins = {
        'vim-neatstatus': 'https://github.com/maciakl/vim-neatstatus.git',
    }

    def __init__(self, env):
        super().__init__(env)
        self.linkdir = os.path.join(env.home, '.vim', 'plugin')
        self.external = os.path.join(env.home, 'external')

    def run(self):
        utils.mkdirp(self.linkdir)
        utils.mkdirp(self.external)

        for name, url in self._plugins.items():
            self.run_item(name, url)

    def run_item(self, name, url):
        link = os.path.join(self.linkdir, name)
        if os.path.exists(link):
            return

        dst = os.path.join(self.external, name)
        if not os.path.exists(dst):
            utils.git_clone(url, dst)

        utils.auto_symlink(dst, link)


class Gitconfig(utils.Task):
    root = False

    def run(self):
        including_file = os.path.join(self.env.home, '.gitconfig')
        included_file = os.path.relpath(
            os.path.join(self.env.base, 'gitconfig'), self.env.home)
        try:
            with open(including_file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            content = ''

        if included_file not in content:
            print('Modifying {}'.format(including_file))
            with open(including_file, 'a') as f:
                print('[include]', file=f)
                print('\tpath = {}'.format(included_file), file=f)
