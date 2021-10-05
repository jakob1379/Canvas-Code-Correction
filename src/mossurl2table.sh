#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [ $# -ne 1 ]
then
    echo "mossurl2table ERROR: Take only one input!"
    exit 2
else
    # Check if url is seemingly valid
    url="$1"
    substring="http://moss.stanford.edu/results"
    if [ ! -z "${url##*$substring*}" ]; then
	echo "invalid url!"
	exit 2
    fi
fi

curl -s "$url" \
    | hxnormalize -x \
    | hxselect 'table' \
    | w3m -dump -cols 2000 -T 'text/html' \
    | awk '(NR>1) {print $1,$3,$2}' \
    | sed -e 's/%//' -e 's/(//g' -e 's/)//g' \
    | sort -k 3,3 -k 1,1 -h -r
