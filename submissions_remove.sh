#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [ $# -lt 1 ]
then
    # rm -rfi Week*/submissions/*/
    rm -rf Week1-2/submissions/*/
elif [ -d "$1" ]
then
     rm -rf $(basename "$1")/submissions/*/
fi
