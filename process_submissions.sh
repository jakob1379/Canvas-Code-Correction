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

# Arguments
args='-'
parallel=false
correct_all=false
show_time=false
while getopts ":hpat" opt; do
    case ${opt} in
	p)
	    echo "RUN_ME: Parallelization enabled!"
	    parallel=true
	    args+='p'
	    ;;
	a)
	    correct_all=true
	    args+='a'
	    ;;
	t)
	    show_time=true
	    args+=t
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
done
shift $((OPTIND-1))

# Routing
echo "INFO: Downloading submissions"
python3 download_submissions.py -p
echo "INFO: Done!"

for folder in $(ls -d Week*/); do    
    echo "INFO: Unzipping"
    bash submissions_unzip.sh "$folder"
    echo "INFO: Done!"

    # Copy armadillo into submissions
    if [ "$folder" = 'Week7-8/' ]; then
	echo "Skipping $folder!"
	break # delete this line when codechecker works

	ls -d Week7-8/submissions/*/ | xargs -i% cp -ur armadillo/armadillo_bits/ %
	ls -d Week7-8/submissions/*/ | xargs -i% cp -ur armadillo/armadillo.hpp %
    fi
    
    echo "INFO: Correcting submissions"
    if [ "$args" != '-' ];
    then
	bash submissions_correcting.sh $args "$folder"
    else
	bash submissions_correcting.sh "$folder"
    fi
    echo "INFO: Done!"

    # echo "INFO: zipping answers"
    # bash submissions_zip.sh "$folder"
    # echo "INFO: Done!"
done

echo "INFO: zipping answers"
./zip_submission
echo "INFO: Done!"

echo "INFO: Done with whole routine!"
