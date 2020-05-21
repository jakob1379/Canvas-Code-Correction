# Import the Canvas class
from canvas_helpers import (file_to_string, create_file_name,
                            flatten_list, print_dict)
from canvasapi import Canvas
from glob import glob
from joblib import Parallel, delayed
import argparse
import multiprocessing
import numpy as np
import progressbar as Pbar
import re
import os
import subprocess
from urllib.parse import unquote

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--parallel",
                    help="grade submissions in parallel",
                    action='store_true')
parser.add_argument("-v", "--verbose",
                    help="set verbose",
                    action='store_true')
parser.add_argument("-q", "--question",
                    help="prompt if a non-matching comment should be uploaded",
                    action='store_true')
args = parser.parse_args()

def extract_comment_filenames(comments):
    # Get all attachments in comments as one flat list
    return flatten_list(
        [[unquote(att.get('filename')) for att in comm.get('attachments')
          if att.get('filename')]
         for comm in comments if comm.get('attachments')])


def upload_comments(sub, assignments, args):
    # Get assignment- and file name
    assignment_name = sub.split('/')[0]
    handin_name = re.sub(" ", "+", sub.split('/')[-2])

    # get points and user id
    user_id = re.findall(r'\d+', handin_name)[0]

    # Get submission for user
    assignment = assignments[assignment_name]
    submission = assignment.get_submission(user_id,
                                           include='submission_comments')

    # extract attached filenames from comments
    comment_files = extract_comment_filenames(submission.submission_comments)

    # get path to comment zip
    file_to_upload = glob(sub + '*.zip')


    if file_to_upload:
        file_to_upload = file_to_upload[0]
        upload_name = file_to_upload.split('/')[-1]
    else:
        raise FileExistsError("zip to upload not found in: " + sub)

    out_str = 'Checking: ' + sub
    # Only upload if it isn't already there.
    if handin_name+'.zip' not in comment_files:
        if args.verbose:
            print(out_str)
            print("Upload: uploading feedback\n", file_to_upload)

        ans = ''
        if args.question:
            print(30*'-')
            print("Old Feedback uploads:")
            if comment_files:
                for comm in comment_files:
                    print(comm)
            else:
                print(None)
            print("\nNew comment:", upload_name, '\n')
            ans = input("Upload: Should new comment be uploaded? [y/N] ")
        if ans.lower() == 'y' or not args.question:
            submission.upload_comment(file_to_upload)

        elif args.question:
            print("Upload: Comments NOT uploaded.")
    elif args.verbose:
        print(out_str)
        print("Upload: feedback already uploaded\n")


# %% Init
if args.verbose:
    print('Initialising canvas...')

# Canvas API URL
domain = 'absalon.ku.dk'
API_URL = "https://"+domain+"/"

# Canvas API key
API_KEY = file_to_string('token')

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

# init course
course_id = file_to_string('course_id')
course = canvas.get_course(course_id)
assignments_as_dict = {ass.name.capitalize().replace(' ', ''): ass
                       for ass in course.get_assignments()}

# get users and local points
users = course.get_users()
reports = sorted(glob('Week*/submissions/*/'))

# Let's start grading!
pbar = Pbar.ProgressBar(redirect_stdout=True)
num_cores = multiprocessing.cpu_count()

if args.parallel:
    if args.verbose:
        print("Uploading comments in parallel!")
    Parallel(n_jobs=num_cores)(delayed(
        upload_comments)(rep, assignments_as_dict, args) for
                               rep in pbar(reports))
else:
    for rep in (reports):
        upload_comments(rep, assignments_as_dict, args)
