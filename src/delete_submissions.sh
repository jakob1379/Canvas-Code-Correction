#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# -depth enables processing of files before dir
to_delete=$(find -mindepth 3 -maxdepth 3 -wholename "*/submissions/*")

for f in $to_delete;do
    rm -rf "$f" || true #echo "Cannot delete: $f"
done
