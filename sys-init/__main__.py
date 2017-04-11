#!/usr/bin/env python3

from __future__ import absolute_import, print_function

import argparse
import os
import sys

from . import system_init
from . import user_init
from . import utils


def main():
    registry = utils.Task.registry

    has_x = bool(os.environ.get('DISPLAY'))

    parser = argparse.ArgumentParser()
    parser.add_argument('-X', action='store_true', default=has_x,
                        help='Install X related packages')
    parser.add_argument('--no-X', action='store_false', dest='X',
                        help="Don't install X related packages")
    parser.add_argument('--no-git-pull', action='store_false', dest='git_pull',
                        default=True, help="Don't run git pull")
    parser.add_argument('tasks', metavar='TASK', nargs='*',
                        help='Valid values: {}'.format(
                            ' '.join(registry.keys())))
    args = parser.parse_args()

    task_id_list = args.tasks
    if task_id_list:
        task_cls_list = [registry[task_id] for task_id in task_id_list]
    else:
        task_cls_list = list(registry.values())

    env = utils.Environment(args)

    if os.getuid() == 0:
        task_cls_list = [cls for cls in task_cls_list if cls.root]
    else:
        task_cls_list = [cls for cls in task_cls_list if cls.normal_user]

    tasks = [cls(env) for cls in task_cls_list]

    for task in tasks:
        if not task.precheck():
            sys.exit(1)

    for task in tasks:
        task.run()


if __name__ == '__main__':
    main()
