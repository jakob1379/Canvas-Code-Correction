#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [ $# -eq 0 ]
then
    # if no args find
    folders=$(find -type d -wholename "*submissions" | grep -oP "\w+.*/")
else
    folders="$@"
fi
top_dir=$PWD
for folder in $folders; do
    # Check if folder exists
    if [ ! -d "$folder" ]; then
	continue
    fi

    # Enter folder and start unzipping
    cd $folder
    if [ -f submissions*.zip ]; then
	unzip -q -n submissions*.zip -d submissions;
	rm -f submissions*.zip
    fi

    # rm zip files after unpacking
    zipCount=$(ls -1 submissions/*.zip 2>/dev/null | wc -l)
    if [ $zipCount -gt 0 ]; then
	# To extract all zips:
	for i in submissions/*.zip; do unzip -q -n "$i" -d "${i%%.zip}"; done
	rm -f submissions/*.zip
    fi

    # find files and move to top folder
    for d in submissions/*/; do
	if [ -d "__MACOSX" ]; then
	    rm -rf "__MACOSX";
	fi
	folder_count=$(find "$d"/* -maxdepth 0 -type d -print 2>/dev/null | wc -l)
	if [ "$folder_count" -gt "0" ] ; then
	    mv "$d"*/*.hpp "$d"
	    mv "$d"*/*.h "$d"
	    mv "$d"*/*.cpp "$d"
	    rm -fr "$d"*/;
	fi
    done

    cd $top_dir
done
