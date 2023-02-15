#!/usr/bin/with-contenv bash
# shellcheck shell=bash

PUID=${PUID:-911}
PGID=${PGID:-911}

groupmod -o -g "$PGID" abc
usermod -o -u "$PUID" abc

echo '
-------------------------------------
GID/UID
-------------------------------------'
echo "
User uid:    $(id -u abc)
User gid:    $(id -g abc)
-------------------------------------
"

chown -R abc:abc /workdir

su -c "cd /workdir && python3 main.py" abc