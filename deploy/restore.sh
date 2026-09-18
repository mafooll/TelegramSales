#!/bin/sh
set -eu

name=${1:?usage: restore.sh <file inside the backups volume>}
directory=${BACKUP_DIRECTORY:-/backups}
file="$directory/$name"

[ -f "$file" ] || { echo "no such backup: $file" >&2; exit 1; }

pg_restore --clean --if-exists --no-owner --dbname="$POSTGRES_DB" "$file"
echo "restored from $file"
