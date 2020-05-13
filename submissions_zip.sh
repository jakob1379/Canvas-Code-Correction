#!/bin/bash

folder=$1

cd "$folder"

for i in submissions/*/; do
if [[ -n $(find "$i/"*_points.txt -cmin -30 -print 2>/dev/null) ]]
then
	trim="${i%/}"
	zip -j -q   "${i%/}.zip"  "$i""${trim#*/}".txt "$i"*.log;
fi
done

zipCount=$(ls -1 *.zip 2>/dev/null | wc -l)
if [ $zipCount -gt 0 ]; then 
	for i in submissions/; do
	zip -j -q submissions_upload.zip  "$i"*.zip;
	done

	rm submissions/*.zip
	mkdir -p upload_me/
	mv submissions_upload.zip upload_me/
fi







