#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [ $# -lt 1 ]
then
    folder=Week*/submissions/*/
elif [ $# -eq 1 ] && [ -d $1 ]
then
     folder=$1
else
    echo "ERROR: Takes at most one argument!"
fi

rm -rf $folder
