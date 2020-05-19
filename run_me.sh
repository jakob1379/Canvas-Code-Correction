#!/bin/bash

displayUsage() {
    echo '
<>  angle brackets for required parameters: ping <hostname>
[]  square brackets for optional parameters: mkdir [-p] <dirname>
... ellipses for repeated items: cp <source1> [source2…] <dest>
 |  vertical bars for choice of items: netstat {-t|-u}

usage:  name <operation> [...]
operations:
    name {-h help} shows this dialogue

'
}

parallel=false
while getopts ":hp" opt; do
    case ${opt} in
	p)
	    echo "RUN_ME: Parallelization enabled!"
	    parallel=true
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

echo "INFO: Downloading submissions"
$parallel && python3 download_submissions.py -p || python3 download_submissions.py
echo "INFO: Done!"

for folder in $(ls -d Week*/); do
    echo "INFO: Unzipping"
    bash submissions_unzip.sh "$folder"
    echo "INFO: Done!"

    echo "INFO: Correcting submissions"
    $parallel && bash submissions_correcting.sh -p "$folder" || bash submissions_correcting.sh "$folder"
    echo "INFO: Done!"

    echo "INFO: zipping answers"
    bash submissions_zip.sh "$folder"
    echo "INFO: Done!"
done

echo "INFO: Done with whole routine!"
