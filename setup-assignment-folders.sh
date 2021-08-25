#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

assignmentNames=$(python download_submissions.py -l | grep -P ' - ' | sed 's/ - //')

for name in $assignmentNames; do
    echo "$name"
    mkdir -p "$name/code"
done
