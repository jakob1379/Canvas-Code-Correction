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
    correct {-a always} always

'
}

always='no'

while getopts ":ha" opt; do
    case ${opt} in
	a)
	    always='yes'
	    ;;
	h)
	    displayUsage
	    exit 1
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
    shift
done


# Check number of arguments
if [ $# -lt 1 ]
then
    echo "No path provided!"
    exit 1
fi

submission=$1

function correction_routine {
    # init variables
    submission=$1
    fileCount=$(ls -1 "$submission"/*log "$submission"/*txt 2>/dev/null | wc -l)

    # evaluate submission
    if [[ -z `find $submission -type f -name '*points.txt'` ]] || [ $always = 'yes' ]
    then
	echo "evaluating..."
	dir="$PWD"
	cp -r "$folder"/code/* "$submission"/
	cd "$submission"
	python2 main.py > errors.log 2>&1
	rm -rf test/ config.py main.py # TODO: Make one cleanup call instead
	cd "$dir"
    else
	echo "skipping..."
    fi

    foldername=$(basename -- "$submission")
    echo -n "$foldername	" >> "$scoreFile"

    bname=$(basename $submission)
    points=$(cat "$submission/$bname""_points.txt" | paste -sd+ - | bc)
    printf "%0.2f " $points >> "$scoreFile"

    # # url="https://absalon.ku.dk/courses/38767/assignments/99856/submissions/"
    # echo -n "$url" >> "$scoreFile"

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
count=1

tmp_file=$(mktemp /tmp/file.XXX)
for d in $(find $totalPath* -type d -name "*")
do
    echo -e "$count of $total $week: $(basename $d)"
    correction_routine $d &

    PID="$!"
    echo "$PID:$scripts" >> $tmp_file
    PID_LIST+="$PID "

    count="$(($count+1))"
done

for process in ${PID_LIST[@]};do
   wait $process
   exit_status=$?
   script_name=`egrep $process $tmp_file | awk -F ":" '{print $2}' | rev | awk -F "/" '{print $2}' | rev`
   echo "$script_name exit status: $exit_status"
done

echo "all's done!"
