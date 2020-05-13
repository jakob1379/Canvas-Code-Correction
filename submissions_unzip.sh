#!/bin/bash

folder=$1

cd "$folder"

mkdir -p submissions/

unzip -q -n submissions*.zip -d submissions;
rm submissions*.zip 


# To extract all zips:
for i in submissions/*.zip; do unzip -q -n "$i" -d "${i%%.zip}"; done
rm submissions/*.zip

# # find files and move to top folder
for d in submissions/*/; do
	folder_count=$(find "$d"/* -maxdepth 0 -type d | wc -l)
	if [ $folder_count -gt 0 ] ; then
		mv "$d"/*/*.hpp "$d"
		mv "$d"/*/*.h "$d"
		mv "$d"/*/*.cpp "$d"
		rm -r "$d"/*/;
	fi

done