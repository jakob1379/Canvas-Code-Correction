#!/bin/bash

folder=$1

cd "$folder"
mkdir -p submissions/


if [ -f submissions*.zip ]; then
    unzip -q -n submissions*.zip -d submissions;
    rm submissions*.zip
fi

zipCount=$(ls -1 submissions/*.zip 2>/dev/null | wc -l)
if [ $zipCount -gt 0 ]; then
    # To extract all zips:
    for i in submissions/*.zip; do unzip -q -n "$i" -d "${i%%.zip}"; done
    rm submissions/*.zip
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
	rm -r "$d"*/;
    fi
done
