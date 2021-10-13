#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'


displayUsage() {
    echo '
usage:  process_submissions.sh [-f -p -a -t -h] [H1,..,Hn]
operations:
    {-h help} shows this dialogue
    {-p plagiarism check} check for plagiarism
    {-a all} Checks all assignments again
'
}

# Arguments
args='-'
plagiarism=''
while getopts ":haptv" opt; do
    case ${opt} in
	h)
	    displayUsage
	    exit 1
	    ;;
	a)
	    args+='a'
	    ;;
	p)
	    plagiarism=true
	    ;;
	t)
	    args+='t'
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

if [ $# -eq 0 ];  then
    # Find assigments with correction code and submissions
    not_empty=$(find -maxdepth 2 -type d -wholename "*/code" -not -empty | cut -d '/' -f 2)
    assigments=$(find -maxdepth 2 -type d  -wholename "*/submissions" -not -empty | cut -d '/' -f 2)
    assignmentsWithSubsAndCode=$(comm -12 <(echo "$not_empty" | sort) <(echo "$assigments" | sort))
    assignments=$(sed -e 's/$/\/submissions/' <(echo "$assignmentsWithSubsAndCode"))
else
    assigments=$@
fi

# Check arguments
for folder in $assigments; do
    if [ ! -d "$folder" ]; then
	echo "WARNING! input does not exist: $folder"
	continue
    fi
    echo "INFO: Unzipping"
    # bash submissions_unzip.sh "$folder"
    python3 submission_unzip.py "$folder"
    echo "INFO: Done!"

    if [ ! -z "$plagiarism" ]
    then
	echo "INfO: Checking plagiarism"
	./plagiarism-check.sh "$folder"
    fi

    echo "INFO: Correcting submissions"
    if [ "$args" != '-' ];
    then
	bash submissions_correcting.sh "$args" "$folder"
    else
	bash submissions_correcting.sh "$folder"
    fi
done

echo "INFO: zipping answers"
bash zip_submission
echo "INFO: Done!"

wait
echo "INFO: Done with whole routine!"
