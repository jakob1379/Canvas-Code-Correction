#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

find -mindepth 3 -maxdepth 3 -wholename "*/submissions/*" -exec /usr/bin/rm -rf {} \;
