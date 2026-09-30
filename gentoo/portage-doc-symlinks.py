#!/usr/bin/python3
# Maintain /usr/share/doc/<PN> symlinks pointing at the largest installed
# <PN>-<version> directory; the symlink is removed when no version is left.
#
# Usage:
#   portage-doc-symlinks.py <PN>   maintain the symlink for one package
#   portage-doc-symlinks.py -a     maintain symlinks for every package
#   --root DIR                     root containing usr/share/doc
#   -n, --dry-run                  print the actions without performing them
#
# Both real and dry runs print every action:
#   + link created   ~ link retargeted   - link removed
#
# --root defaults to $ROOT (or "/") when not given.

import argparse
import os
import sys
from functools import cmp_to_key

from portage.versions import (  # type: ignore[import-untyped]
    catpkgsplit,
    vercmp,
)


def split_pf(name: str) -> tuple[str, str] | None:
    """'foo-1.2-r1' -> ('foo', '1.2-r1'); None if not a valid PF."""
    cpv = catpkgsplit(name)
    if not cpv:
        return None
    pn = cpv[1]
    rest = name[len(pn) + 1:]
    if not rest:
        return None
    return pn, rest


def dir_version(entry: os.DirEntry[str]) -> tuple[str, str] | None:
    """Return (PN, version) if entry is a real versioned doc directory."""
    if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
        return None
    return split_pf(entry.name)


class DocLinks:
    def __init__(self, root: str, dry_run: bool = False) -> None:
        self.docdir = root.rstrip("/") + "/usr/share/doc"
        self.dry = dry_run

    def version_dirs(self, pn: str | None = None) -> dict[str, list[str]]:
        """Return {PN: [versions...]} (ascending) for real directories."""
        groups: dict[str, list[str]] = {}
        try:
            with os.scandir(self.docdir) as entries:
                for entry in entries:
                    parts = dir_version(entry)
                    if parts is None:
                        continue
                    name, version = parts
                    if pn is not None and name != pn:
                        continue
                    groups.setdefault(name, []).append(version)
        except (FileNotFoundError, NotADirectoryError):
            return groups
        for versions in groups.values():
            versions.sort(key=cmp_to_key(vercmp))
        return groups

    def ensure(self, pn: str, target: str | None) -> None:
        """Create/retarget/remove the <PN> symlink.

        `target` is the versioned directory name, or None to remove.
        """
        link = os.path.join(self.docdir, pn)
        prefix = "[DRY-RUN] " if self.dry else ""
        if os.path.lexists(link) and not os.path.islink(link):
            print(f"! {link} exists and is not a symlink; skipping",
                  file=sys.stderr)
            return
        if target is None:
            if os.path.islink(link):
                print(f"{prefix}- {link} (was -> {os.readlink(link)})")
                if not self.dry:
                    os.unlink(link)
            return
        if os.path.islink(link):
            current = os.readlink(link)
            if current == target:
                return
            print(f"{prefix}~ {link} -> {target} (was -> {current})")
        else:
            print(f"{prefix}+ {link} -> {target}")
        if self.dry:
            return
        tmp = os.path.join(self.docdir, f".{pn}.doclink.tmp")
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        os.symlink(target, tmp)
        os.replace(tmp, link)

    def clean_dangling(self) -> None:
        prefix = "[DRY-RUN] " if self.dry else ""
        try:
            with os.scandir(self.docdir) as entries:
                dangling = [entry.path for entry in entries
                            if entry.is_symlink()
                            and not os.path.exists(entry.path)]
        except (FileNotFoundError, NotADirectoryError):
            return
        for path in dangling:
            was = os.readlink(path)
            print(f"{prefix}- {path} (dangling, was -> {was})")
            if not self.dry:
                os.unlink(path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Maintain /usr/share/doc/<PN> symlinks pointing to "
                    "the largest installed <PN>-<version> doc directory.")
    parser.add_argument("package", nargs="?", metavar="PN",
                        help="only check this package name")
    parser.add_argument("-a", "--all", action="store_true",
                        help="check every package under the doc directory")
    parser.add_argument("--root", metavar="DIR",
                        help="root containing usr/share/doc "
                             "(default: $ROOT or /)")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="print the actions without performing them")
    args = parser.parse_args()

    if args.all == (args.package is not None):
        parser.error("specify either a package name or -a, but not both")

    root = args.root if args.root is not None else os.environ.get("ROOT", "/")
    links = DocLinks(root, args.dry_run)

    if args.all:
        groups = links.version_dirs()
        for pn in sorted(groups):
            links.ensure(pn, f"{pn}-{groups[pn][-1]}")
        links.clean_dangling()
        return

    pn = args.package
    versions = links.version_dirs(pn).get(pn, [])
    links.ensure(pn, f"{pn}-{versions[-1]}" if versions else None)


if __name__ == "__main__":
    main()
