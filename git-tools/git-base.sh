#!/bin/bash

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
