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
    echo "ERROR: Need a valid path"
fi

rm -rf $folder
