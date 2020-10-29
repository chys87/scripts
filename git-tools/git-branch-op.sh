#!/bin/bash
#
# Copyright (c) 2020, chys <admin@CHYS.INFO>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#   Neither the name of chys <admin@CHYS.INFO> nor the names of other
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# This script assumes you work on a collaborated git repository, and that
# your repository has a convention that everybody's branches starts with
# "USERNAME/"
#
# auto-push (ap): Push a branch, creating one on the remote end if necessary
# rebase-master (reb): Sync master with origin, and rebase current branch

set -e

. "$(dirname "$0")"/git-base.sh

echo "Current branch: $cur_branch"

if [[ "$cur_branch" == "master" ]]; then
    FATAL "Cannot operate on master"
fi

if ! is_my_branch "$cur_branch"; then
    FATAL "Not your branch"
fi

case "${0##*/git-}" in
    auto-push|ap)
        if fgrep -q "[branch \"$cur_branch\"]" "$GIT_DIR/config"; then
            ECHO git push "$@"
        else
            ECHO git push -u origin "$cur_branch" "$@"
        fi
        ;;
    rebase-master|reb)
        ECHO git checkout master
        ECHO git pull
        ECHO git checkout "$cur_branch"
        ECHO git rebase master
        ;;
    *)
        echo "Unrecognized command: $0" >&2
        ;;
esac
