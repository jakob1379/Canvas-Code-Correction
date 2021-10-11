#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# init config to bash array
bash config2shell
find . -maxdepth 1 -type d -wholename '*/code' -exec cp '.config_array' '{}' \;

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

config_children="$(awk -F '=' -e '/^MAXPROC/{print $2}' config.ini)"
if [ ! -z "$config_children" ];then
    max_children=$config_children
else
    max_children=1
fi

function timout-write-points-and-comments {
    bname=$(basename "$PWD")
    echo "0" > "$bname""_points.txt"
    echo "
########################################
# Timeout reached! Code did not finish #
########################################" >> "$bname.txt"
}

function crarsh-write-points-and-comments {
    bname=$(basename "$PWD")
    echo "0" > "$bname""_points.txt"
    echo "
 ###################
 # Program crashed #
 ###################
" >> "$bname.txt"
}

function correction_routine {
    # init variables
    submission="$1"

    # evaluate submission
    $verbose && echo "evaluating..."
    dir="$PWD"
    orig_file_names=$(find "$folder"/code/ -maxdepth 1 -mindepth 1 -exec basename {} \;)
    /bin/cp -af "$folder"/code/. "$submission"/ # copy everything including hidden files
    cd "$submission"

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
	    timeout $maxtime sh main.sh 2> /dev/null && exit_code=0 || exit_code="$?"
	fi
    fi

    if [ "$exit_code" -eq "124" ]; then
	timout-write-points-and-comments
    fi

    # delete test files
    for fname in $orig_file_names; do
	rm -rf "$fname" || true
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

if [[ "$always" == "true" ]]
then
    echo "Correcting all!"
    folders=$(find "$totalPath" -mindepth 1 -maxdepth 1 -type d |\
	   shuf)
else
    echo "finding uncorrected..."
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
echo "Max concurrent processes: $max_children"
for d in $folders; do
    echo $count | tqdm --update-to --total=$num_folders > /dev/null
    while [ "$(pgrep -c -P$$)" -ge "$max_children" ]; do
	sleep 0.1
    done
    echo "Correcting: $d"
    correction_routine "$totalPath$(basename "$d")" &
    ((count+=1))
done
wait
echo $num_folders | tqdm --update-to --total=$num_folders > /dev/null
echo "Done!"
