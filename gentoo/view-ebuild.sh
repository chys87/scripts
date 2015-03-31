#! /bin/bash
# -*- coding: utf-8 -*-
# vim:ts=4 sts=4 sw=4 expandtab

#
# Copyright (c) 2009, 2010, 2011, 2012, 2013, chys <admin@CHYS.INFO>
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
#   Neither the name of chys <admin@CHYS.INFO> nor the names of other
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

usage() {
	cat >&2 << EOF
Usage: ${0##*/} [-c] [<category>/]<package>[-<version>]

View an ebuild file in the Gentoo portage tree.
You must have app-portage/eix installed to run this script.

-i      View the lastest of installed versions (if any)
-c      View ChangeLog instead of ebuild
The pager is view or \$PAGER or less.
EOF
	exit ${1:-1}
}

shopt -s nullglob extglob
PORTDIRS='a'
PACKAGE=
VIEW_CHANGELOG=0
VIEW_INSTALLEDVER=0
# getopt and getopts suck! Parse the arguments ourselves
for o; do
    if [[ "$o" == '--help' ]]; then
        usage 0
	elif [[ "${o:0:1}" = '-' ]]; then
		for ((i=1; i<${#o}; ++i)); do
			case "${o:$i:1}" in
				c)	VIEW_CHANGELOG=1;;
				g)	PORTDIRS='g';;
				i)	VIEW_INSTALLEDVER=1;;
				l)	PORTDIRS='l';;
                h) usage 0;;
				*)	usage;;
			esac
		done
	elif [[ -z "$PACKAGE" ]]; then
		PACKAGE="$o"
	else
		echo "Too many arguments: $o" >&2
		exit 1
	fi
done

PORTDIRS="$(portageq repositories_configuration / | sed -n -e '/^location =/s/^location = \(.*\)/\1/p')"

tmp="$PACKAGE"
PACKAGE="${tmp%%-[0-9]*}"
VERSION="${tmp:$((1+${#PACKAGE}))}"
GLOBVER="${VERSION:-[0-9]*}"
unset -v tmp

if [[ -z "$PACKAGE" ]]; then
    usage
fi

existany() {
	test $# != 0
}


# Sort a number of Gentoo package versions,
# and return the latest in LATEST_VERSION
# For example: latest_version 2.0.0.2_rc2_p3-r1 2.0.0.3_beta1
latest_version () {
	if (( $# == 1 )); then
		LATEST_VERSION="$1"
	else
		local sorted
		# versionsort is part of eix
		sorted=$(versionsort "$@") || exit 1
		LATEST_VERSION="${sorted##*$'\n'}"
	fi
}



if [ "$VIEW_INSTALLEDVER" != 0 ]; then

	findinstalledpackage () {
		[ $# = 0 ] && return 1
		local g=("${@#/var/db/pkg/}")
		g=("${g[@]%/}")
		local f=("${g[@]%-[0-9]*}")
		local i x
		for x in "${f[@]}"; do
			if [ "$x" != "${f[0]}" ]; then
				printf '%s\n' 'Ambiguous package name:' "${g[@]}" >&2
				exit 1
			fi
		done
		CATEGORY="${f[0]%/*}"
		BNAME="${f[0]#*/}"
		return 0
	}

	CATEGORY=
	BNAME=
	# Do NOT quote $PACKAGE. It can contain wildcards
	if [[ "$PACKAGE" == +([^/]) ]]; then # "Naked" package name
		findinstalledpackage /var/db/pkg/*/$PACKAGE-$GLOBVER/ ||
		findinstalledpackage /var/db/pkg/*/*$PACKAGE*-$GLOBVER/
	elif [[ "$PACKAGE" == +([^/])/+([^/]) ]]; then
		findinstalledpackage /var/db/pkg/$PACKAGE-$GLOBVER/ ||
		findinstalledpackage /var/db/pkg/*$PACKAGE*-$GLOBVER/
	fi
	if [ -z "$CATEGORY" ] || [ -z "$BNAME" ]; then
		echo "Bad installed package name: $PACKAGE${VERSION:+-$VERSION}." >&2
		exit 1
	fi
	f=("/var/db/pkg/$CATEGORY/$BNAME"-$GLOBVER/)
	f=("${f[@]##*/"$BNAME"-}")
	latest_version "${f[@]%/}"
	FNAME="/var/db/pkg/$CATEGORY/$BNAME-$LATEST_VERSION/$BNAME-$LATEST_VERSION.ebuild"
else

	findpackage () {
		local pkgs=()
		local o s t
		for o in $PORTDIRS; do
			for s in "$o"/$1; do
				# Add to pkgs if not already present
				local present=
				for t in "${pkgs[@]}"; do
					[ "$t" = "${s%/*}" ] && present=1
				done
				[ -z "$present" ] && pkgs+=("${s%/*}")
			done
		done
		# If some are installed and some are not, choose the installed
		if ((${#pkgs[@]} >= 2)); then
			local installedpkgs=()
			for s in "${pkgs[@]}"; do
				local bname="${s##*/}"
				local t="${s%/*}"
				local category="${t##*/}"
				if existany /var/db/pkg/"$category"/"$bname"-[0-9]*/; then
					installedpkgs+=("$s")
				fi
			done
			if ((${#installedpkgs[@]}==1)); then
				pkgs=("$installedpkgs")
			fi
		fi
		# Number still not right?
		case "${#pkgs[@]}" in
			0)	return 1;;
			1)	PACKAGEDIR="${pkgs[0]}"; return 0;;
			*)
				exec >&2
				echo 'Ambiguous package name:'
				for s in "${pkgs[@]}"; do
					local bname="${s##*/}"
					s="${s%/*}"
					local category="${s##*/}"
					local overlay="${s%/*}"
					if [ -f "$overlay/profiles/repo_name" ]; then
						overlay="$(<"$overlay/profiles/repo_name")"
					fi
					echo "$category/$bname [$overlay]"
				done
				exit 1;;
		esac
	}

	PACKAGEDIR=
	if [[ "$PACKAGE" == +([^/]) ]]; then # "Naked" package name
		findpackage "!(profiles|Documentation|eclass|licenses|sets|cross-*)/$PACKAGE/*-$GLOBVER.ebuild" ||
		findpackage "!(profiles|Documentation|eclass|licenses|sets|cross-*)/*$PACKAGE*/*-$GLOBVER.ebuild"
	elif [[ "$PACKAGE" == +([^/])/+([^/]) ]]; then
		findpackage "$PACKAGE/*-$GLOBVER.ebuild" || findpackage "*$PACKAGE*/*-$GLOBVER.ebuild"
	fi

	if [ -z "$PACKAGEDIR" ]; then
		echo "Bad package name: $PACKAGE${VERSION:+-$VERSION}" >&2
		exit 1
	fi

	if [ "$VIEW_CHANGELOG" != 0 ]; then
		FNAME="$PACKAGEDIR/ChangeLog"
	else
		bname="${PACKAGEDIR##*/}"
		f=("$PACKAGEDIR/$bname"-$GLOBVER.ebuild)
		f=("${f[@]##*/"$bname"-}")
		latest_version "${f[@]%.ebuild}"
		FNAME="$PACKAGEDIR/$bname-$LATEST_VERSION.ebuild"
	fi
fi

exec view "$FNAME"
# Don't quote PAGER
exec ${PAGER:-less} "$FNAME"
