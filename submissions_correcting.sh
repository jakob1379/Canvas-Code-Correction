#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'



displayUsage() {
    echo '
usage:  name <operation> [...]
operations:
    correct {-h help} shows this dialogue
    correct {-a always} always corect assigments
    correct {-p paralllel} run in parallel

'
}
always=false
verbose=false
parallel=false
show_time=false
while getopts ":havptr" opt; do
    case ${opt} in
	a)
	    always=true
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
    $verbose && echo  "evaluating..."
    dir="$PWD"
    /usr/bin/cp -rf "$folder"/code/* "$submission"/
    cd "$submission"

    start=$(date +%s)
    if $show_time
    then
	time python main.py > errors.log 2>&1
    else
	python main.py > errors.log 2>&1
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

    bname=$(basename "$submission")
    points=$(cat "$submission/$bname""_points.txt" | paste -sd+ - | bc)

    OIFS=$IFS
    IFS='_'
    read -ra ADDR <<< "$foldername"
    IFS=$OIFS

    str1="LATE"
    str2="${ADDR[1]}"
}

# Read user input
folder="$1"
week=$(basename -- "$folder")
totalPath="$week/submissions/"

if [[ $always ]]
then
    echo "Correcting all!"
    folders=$(find $totalPath -mindepth 1 -maxdepth 1 -type d)
else
    # Find folders that does not have a points.txt file in them
    folders=$(find $totalPath -type f -not -name '*_points.txt' -exec dirname {} \;)
fi

num_folders=$(echo "$folders" | wc -l)
count=0
for d in $folders; do
    echo "Correcting: $d"
    correction_routine "$totalPath$(basename "$d")"
    echo $count | tqdm --update-to --total=$num_folders > /dev/null
    ((count+=1))
done

echo "Done!"
