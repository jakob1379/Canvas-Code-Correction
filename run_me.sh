#!/bin/bash


echo "INFO: Downloading submissions"
python3 download_submissions.py
echo "INFO: Done!"

echo "INFO: Unzipping"
./unzip_submissions2
echo "INFO: Done!"

for folder in $(ls -d */)
do
    echo "INFO: Correcting submissions"
    bash submissions_correcting.sh "$folder"
    echo "INFO: Done!"

    echo "INFO: zipping answers"
    bash submissions_zip.sh "$folder"
    echo "INFO: Done"
done

echo "INFO: Done whole routine!"
