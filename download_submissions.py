# Import the Canvas class
from canvas_helpers import (download_url,
                            file_to_string,
                            create_file_name,
                            print_dict,
                            flatten_list,
                            extract_comment_filenames)
from canvasapi import Canvas
from glob import glob
from joblib import Parallel, delayed
from time import time
import argparse
import multiprocessing
import os
import progressbar as Pbar
import re
import shutil
import urllib.request

parser = argparse.ArgumentParser("""
Program to download assignments. It needs two files next to it
    course_id: Containing the course id
    token:     Your personal accesstoken from canvas""")
parser.add_argument("-v", "--verbose",
                    help="sets verbosity",
                    action='store_true')
parser.add_argument("-p", "--parallel",
                    help="download in parallel",
                    action='store_true')
parser.add_argument("-c", "--check-all",
                    help="check all assignments, default is to only check " +
                    "changed assignments",
                    action='store_true')
parser.add_argument("-u", "--uncommented",
                    help="cheack uncommented assignments",
                    action='store_true')
parser.add_argument("-f", "--failed",
                    help="download failed submissions",
                    action='store_true')


args = parser.parse_args()

def download_submission(sub, old_files, course, args):
    try:
        url = sub.attachments[0]['url']
        if url:
            file_name = create_file_name(sub, course)
            directory = course.get_assignment(sub.assignment_id).name.replace(
                ' ', '') + '/' + 'submissions/'
            # check if user has old submissions
            folders_to_remove = [old for old in old_files
                                 if str(sub.user_id) in old and
                                 file_name+'/' not in old]
            for f in folders_to_remove:
                shutil.rmtree(f)
            # download attachment if it doesn't exist,
            if directory+file_name+'/' not in old_files:
                url = sub.attachments[0]['url']
                print("Saving to:", directory+file_name+'.zip')
                download_url(url, directory+file_name+'.zip')

    except AttributeError:
        if args.verbose:
            print("Submission has no attachment:", sub.id)


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

# get users
users = course.get_users()

# Walk through all assignments
submissions = []
count = 0
old_files = glob('Week*/submissions/*/')
for assignment in course.get_assignments():
    # Create paths for zip files
    print("Checking " + assignment.name + "...")
    if args.check_all:
        submissions += list(assignment.get_submissions())
    elif args.failed:
        submissions += [sub for sub in assignment.get_submissions()
                        if sub.grade == 'incomplete']
    elif args.uncommented:
        for sub in assignment.get_submissions(include='submission_comments'):
            comment_files = extract_comment_filenames(
                sub.submission_comments)
            submission_fname = create_file_name(sub, course) + '.zip'
            if submission_fname not in comment_files:
                submissions.append(sub)
    else:
        for sub in assignment.get_submissions():
            if vars(sub).get('attachments') is not None and (
                    not sub.grade_matches_current_submission or
                    sub.grade is None):
                submissions.append(sub)

if args.verbose:
    print("Submissions to correct:", len(submissions))

# Download submissions
if submissions:
    num_cores = multiprocessing.cpu_count()
    pbar = Pbar.ProgressBar(redirect_stdout=True)
    if args.parallel:
        print("Downloading submissions in parallel!")
        Parallel(n_jobs=num_cores)(delayed(
            download_submission)(sub, old_files, course, args)
                                   for sub in pbar(submissions))
    else:
        for sub in pbar(submissions):
            download_submission(sub, old_files, course, args)
else:
    print("No submissions to download...")
