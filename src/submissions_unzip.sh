#!/bin/bash

if [ $# -ne 1 ] || [ ! -d "$1" ]
then
    echo "submissions_unzip: Needs exactly one directory"
    exit 1
fi

folder=$1

cd "$folder"

# zipCount=$(ls -1 submissions/*.zip 2>/dev/null | wc -l)
# if [ $zipCount -gt 0 ]; then
#     # To extract all zips:
#     for i in submissions/*.zip; do
#	unzip -q -n "$i" -d "${i%%.zip}";
#     done
#     rm -f submissions/*.zip
# fi
find \
    -wholename 'submissions/*/*.zip' \
    -exec sh -c 'unzip -q -n "{}" -d "$(dirname "{}")" && rm -rf "{}"' \;

# find files and move to top folder
for d in submissions/*/; do
    folder_count=$(find "$d"/* -maxdepth 0 -type d -print 2>/dev/null | wc -l)
    file_count=$(find "$d"/* -maxdepth 0 -type f -print 2>/dev/null | wc -l)
    if [ "$folder_count" -eq "1" ] && [ "$file_count" -eq "0" ]; then
	mv "$d"*/* "$d"
	rm -fr "$d"*/;
    fi
done
