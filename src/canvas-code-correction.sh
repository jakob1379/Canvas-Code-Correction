#!/usr/bin/env bash
set -euo pipefail

displayUsage() {
    echo "
usage:  canvas-code-correction.sh [...]
operations:
    {-h help}    shows this dialogue
    {-a all}     correct all assignments
    {-d daemon}  keep running until process is closed
    {-n number}  number of times to run the correction
    {-f failed}  correct failed assignment
    {-s skip}    skip checking requirements
    {-t time}    time to run as daemon. Given as HH:MM:SS
    {-v verbose} set verbosity
    {-w wait}    Pause for TIME. SUFFIX may be 's' for seconds (the default),
'm' for minutes, 'h' for hours or 'd' for days. Given two or more arguments, pause for the amount of time
specified by the sum of their values e.g. '1d4h'
"
}

n=1
t=0
w=0
daemon=false
args=''
download_args=' '
max_time=0
while getopts ":hadfn:st:vw:" opt; do
    case ${opt} in
	h)
	    displayUsage
	    exit 0
	    ;;
	a)
	    grade_all=true
	    args+='a'
	    ;;
	d)
	    daemon=true
	    ;;
	f)
	    download_args='-d failed '
	    ;;
	n)
	    n="$OPTARG"
	    ;;
	s)
	    skip_check="skip"
	    ;;
	t)
	    max_time=$(echo "$OPTARG" | awk -F: '{ print ($1 * 3600) + ($2 * 60) + $3 }')
	    ;;
	v)
	    verbose=true
	    args+='v'
	    download_args+='-v '
	    ;;
	w)
	    w=$OPTARG
	    ;;
	\?)
	    echo "Invalid option: $OPTARG" 1>&2
	    displayUsage
	    exit 2
	    ;;
	:)
	    echo "Invalid option: $OPTARG requires an argument" 1>&2
	    displayUsage
	    exit 2
	    ;;
    esac
done
shift $((OPTIND - 1))


# check requirements
if [ -z skip_check ]
then
    echo "Checking requirements"
    bash check_requirements || exit 1
fi

# check for network
if ! wget -q --spider http://google.com
then
    echo "No connection to the internet"
    exit 1
fi


[ ! -z "$args" ] && args+="-$args"

function routine {
    echo "
    ################################################################################
    #                           deleting old submissions                           #
    ################################################################################"
    python3 delete_submissions.py
    echo "Done deleting old submissions!"

    echo "
    ################################################################################
    #                           Downloading submissions                            #
    ################################################################################
    "

    if [ ! -z "$download_args" ]; then
	download_out=$(python3 download_submissions.py $download_args | tee /dev/fd/2)
    else
	download_out=$(python3 download_submissions.py | tee /dev/fd/2)
    fi
    numAssignments=$(echo "$download_out" | \
			     grep -oP "Submissions to correct:.*" | \
			     grep -oP "\d+")
    echo "Done downloading submissions"
    echo "Number of assignments: $numAssignments"

    if [ "$numAssignments" -eq "0" ]
    then
	echo "No new assignments. Skipping rest of the routine"
	return
    fi

    echo "
    ################################################################################
    #                             process submissions                              #
    ################################################################################"
    bash process_submissions.sh
    echo "Done correcting submissions!"

    echo "
    ################################################################################
    #                              uploading comments                              #
    ################################################################################"
    python3 upload_comments.py -v
    echo "Done uploading comments!"

    echo "
    ################################################################################
    #                               updating grades                                #
    ################################################################################"
    python3 upload_grades.py -v
    echo "Done updating grades!"

    echo "
    ################################################################################
    #                               plotting results                               #
    ################################################################################"
    python3 plot_scores.py
    echo "Done plotting"
}


convert-secs() {
    ((h=${1}/3600))
    ((m=(${1}%3600)/60))
    ((s=${1}%60))
    printf "%02d:%02d:%02d\n" $h $m $s
}


SECONDS=0
while true; do

    time routine

    if [ "$n" -gt "0" ]; then
	n=$((n - 1))
    fi
    if [ "$n" -gt "0" ] || $daemon; then
	echo "
	################################################################################
	#                                   waiting                                    #
	################################################################################"
	! $daemon && date && echo "Runs left: $n"

	# While
	echo "waiting for $w"
	date
	sleep "$w"

	run_time=$(convert-secs $SECONDS)
	echo -e "\nDaemon has been running for: $run_time"
    fi
    if [ "$n" = "0" ] && [ "$daemon" = "false" ];
    then
	break
    elif [ "$SECONDS" -gt "$max_time" ] && [ "$max_time" -ne "0" ] && [ "$daemon" = "true" ];
    then
	break
    fi
done

echo "Autorun: Done!"
