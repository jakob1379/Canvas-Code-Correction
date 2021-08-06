#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

assignments=$(python download_submissions.py -l \
		  | grep -P ' - ' | sed 's/ - //')

for line in $assignments; do
    mkdir -p "$line/code"
done

echo "$assignments"
