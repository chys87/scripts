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

ECHO() {
    echo "[32;1m$@[0m" >&2
    "$@"
}

FATAL() {
    echo "[31;1m$@[0m" >&2
    exit 1
}

if [[ -z "$GIT_WORK_TREE" ]]; then
    export GIT_WORK_TREE="$(ECHO git rev-parse --show-toplevel)"
fi
if [[ -z "$GIT_DIR" ]]; then
    export GIT_DIR="$GIT_WORK_TREE/.git"
fi

master=$(ECHO git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')

cur_branch="$(sed -e 's!ref: refs/heads/!!g' "$GIT_DIR/HEAD")"
if [[ ! -f "$GIT_DIR/refs/heads/$cur_branch" ]] && [[ ! -f "$GIT_DIR/logs/refs/heads/$cur_branch" ]]; then
    FATAL "Something is wrong.  Are you not on a branch?"
fi

conf_user_name=

ensure_conf_user_name() {
    if [[ -z "$conf_user_name" ]]; then
        conf_user_name="$(ECHO git config user.name)"
    fi
}

is_my_branch() {
    if [[ "$1" == "${USERNAME:-${USER}}"/* ]]; then
        return 0
    fi

    ensure_conf_user_name
    if [[ "$1" == "$conf_user_name"/* ]]; then
        return 0
    fi

    return 1
}
