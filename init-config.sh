#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

read -p "please create and insert your token from
https://absalon.ku.dk/profile/setting: " token

read -p "please insert your course ud from absalon which is in the url
https://absalon.ku.dk/courses/<course-id>: " courseid

# Test token and courseid
canvas="absalon.ku.dk"
http_code=$(curl --silent \
		 --output /dev/null \
		 --write-out "%{http_code}\n" \
		 -X GET \
		 -H "Authorization: Bearer $token"\
		 "https://$canvas/api/v1/courses/$courseid/assignments")

if [ "$http_code" -eq "401" ]; then
    echo "Token is invalid. try again..."
    exit 2
elif [ "$http_code" -eq "404" ]; then
    echo "Course-id is invalid. try again..."
    exit 2
else
    echo "Token is valid!"
fi

read -p "please insert the used language.
Supported languages are (\"c\", \"cc\", \"java\", \"ml\", \"pascal\", \"ada\", \"lisp\", \"scheme\", \"haskell\", \"fortran\", \"ascii\", \"vhdl\", \"perl\", \"matlab\", \"python\", \"mips\", \"prolog\", \"spice\", \"vb\", \"csharp\", \"modula2\", \"a8086\", \"javascript\", \"plsql\", \"verilog\"): " lang
lang="$(echo "$lang" | tr '[:upper:]' '[:lower:]'))"

read -p "please insert the extension to check for plagiarism, multiple should be seperated with space e.g. .cpp .h .hpp " exts
echo "Similarity has been set to defaul 50%. This can be changed manually in config.ini"

text="[DEFAULT]
APIURL=https://absalon.ku.dk/
TOKEN=$token
COURSEID=$courseid
UPLOAD_SCORE=no

[plagiarism]
# This framework is using moss (https://theory.stanford.edu/~aiken/moss/)
# Define types of files delivered that should be checked for plagiarism e.g. ext1='.cpp', ext2='.hpp' etc.
# Supported languages are (\"c\", \"cc\", \"java\", \"ml\", \"pascal\", \"ada\", \"lisp\", \"scheme\", \"haskell\", \"fortran\", \"ascii\", \"vhdl\", \"perl\", \"matlab\", \"python\", \"mips\", \"prolog\", \"spice\", \"vb\", \"csharp\", \"modula2\", \"a8086\", \"javascript\", \"plsql\", \"verilog\")
lang=$lang
extensions=$exts
# cutoff for plagiarism warning
cutoff=50
"


if [ -f "config.ini" ]
then
    while true; do
	read -p "config.ini exists, are you sure you want to overwrite? [y/N] " ans
	ans="$(echo "$ans" | tr '[:upper:]' '[:lower:]')"
	case "$ans" in
	    'y' )
		echo "Text is saved in config.ini"
		echo "$text" > config.ini
		break
		;;
	    'n' )
		echo "Text is NOT saved!"
		echo "$text"
		break
		;;
	esac

    done
fi

# initialize assignment folders from canvas
assignments=$(bash setup-assignmhnt-folders.sh)

echo "Enter the amount of points needed to complete each assignment:"
scores=()
re='^[0-9]+([.][0-9]+)?$'
for assignment in $assignments;
do
    while true
    do
	read -p "$assignment: " score
	if [[ ! "$score" =~ $re ]]
	then
	    echo "Not a valid number. Try again"
	else
	    scores+=( "$assignment=$score" )
	    break
	fi
    done
done

scores="$(for score in ${scores[@]}; do echo "$score"; done;)"
text="
[scores_to_complete]
# assignment names should match the folder names list assignments with 'python download_submissions.py -l'
$scores
"
echo "$text" >> config.ini

while true; do
    read -p "Should scores be uploaded to absalon [y/N]: " ans
    ans="$(echo "$ans" | tr '[:upper:]' '[:lower:]')"
    case "$ans" in
	'y' )
	    sed -i 's/UPLOAD_SCORE=no/UPLOAD_SCORE=yes/' config.ini
	    break
	    ;;
	'n' )
	    break
	    ;;
    esac
done
