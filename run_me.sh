#!/bin/bash


echo "INFO: Downloading submissions"
python3 download_submissions.py
echo "INFO: Done!"

for folder in $(ls -d Week*/); do
    echo "INFO: Unzipping"
    bash submissions_unzip.sh "$folder"
    echo "INFO: Done!"

    echo "INFO: Correcting submissions"
    bash submissions_correcting.sh "$folder"
    echo "INFO: Done!"

    echo "INFO: zipping answers"
    bash submissions_zip.sh "$folder"
    echo "INFO: Done!"
done

echo "INFO: Done with whole routine!"
