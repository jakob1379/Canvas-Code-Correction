#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if [ $# -lt 1 ]
then
    echo "plagiarism-check: takes at least one path"
    exit 2
fi

extensions=$(awk -F '=' '/^extensions/{print $2}' config.ini)
cutoff=$(awk -F '=' 'BEGIN{ORS=""}/cutoff/{print $2}' config.ini)
language=$(awk -F '=' 'BEGIN{ORS=""}/lang/{print $2}' config.ini )

function check_assignment {
    # create input for moss
    assignment=$(basename "$1")

    # Construct the paths for moss by checking each presence of each extension
    paths_to_check=()
    used_exts=()
    echo "checking extensions..."
    IFS=' '
    for ext in $extensions
    do
	echo "Checking ext: $ext"

	IFS='\n\t'
	if [ ! -z  "$(find "$assignment/submissions" -type f -name "*$ext")" ]
	then
	    echo "Found files with extension: $ext"
	    mapfile -d $'\0' tmp_paths < \
		    <(find "$assignment/submissions" -type f -name "*$ext" -print0)

	    # Make sure each file is a text file
	    echo "Validating files..."
	    num_files="${#tmp_paths[@]}"
	    for file in "${tmp_paths[@]}"; do
		isFile=$(file -0 "$file" | cut -d $'\0' -f2)
		if [[ "$isFile" == *"text"* ]]; then
		    paths_to_check+=( "$file" )
		fi
		# count=$(( count + 1 )) # un-comment when tqdm has been fixed
	    done #| tqdm --total="$num_files" --null

	    used_exts+=( "$ext" )
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
    output=$(./moss -l $language -d "${paths_to_check[@]}" 2>&1 | tee tmp/moss.log)
    url=$(echo "$output" | grep -oP 'http://moss.stanford.edu/results.*')/
    echo "$url"
    # url="http://moss.stanford.edu/results/5/4697031321443/"

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
	    --title "$url types:${used_exts[*]}" \
	    "$url"
    fi
    return $?
}

function routine {
    folder=$(basename "$1")
    check_assignment "$folder/"
    # python hclust.py "$folder/similarity.txt"

    return $?
}

# combine folders and extensions into regexes for moss
for folder in $@; do
    echo "Checking: $folder"
    routine "$folder"
done

wait
