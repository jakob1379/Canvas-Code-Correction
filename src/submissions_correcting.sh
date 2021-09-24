#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# init config to bash array
bash config2shell
find . -type d -wholename '*/code' -exec cp '.config_array' '{}' \;

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
sandbox="$(awk -F '=' -e '/^sandbox/{print $2}' config.ini)"
maxtime="$(awk -F '=' -e '/^MAXTIME/{print $2}' config.ini)"


function timout_write_points_and_comments {
    bname=basename "$PWD"
    echo "0" > "$bname_points.txt"
    echo "########################################
# Timeout reached! Code did not finish #
########################################" >> "$bname.txt"
}

function correction_routine {
    # init variables
    submission="$1"

    # evaluate submission
    $verbose && echo "evaluating..."
    dir="$PWD"
    orig_file_names=$(find "$folder"/code/ -maxdepth 1 -mindepth 1 -exec basename {} \;)
    /usr/bin/cp -rf "$folder"/code/. "$submission"/ # copy everything including hidden files
    cd "$submission"

    echo "###### RUNNING CODE ######## "
    start=$(date +%s)
    if $show_time
    then
	if [ "$sandbox" == 'yes' ]; then
	    timeout $maxtime time firejail sh main.sh 2> /dev/null
	else
	    timeout $maxtime time sh main.sh 2> /dev/null
	fi
    else
	if [ "$sandbox" == 'yes' ]; then
	    timeout $maxtime firejail sh main.sh 2> /dev/null
	else
	    timeout $maxtime sh main.sh 2> /dev/null && exit_code=0 ||  exit_code="$?"
	fi
    fi
    echo "###### FINISHED RUNNING CODE $exit_code ######## "
    if [[ "$exit_code" == "124" ]]; then
	timout_write_points_and_comments
	echo "###### WRITING TIMEOUT MESSAGE ######## "
    fi

    # delete test files
    for fname in $orig_file_names; do
	rm -rf "$fname"
    done

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
assignment=$(basename -- "$folder")
totalPath="$assignment/submissions/"

if [[ $always ]]
then
    echo "Correcting all!"
    folders=$(find "$totalPath" -mindepth 1 -maxdepth 1 -type d |\
	   shuf)
else
    folders=$(find "$totalPath" \
		   -mindepth 1 \
		   -maxdepth 1 \
		   -type d \
		   -exec sh -c '[[ $(ls -A "{}"/*points.txt 2>/dev/null) ]] && exit 1; true' \; \
		   -print | \
	   shuf)
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
