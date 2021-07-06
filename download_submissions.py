# Import the Canvas class
import cProfile
import argparse
import multiprocessing
import os
import shutil
import sys
from functools import partial
from glob import glob
from pathlib import Path
from pprint import pprint

import progressbar as Pbar
from canvasapi import Canvas
from p_tqdm import p_map, p_umap
from itertools import chain
from canvas_helpers import create_file_name
from canvas_helpers import download_url
from canvas_helpers import extract_comment_filenames
from canvas_helpers import file_to_string

# Canvas API URL
API_URL = "https://absalon.ku.dk/"

# Canvas API key
API_KEY = file_to_string('token')

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

# init course
course_id = file_to_string('course_id')
course = canvas.get_course(course_id)

parser = argparse.ArgumentParser("""
Program to download assignments. It needs two files next to it
    course_id: Containing the course id
    token:     Your personal accesstoken from canvas
Default behaviour is to only download handins that have been changed""")
parser.add_argument("-v", "--verbose",
                    help="sets verbosity",
                    action='store_true')
parser.add_argument("-p", "--parallel",
                    help="download in parallel",
                    action='store_true')
parser.add_argument("-n", "--num-cores",
                    help="description",
                    metavar="num-cores",
                    type=int,
                    nargs='?',
                    default=multiprocessing.cpu_count())
parser.add_argument("-a", "--assignment",
                    help="Specific assignments to download",
                    metavar="assignement",

                    default=[a.name for a in course.get_assignments()],
                    nargs='*',
                    choices=[a.name for a in course.get_assignments()],
                    type=str)
parser.add_argument("-s", "--student-id",
                    help="Specific student-id to download",
                    metavar="student-id",
                    nargs='*',
                    type=int)
parser.add_argument("-d", "--download",
                    help="Which handins to download",
                    dest='download',
                    type=str,
                    # nargs='?',
                    default="new",
                    choices=["failed", "uncommented", "all", "new"])
parser.add_argument("-l", "--list-assignments",
                    help="list assignments for course and exit",
                    action='store_true')
parser.add_argument("--dry",
                    help="dry run where nothing is downloaded",
                    action='store_true')

args = parser.parse_args()


def download_submission(sub, old_files, course, args):
    try:
        url = sub.attachments[0]['url']
        if url:
            file_name = create_file_name(sub, course)
            directory = course.get_assignment(sub.assignment_id).name.replace(' ', '')
            directory = os.path.join(directory, 'submissions', '')
            Path(directory).mkdir(parents=True, exist_ok=True)

            # check if user has old submissions
            folders_to_remove = [old for old in old_files
                                 if str(sub.user_id) in old and
                                 os.path.join(file_name, '') not in old]
            for f in folders_to_remove:
                shutil.rmtree(f, ignore_errors=True)
            # download attachment if it doesn't exist,
            if os.path.join(directory, 'file_name', '') not in old_files:
                url = sub.attachments[0]['url']
                if args.verbose:
                    print("Saving to:", directory+file_name+'.zip')
                if not args.dry:
                    download_url(url, directory+file_name+'.zip')

    except AttributeError:
        if args.verbose:
            print("Submission has no attachment:", sub.id)


if args.list_assignments:
    print("Possible assignments are:")
    print('\n'.join([' - '+a.name for a in course.get_assignments()]))
    sys.exit()

# get users
users = course.get_users()

# Walk through all assignments
submissions = []
sub_len = 0
count = 0

old_files = glob(os.path.join("*", 'submissions', '*', ''))

for assignment in [a for a in course.get_assignments() if a.name in args.assignment]:
    # Create paths for zip files
    if args.verbose:
        print("Checking " + assignment.name + "...")

    if args.download == "all":
        submissions += list(assignment.get_submissions())
    elif args.download == "failed":
        submissions += [sub for sub in assignment.get_submissions()
                        if sub.grade == 'incomplete']
    elif args.download == "uncommented":
        for sub in assignment.get_submissions(include='submission_comments'):
            comment_files = extract_comment_filenames(
                sub.submission_comments)
            submission_fname = create_file_name(sub, course) + '.zip'
            if submission_fname not in comment_files:
                submissions.append(sub)
    elif args.download == "new":
        for sub in assignment.get_submissions():
            if vars(sub).get('attachments') is not None and (
                    not sub.grade_matches_current_submission or
                    sub.grade is None):
                submissions.append(sub)

    # is specific students where chosen filter them out_file
    if args.student_id:
        submissions = [sub for sub in submissions if sub.user_id in args.student_id]
    if args.verbose:
        print("found:", len(submissions)-sub_len)
        sub_len = len(submissions)

print("Submissions to correct:", len(submissions))

# Download submissions

with cProfile.Profile() as pr:
    if submissions:
        if args.parallel:
            print("Downloading submissions in parallel!")
            p_umap(
                partial(download_submission, old_files=old_files,
                        course=course, args=args),
                submissions,
                num_cpus=args.num_cores)
        else:
            pbar = Pbar.ProgressBar(redirect_stdout=True)
            for sub in pbar(submissions):
                download_submission(sub, old_files, course, args)
    else:
        print("No submissions to download...")
pr.dump_stats("download_umap.pstats")
