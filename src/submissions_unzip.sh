#!/bin/bash

if [ $# -ne 1 ] || [ ! -d "$1" ]
then
    echo "submissions_unzip: Needs exactly one directory"
    exit 1
fi

folder=$1

cd "$folder"

find \
    submissions/*/ -maxdepth 1 -type f -name '*.zip' \
    -exec sh -c 'unzip -q -n "{}" -d "$(dirname "{}")" && rm -rf "{}"' \;
find submissions/*/ -maxdepth 1 -type d -name '__MACOSX' -exec sh -c 'rm -rf "{}" || true' \;

# find files and move to top folder
for d in submissions/*/; do
    folder_count=$(find "$d"/* -maxdepth 0 -type d -print 2>/dev/null | wc -l)
    file_count=$(find "$d"/* -maxdepth 0 -type f -print 2>/dev/null | wc -l)
    if [ "$folder_count" -eq "1" ] && [ "$file_count" -eq "0" ]; then
	mv "$d"*/* "$d"
	rm -fr "$d"*/ || true
    fi
done
