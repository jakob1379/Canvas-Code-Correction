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
while getopts ":havp" opt; do
    case ${opt} in
	a)
	    always='yes'
	    ;;
	v)
	    verbose=true
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
    if [[ -z `find "$submission" -type f -name '*points.txt'` ]] || [ $always = 'yes' ]
    then
	echo "evaluating..."
	dir="$PWD"
	cp -r "$folder"/code/* "$submission"/
	cd "$submission"
	python2 main.py > errors.log 2>&1
	rm -rf test/ config.py main.py # TODO: Make one cleanup call instead
	cd "$dir"
	echo "$submission corrected" >> correction_status
    else
	echo "skipping..."
	echo "$submission skipped" >> correction_status
    fi

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

# Create a file to keep track of correction statuss
> correction_status

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
count=1

tmp_file=$(mktemp /tmp/file.XXX)
for d in $totalPath*/
do

    echo -e "$count of $total $week: $totalPath$d"
    if $parallel; then
	correction_routine "$totalPath$(basename "$d")" &
	PID="$!"
	echo "$PID:$scripts" >> $tmp_file
	PID_LIST+="$PID "
    else
	correction_routine "$totalPath$(basename "$d")"
    fi
    count="$(($count+1))"
done

if $parallel; then
    for process in ${PID_LIST[@]};do
	wait $process
	exit_status=$?
	script_name=`egrep $process $tmp_file | awk -F ":" '{print $2}' | rev | awk -F "/" '{print $2}' | rev`
	echo "$script_name exit status: $exit_status"
    done
fi

num_lines=$(cat correction_status | wc -l)
corrected=$(grep -P "corrected$" correction_status | wc -l)
skipped=$(grep -P "skipped$" correction_status | wc -l)
echo "Done!"
echo "corrected/skipped/total:"
echo "$corrected/$skipped/$num_lines"
