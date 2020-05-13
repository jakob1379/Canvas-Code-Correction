#!/bin/bash


for folder in $(ls -d */)
do
bash submissions_unzip.sh "$folder"
bash submissions_correcting.sh "$folder"
bash submissions_zip.sh "$folder"
done



