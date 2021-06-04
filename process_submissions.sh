#!/bin/bash

displayUsage() {
    echo '
<>  angle brackets for required parameters: ping <hostname>
[]  square brackets for optional parameters: mkdir [-p] <dirname>
... ellipses for repeated items: cp <source1> [source2…] <dest>
 |  vertical bars for choice of items: netstat {-t|-u}

usage:  process_submissions.sh [-f -p -a -t -h]
operations:
    {-h help} shows this dialogue
    {-f force} Checks already failed assignments
    {-p parallel} downloads and check in parallel
    {-a all} Checks all assignments again
    {-t time} show time
'
}

# Arguments
args='-'
parallel=false
correct_all=false
show_time=false
reverse=false
failed=false
while getopts ":hpat" opt; do
    case ${opt} in
	p)
	    echo "Parallelization enabled!"
	    parallel=true

	    args+='p'
	    ;;
	a)
	    correct_all=true
	    args+='a'
	    ;;
	t)
	    show_time=true
	    args+='t'
	    ;;
	h)
	    displayUsage
	    exit 1
	    ;;
	v)
	    verbose=true
	    download_args+='v'
	    ;;
	p)
	    parallel=true
	    download_args+='p'
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

for folder in $(ls -d Week*/); do
    echo "INFO: Unzipping"
    bash submissions_unzip.sh "$folder"
    echo "INFO: Done!"

    echo "INFO: Correcting submissions"
    if [ "$args" != '-' ];
    then
	bash submissions_correcting.sh "$args" "$folder"
    else
	bash submissions_correcting.sh "$folder"
    fi
    echo "INFO: Done!"
done

echo "INFO: zipping answers"
bash zip_submission
echo "INFO: Done!"

echo "INFO: Done with whole routine!"
