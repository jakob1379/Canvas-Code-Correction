#!/bin/bash

folder="$1"
totalPath="$folder"/submissions/
week=$(basename -- "$folder")
scoreFile="$week"_scores.txt

submissionCount=$(ls -1 "$totalPath" 2>/dev/null | wc -l)

if [ $submissionCount -gt 0 ]; then

    echo "Assignment_id	Total_points	URL" >  "$scoreFile"

    total="$(ls $totalPath | wc -l)"
    num1=0

    for d in "$totalPath"/*/; do
	fileCount=$(ls -1 "$d"/*log "$d"/*txt 2>/dev/null | wc -l)
	if [ $fileCount -lt 3 ]; then
	    dir="$PWD"
	    cp -r "$folder"/code/* "$d"/
	    cd "$d"
	    python2 main.py > errors.log 2>&1
	    rm -fr {test,config.py,main.py}
	    cd "$dir"
	fi

	filename=$(basename -- "$d")
	echo -n "$filename	" >> "$scoreFile"

	points="$(cat "$d"/*_points.txt | paste -sd+ - | bc)"
	printf "%0.2f " $points >> "$scoreFile"

	url="https://absalon.ku.dk/courses/38767/assignments/99856/submissions/"
	echo -n "$url" >> "$scoreFile"
	OIFS=$IFS
	IFS='_'
	read -ra ADDR <<< "$filename"
	IFS=$OIFS

	str1="LATE"
	str2="${ADDR[1]}"
	if [ "$str1" != "$str2" ]; then
	    echo "${ADDR[1]}" >> "$scoreFile"
	else
	    echo "${ADDR[2]}" >> "$scoreFile"
	fi

	num1="$(($num1+1))"
	echo "$num1" of "$total" corrected "$week": "$filename"

    done;

else
    echo No submissions found >  "$scoreFile"
fi
