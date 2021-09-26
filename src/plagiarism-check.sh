#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [ $# -lt 1 ]
then
    echo "plagiarism-check: takes at least one path"
    exit 2
fi

# folders="$(find -wholename "*/submissions")"
# extensions=$(awk -F '=' -e '/^ext/{print $2}' config.ini)
extensions=$(awk -F '=' '/^extensions/{print $2}' config.ini)
cutoff=$(awk -F '=' 'BEGIN{ORS=""}/cutoff/{print $2}' config.ini)
language=$(awk -F '=' 'BEGIN{ORS=""}/lang/{print $2}' config.ini )

function check_assignment {
    # create input for moss
    assignment=$(basename "$1")
    mossPath=$(basename "$1" | sed 's/ /\\ /g')

    # # download all the handins
    # rm -rf "$assignment/submissions/*"
    # python download_submissions.py -d all -a "$assignment"
    # bash submissions_unzip.sh "$assignment/"

    # Construct the paths for moss by checking each presence of each extension
    paths_to_check=()
    echo "checking extensions..."
    IFS=' '
    for ext in $extensions
    do
	IFS='\n\t'
	if [ ! -z  "$(find "$assignment/submissions" -type f -name "*$ext")" ]
	then
	    echo "Found: $ext"
	    mapfile -d $'\0' tmp_paths < \
		    <(find "$assignment/submissions" -type f -name "*$ext" -print0)
	    paths_to_check+=( "${paths_to_check[@]}" "${tmp_paths[@]}" )
	fi
	IFS=' '
    done

    # return if nothing found
    if (( "${#paths_to_check[@]}" == 0 ))
    then
	echo "No files found. skipping $1"
	return
    fi

    # Catch result url
    echo "uploading to moss..."
    url=$(./moss -l $language -d "${paths_to_check[@]}" | grep -oP 'http://moss.stanford.edu/results.*')/
    echo "$url"
    # # url="http://moss.stanford.edu/results/8/4255768150604/" # a test url

    # Create table for local inspection
    echo "creating table..."
    echo "$url" > "$assignment/similarity.txt"
    bash mossurl2table.sh "$url" >> "$assignment/similarity.txt"

    # Print lines that crosses the cutoff value

    suspecious_handins=$(awk -v cutoff="$cutoff" '{ if ($3 >= cutoff) { print } }' "$assignment/similarity.txt")
    if [ ! -z "$suspecious_handins" ]
    then
	echo "*** PEOPLE ABOVE THE THRESHOLD THE THESHOLD!: ***"
	echo "$suspecious_handins"
	echo ""
	echo "$suspecious_handins" > "$assignment/suspicious.txt"

	# Create mossum diagram
	echo "making graph..."
	mossum \
	    --min-percent "$cutoff" \
	    --format pdf \
	    --transformer '.*/submissions/(.*)_.*_.*_(.*).*/' \
	    --output "$assignment/similarity_graph" \
	    --title "$url" \
	    "$url"
    fi
    return $?
}

function routine {
    folder="$(basename $1)"
    check_assignment "$folder/" || return $?
    python hclust.py "$folder/similarity.txt"

    return $?
}

# combine folders and extensions into regexes for moss
for folder in $@; do
    echo "Checking: $folder"
    routine "$folder"
done

wait
