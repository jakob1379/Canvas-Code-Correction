#!/bin/bash

if [ $# -ne 1 ] || [ ! -d $1 ]
then
    echo "submissions_unzip: Needs exactly one directory"
    exit 1
fi

folder=$1

cd "$folder"

if [ -f submissions*.zip ]; then
    unzip -q -n submissions*.zip -d submissions;
    rm -f submissions*.zip
fi

zipCount=$(ls -1 submissions/*.zip 2>/dev/null | wc -l)
if [ $zipCount -gt 0 ]; then
    # To extract all zips:
    for i in submissions/*.zip; do unzip -q -n "$i" -d "${i%%.zip}"; done
    rm -f submissions/*.zip
fi


# # find files and move to top folder
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
