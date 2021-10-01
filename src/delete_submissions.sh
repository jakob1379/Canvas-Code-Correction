#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# -depth enables processing of files before dir
find -mindepth 3 -maxdepth 3 -wholename "*/submissions/*" | xargs /usr/bin/rm -rf
