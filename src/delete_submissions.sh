#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# -depth enables processing of files before dir
to_delete=$(find -mindepth 3 -maxdepth 3 -wholename "*/submissions/*")

for f in $to_delete;do
    rm -rf "$f" > /dev/null 2>&1  || echo "Cannot delete: $f"
done
