#!/usr/bin/python3

import argparse
import glob
import os
import subprocess as sp
import sys

from portage.output import EOutput
import yaml


class AutoPatcher:
    def __init__(self, args):
        self.patch_overlay = args.patch_overlay
        self.args = args
        self.inclusions = self._inclusions()
        self._eout = EOutput()

        self.einfo = self._eout.einfo
        self.eerror = self._eout.eerror

    def _inclusions(self):
        filename = os.path.join(self.patch_overlay, 'inclusions.yaml')
        try:
            with open(filename) as f:
                yaml_text = f.read()
        except FileNotFoundError:
            return {}
        else:
            return yaml.load(yaml_text)

    def find_patches(self, prefix):
        return (glob.glob('{}/{}.*.patch'.format(self.patch_overlay, prefix)) +
                glob.glob('{}/{}.*.diff'.format(self.patch_overlay, prefix)))

    def find_all_patches(self, prefix, dirname):
        for patch in self.find_patches(prefix):
            yield (patch, dirname)
        inclusions = self.inclusions.get(prefix)
        if inclusions:
            for subprefix, subdir in inclusions.items():
                yield from self.find_all_patches(
                    subprefix, os.path.join(dirname, subdir))

    def make_prefixes(self):
        args = self.args
        base_prefix = '{}.{}'.format(args.category, args.pn)
        yield base_prefix
        yield base_prefix + ':' + args.slot

        pv_parts = args.pv.split('.')
        for i in range(1, len(pv_parts) + 1):
            yield base_prefix + '-' + '.'.join(pv_parts[:i]) + '!'

    def auto_apply_patch(self, dst_dir, patch):
        tag_file = os.path.join(dst_dir,
                                '.autopatched.' + os.path.basename(patch))
        if os.path.exists(tag_file):
            return

        self.einfo('Applying patch {} to {}'.format(patch, dst_dir))

        for level in ('-p1', '-p0'):
            code = sp.call(['patch', '--dry-run', '-f', '-d' + dst_dir, level],
                           stdin=open(patch), stdout=sp.DEVNULL)
            if code == 0:
                code = sp.call(['patch', '-f', '-d' + dst_dir, level],
                               stdin=open(patch))
                if code == 0:
                    open(tag_file, 'w').close()
                    return
                else:
                    break

        # For some packages, e.g. libpng, abi directories contain no
        # source files
        if '-abi_' in dst_dir:
            self.einfo("Failed to apply patch {} to {}, "
                       "but probably that's not important".format(
                           patch, dst_dir))
        else:
            self.eerror("Failed to apply patch {} to {}".format(
                patch, dst_dir))
            sys.exit(1)

    def apply_patch(self, basedir, subdir, patch):
        self.auto_apply_patch(os.path.join(basedir, subdir), patch)

        for altdir in glob.glob('{}-abi_*'.format(basedir)):
            self.auto_apply_patch(os.path.join(altdir, subdir), patch)

    def run(self):
        s = self.args.s
        for prefix in self.make_prefixes():
            for patch, subdir in self.find_all_patches(prefix, '.'):
                if s:
                    self.apply_patch(s, subdir, patch)
                else:
                    print(patch, subdir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--patch-overlay', required=True)
    parser.add_argument('--category', required=True)
    parser.add_argument('--pn', required=True)
    parser.add_argument('--pv', required=True)
    parser.add_argument('--slot', required=True)
    parser.add_argument('--s', required=False)
    args = parser.parse_args()

    AutoPatcher(args).run()


if __name__ == '__main__':
    main()
