#!/bin/bash

#    git pre-commit hook, checking for filename and content encoding
#    Copyright (C) 2014, chys <admin@CHYS.INFO>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This file is modified and extended from git's sample pre-commit hoook.

set -e

if git rev-parse --verify HEAD >/dev/null 2>&1
then
	against=HEAD
else
	# Initial commit: diff against an empty tree object
	against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# Redirect output to stderr.
exec 1>&2

# Reject non-ascii filenames
if test $(git diff --cached --name-only --diff-filter=AR -z $against |
	  LC_ALL=C tr -d '[ -~]\0' | wc -c) != 0
then
	echo "Error: Attempt to add a non-ascii file name."
	exit 1
fi

TEXT_FILE_EXTENSIONS=(
	c
	cpp
	css
	h
	hpp
	htm
	html
	js
	md
	pat
	py
	sh
	txt
)

is_text_file() {
	ext="${1##*.}"
	for txt_ext in "${TEXT_FILE_EXTENSIONS[@]}"; do
		if [ "X$ext" = "X$txt_ext" ]; then
			return 0
		fi
	done
	return 1
}

# Check text file encoding
git diff --cached --name-only --diff-filter=AM $against | (
	exit_code=0
	while read -r filename; do
		if is_text_file "$filename"; then
			if ! iconv -f utf-8 -t utf-8 "$filename" &>/dev/null; then
				echo "Error: $filename is not encoded in UTF-8."
				exit_code=1
			fi
		fi
	done
	exit $exit_code
)


# If there are whitespace errors, print the offending file names and fail.
#exec git diff-index --check --cached $against --
