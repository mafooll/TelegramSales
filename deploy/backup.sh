#!/bin/sh
set -eu

directory=${BACKUP_DIRECTORY:-/backups}
interval=${BACKUP_INTERVAL:-86400}
keep=${BACKUP_KEEP_DAYS:-14}

mkdir -p "$directory"

dump() {
	name="$directory/$POSTGRES_DB-$(date -u +%Y%m%d-%H%M%S).dump"
	if pg_dump --format=custom --compress=9 --file="$name.part"; then
		mv "$name.part" "$name"
		echo "backup done: $name ($(du -h "$name" | cut -f1))"
	else
		rm -f "$name.part"
		echo "backup failed" >&2
		return 1
	fi
	find "$directory" -name "$POSTGRES_DB-*.dump" -mtime "+$keep" -print -delete
}

if [ "${BACKUP_ONCE:-false}" = "true" ]; then
	dump
	exit 0
fi

while true; do
	dump || true
	sleep "$interval"
done
