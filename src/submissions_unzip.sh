#!/bin/bash

if [ $# -ne 1 ] || [ ! -d "$1" ]
then
    echo "submissions_unzip: Needs exactly one directory"
    exit 1
fi

folder=$1

cd "$folder"

find 'submissions/' \
     -maxdepth 2 \
     -type f \
     -name '*.zip' \
     -exec sh -c 'unzip -q -n "{}" -d "$(dirname "{}")" && rm -rf "{}"' \;

find 'submissions/' \
     -maxdepth 2 \
     -type d \
     -name '__MACOSX' \
     -exec sh -c 'rm -rf "{}" || true' \;

# find files and move to top folder
for d in submissions/*/; do
    folder_count=$(find "$d"/* -maxdepth 0 -type d -print 2>/dev/null | wc -l)
    file_count=$(find "$d"/* -maxdepth 0 -type f -print 2>/dev/null | wc -l)
    # Check if folder only has a single folder
    if [ "$folder_count" -eq "1" ] && [ "$file_count" -eq "0" ]; then
	# Only touch files that are writable
	for thing in $(find "$d" -mindepth 2 -maxdepth 2); do
	    if [[ "$(stat -c "%A" "$thing")" =~ 'w' ]]; then
		destination=$(rev <(echo "$thing") | cut -d '/' -f 3- | rev)
		mv "$thing" "$destination/"
		rm -fr "$thing"
	    fi
	done
    fi
done
