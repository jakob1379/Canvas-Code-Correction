#!/bin/bash

displayUsage() {
    echo '
<>  angle brackets for required parameters: ping <hostname>
[]  square brackets for optional parameters: mkdir [-p] <dirname>
... ellipses for repeated items: cp <source1> [source2…] <dest>
 |  vertical bars for choice of items: netstat {-t|-u}

usage:  name <operation> [...]
operations:
    correct {-h help} shows this dialogue
    correct {-a always} always corect assigments
    correct {-p paralllel} run in parallel

'
}
always='no'
verbose=false
parallel=false
show_time=false
while getopts ":havpt" opt; do
    case ${opt} in
	a)
	    always='yes'
	    ;;
	v)
	    verbose=true
	    ;;
	t)
	    show_time=true
	    ;;
	h)
	    displayUsage
	    exit 1
	    ;;
	p)
	    echo "Correction INFO: Running in parallel!"
	    parallel=true
	    ;;
	\?)
	    echo "Invalid option: $OPTARG" 1>&2
	    exit 2
	    ;;
	:)
	    echo "Invalid option: $OPTARG requires an argument" 1>&2
	    exit 2
	    ;;
    esac
done

shift $((OPTIND-1))

# Check number of arguments
if [ $# -lt 1 ]
then
    echo "No path provided!"
    exit 1
fi

sum=0
count=0
submission=$1
corrected=0
skipped=0
function correction_routine {
    # init variables
    submission=$1

    # evaluate submission
    echo "evaluating..."
    dir="$PWD"
    cp -r "$folder"/code/* "$submission"/
    cd "$submission"
    start=$(date +%s)
    if $show_time

    then
	time python2 main.py > errors.log 2>&1
    else
	python2 main.py > errors.log 2>&1
    fi

    rm -rf test/ config.py main.py
    end=$(date +%s)
    if $verbose; then
	echo "EVALUATED IN: $(( end - start))s"
    fi

    # zip answers
    bname=$(basename "$PWD")
    zip_name=$(basename "$PWD" | sed 's/ /+/g')
    zip "$zip_name" "$bname.txt" "errors.log"

    cd "$dir"
    corrected=$(( corrected+1 ))

    foldername=$(basename -- "$submission")
    echo -n "$foldername	" >> "$scoreFile"

    bname=$(basename "$submission")
    points=$(cat "$submission/$bname""_points.txt" | paste -sd+ - | bc)
    LC_ALL=C printf "%0.2f " "$points" >> "$scoreFile" #make locale correct

    OIFS=$IFS
    IFS='_'
    read -ra ADDR <<< "$foldername"
    IFS=$OIFS

    str1="LATE"
    str2="${ADDR[1]}"
    if [ "$str1" != "$str2" ]; then
    	echo "${ADDR[1]}" >> "$scoreFile"
    else
    	echo "${ADDR[2]}" >> "$scoreFile"
    fi
}

# Read user input
folder="$1"
totalPath="$folder/submissions/"
week=$(basename -- "$folder")
scoreFile="$week""_scores.txt"

submissionCount=$(ls -1 "$totalPath" 2>/dev/null | wc -l)

if [ $submissionCount = 0 ]
then
    echo No submissions found >  "$scoreFile"
fi

echo "Assignment_id	Total_points	URL" >  "$scoreFile"

total="$(ls $totalPath | wc -l)"
count=0

if [ "$always" = "yes" ]
then
    folders=$totalPath*/
else
    folders=$(find "$totalPath" -mindepth 1 -type d '!' -exec sh -c 'ls -1 "{}"|egrep -i -q "^*points.txt$"' ';' -print | sort | xargs -i% echo "%/")
fi

for dir in "$folders"
do
    # dir="$(dirname $f)"
    if $verbose
    then
	echo "Correcting:"
	echo "$dir"
    fi
    correction_routine "$totalPath$(basename "$dir")"
done

echo "Done!"
# echo "corrected/skipped/total:"
# echo "$corrected/$skipped/$num_lines"
